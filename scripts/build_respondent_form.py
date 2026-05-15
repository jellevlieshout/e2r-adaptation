"""Deterministic per-respondent survey-form builder.

For seed N, samples 16 real (source, system) pairs + 2 bad-references + 2
repeat-pair items from the assembled survey pool and writes
`respondent_NN.csv` + `respondent_NN_form.md` into the Obsidian vault's
`1 - Thesis/Survey/respondent_assignments/` directory.

The output is intended to be hand-built into Microsoft Forms one section
at a time. The markdown is the source-of-truth blueprint; the MS Form is
the live instrument. See `1 - Thesis/Survey/PLAN.md` §§3, 5, 6 for the
design constraints encoded here.

Inputs (Obsidian vault paths, hard-coded relative to ``--vault``):
  - ``selected_sources.csv``      — 27 source sentences (post-2026-05-15
    drop of src_18 for SemEval gold contamination).
  - ``survey_items.csv``          — 81 rows = 27 sources × 3 system
    conditions; assembled by ``assemble_survey_items.py`` and filtered.
  - ``bad_references_final.csv``  — 27 rows; LLM-degraded variants
    targeting meaning preservation, manually reviewed.

Outputs (under ``respondent_assignments/``):
  - ``respondent_NN.csv``         — 20-row item ledger with form_position,
    source_id, system_id, is_bad_ref, is_repeat_second_showing, and the
    user-visible text fields.
  - ``respondent_NN_form.md``     — blueprint for hand-building the MS
    Form: consent + eligibility (3-way, with branching) + ethics
    paragraph + calibration + 20 rated sections. Rating fields are flagged
    Required=OFF per Mari Carmen 2026-05-15.

Per-respondent sampling rules (PLAN §3, §4, §5):
  - 16 real items, distinct sources, balanced across the 3 system
    conditions (cycled 6/5/5 with the per-seed roles rotating).
  - 2 bad-reference items, sources disjoint from the 16 real items.
  - 2 of the 16 real items repeated as a second showing, with ≥5
    positions between first and second showing.
  - 20 ordered positions, bad-refs spread (one in positions 1-10, one
    in positions 11-20).

Usage::

    uv run python scripts/build_respondent_form.py --seed 1
    uv run python scripts/build_respondent_form.py --seeds 1-25

By default ``--vault`` points to ``$HOME/Documents/Obsidian Vault``.
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

DEFAULT_VAULT = Path(os.environ.get("OBSIDIAN_VAULT", str(Path.home() / "Documents/Obsidian Vault")))
SURVEY_DIR_REL = Path("1 - Thesis/Survey")

SYSTEM_IDS = ["8b_agentic", "8b_monolithic", "70b_agentic"]
# Per-respondent quota: 16 = 6+5+5. The "6-slot" rotates across respondents so
# each system averages 16/3 × 16 ≈ 85 ratings across 16 respondents (vs 96/80/80
# if the 6-slot were fixed on 8b_agentic — which by pigeonhole leaves some
# (source, 5-slot-system) pairs at 2 ratings after 16 respondents). With
# rotation each system gets ≥85/27 = 3.15 ratings/source on average → greedy
# distributes to ≥3 per pair at N=16.
QUOTA_AMOUNTS = (6, 5, 5)
N_REAL = 16
N_BAD_REF = 2
N_REPEAT = 2
N_TOTAL = N_REAL + N_BAD_REF + N_REPEAT  # 20
MIN_REPEAT_GAP = 5


@dataclass
class SurveyPool:
    items_by_source_system: dict[tuple[str, str], dict]
    sources: list[dict]            # ordered list, one row per source
    bad_refs: dict[str, dict]      # source_id -> bad-ref row


def load_pool(survey_dir: Path) -> SurveyPool:
    sources_path = survey_dir / "selected_sources.csv"
    items_path = survey_dir / "survey_items.csv"
    bad_refs_path = survey_dir / "bad_references_final.csv"

    with sources_path.open() as f:
        sources = list(csv.DictReader(f))
    with items_path.open() as f:
        items = list(csv.DictReader(f))
    with bad_refs_path.open() as f:
        bad_refs = list(csv.DictReader(f))

    items_by_key = {(r["source_id"], r["system_id"]): r for r in items}
    bad_refs_by_source = {r["source_id"]: r for r in bad_refs}

    source_ids = {s["source_id"] for s in sources}
    missing_items = [s for s in source_ids for sys in SYSTEM_IDS if (s, sys) not in items_by_key]
    if missing_items:
        raise SystemExit(f"survey_items.csv missing rows for: {missing_items[:5]}")
    missing_brefs = sorted(source_ids - set(bad_refs_by_source))
    if missing_brefs:
        raise SystemExit(f"bad_references_final.csv missing rows for: {missing_brefs[:5]}")

    return SurveyPool(items_by_key, sources, bad_refs_by_source)


def build_batch_assignments(pool: SurveyPool, max_seed: int) -> dict[int, list[tuple[str, str]]]:
    """Greedy batch assignment of 16 (source, system) real-item pairs per respondent.

    Walks seeds ``1..max_seed`` in order, maintaining a running coverage counter
    across the global pool of (source, system) pairs. For each respondent the
    sampler builds a 16-pair selection under three constraints:

      1. **No source repeat per respondent.** A respondent never rates the same
         source twice as a real item (PLAN §3, §4). The repeat-pair mechanism
         (§5b) handles deliberate intra-respondent repeats separately.
      2. **System balance per respondent.** 16 real items split 6 / 5 / 5
         across ``8b_agentic`` / ``8b_monolithic`` / ``70b_agentic``, with the
         dominant-system rotation cycling per seed so condition prevalence
         varies across respondents.
      3. **Global coverage minimised.** At each slot the sampler picks the
         (source, system) candidate whose current coverage is lowest, breaking
         ties pseudo-randomly via ``random.Random(seed)``. This yields
         deterministic ratings counts: by N=16 respondents (256 ratings,
         243 needed at ≥3/pair) every pair is rated ≥3 times.

    Prefix-stable: the first k respondents in a batch of N>k are identical
    to a batch of N=k, because greedy never looks ahead. ``--seed 5`` and
    ``--seeds 1-5`` therefore produce byte-identical ``respondent_05.csv``.
    """
    sources = [s["source_id"] for s in pool.sources]
    if len(sources) < N_REAL + N_BAD_REF:
        raise SystemExit(
            f"Need at least {N_REAL + N_BAD_REF} sources, pool has {len(sources)}."
        )

    coverage: dict[tuple[str, str], int] = {
        (s, sys): 0 for s in sources for sys in SYSTEM_IDS
    }
    out: dict[int, list[tuple[str, str]]] = {}

    for seed in range(1, max_seed + 1):
        # Per-respondent RNG for tie-breaking — disambiguates equal-coverage
        # candidates without polluting the layout/repeat RNG used downstream.
        tie_rng = random.Random(seed * 7919 + 17)

        # Quota with per-seed rotation: the "6-slot" cycles across systems.
        rotation = (seed - 1) % len(SYSTEM_IDS)
        rotated = SYSTEM_IDS[rotation:] + SYSTEM_IDS[:rotation]
        target_quota = {sys: amt for sys, amt in zip(rotated, QUOTA_AMOUNTS)}
        quota = dict(target_quota)  # depleted as we pick

        used_sources: set[str] = set()
        chosen: list[tuple[str, str]] = []

        for _ in range(N_REAL):
            # Candidate pairs: (cov, tiebreak, source, system)
            candidates: list[tuple[tuple[int, float], str, str]] = []
            for s in sources:
                if s in used_sources:
                    continue
                for sys in SYSTEM_IDS:
                    if quota[sys] <= 0:
                        continue
                    candidates.append(((coverage[(s, sys)], tie_rng.random()), s, sys))
            if not candidates:
                raise SystemExit(
                    f"Could not fill 16 slots for seed {seed}: "
                    f"used_sources={len(used_sources)} quota={quota}"
                )
            candidates.sort(key=lambda x: x[0])
            _, src, sys = candidates[0]
            chosen.append((src, sys))
            used_sources.add(src)
            quota[sys] -= 1
            coverage[(src, sys)] += 1

        # Sanity: counts must equal the (rotated) target quota for this seed.
        sys_counts = Counter(p[1] for p in chosen)
        if dict(sys_counts) != target_quota:
            raise SystemExit(
                f"System balance broken at seed {seed}: got {dict(sys_counts)}, expect {target_quota}"
            )
        out[seed] = chosen

    return out


def build_assignment(pool: SurveyPool, seed: int, real_pairs: list[tuple[str, str]]) -> list[dict]:
    """Sample 20 ordered items for a respondent with the given seed.

    The 16 real (source, system) pairs are supplied by ``build_batch_assignments``
    (greedy + globally coverage-optimal). This function handles per-respondent
    randomisation: which 11 unused sources to pick bad-refs from, which 2 of
    the 16 real items become the repeated pair, and the slot layout that
    enforces gap-≥5 between repeat first/second showings.
    """
    rng = random.Random(seed)

    real_sources = [p[0] for p in real_pairs]
    used = set(real_sources)
    remaining = [s["source_id"] for s in pool.sources if s["source_id"] not in used]
    bad_ref_sources = rng.sample(remaining, N_BAD_REF)

    # Pick a valid 20-slot layout — see ``pick_slot_layout``.
    layout = pick_slot_layout(rng, seed)

    # Of the 16 real items, the two whose slots become ``first_of_repeat``
    # need their second showing reproduced at the matching ``second_of_repeat``
    # slot. Real items are placed at the 16 slots tagged ``plain_real`` or
    # ``first_of_repeat`` (16 total = 14 + 2); the ``second_of_repeat`` slots
    # echo the ``first_of_repeat`` item.
    real_slot_indices = [i for i, tag in enumerate(layout) if tag[0] in ("plain_real", "first_of_repeat")]
    assert len(real_slot_indices) == N_REAL
    rng.shuffle(real_slot_indices)  # already randomized via prior shuffles, but be explicit
    # Map real item idx (0..15) -> slot
    real_idx_to_slot = dict(zip(range(N_REAL), real_slot_indices))
    slot_to_real_idx = {v: k for k, v in real_idx_to_slot.items()}

    # Materialise rows in slot order.
    rows: list[dict] = []
    for slot in range(N_TOTAL):
        tag = layout[slot]
        kind = tag[0]
        if kind == "plain_real":
            idx = slot_to_real_idx[slot]
            source_id, system_id = real_pairs[idx]
            item = pool.items_by_source_system[(source_id, system_id)]
            rows.append({
                "form_position": slot + 1,
                "source_id": source_id,
                "system_id": system_id,
                "is_bad_ref": "False",
                "is_repeat_second_showing": "False",
                "original_text": item["original_text"],
                "displayed_detected_expression": item["displayed_detected_expression"],
                "system_replacement": item["system_replacement"],
            })
        elif kind == "first_of_repeat":
            idx = slot_to_real_idx[slot]
            source_id, system_id = real_pairs[idx]
            item = pool.items_by_source_system[(source_id, system_id)]
            rows.append({
                "form_position": slot + 1,
                "source_id": source_id,
                "system_id": system_id,
                "is_bad_ref": "False",
                "is_repeat_second_showing": "False",
                "original_text": item["original_text"],
                "displayed_detected_expression": item["displayed_detected_expression"],
                "system_replacement": item["system_replacement"],
            })
        elif kind == "second_of_repeat":
            pair_id = tag[1]
            # Find the matching first_of_repeat slot, then the item index there.
            first_slot = next(s for s, t in enumerate(layout) if t[0] == "first_of_repeat" and t[1] == pair_id)
            idx = slot_to_real_idx[first_slot]
            source_id, system_id = real_pairs[idx]
            item = pool.items_by_source_system[(source_id, system_id)]
            rows.append({
                "form_position": slot + 1,
                "source_id": source_id,
                "system_id": system_id,
                "is_bad_ref": "False",
                "is_repeat_second_showing": "True",
                "original_text": item["original_text"],
                "displayed_detected_expression": item["displayed_detected_expression"],
                "system_replacement": item["system_replacement"],
            })
        elif kind == "bad_ref":
            bf_id = tag[1]
            source_id = bad_ref_sources[bf_id]
            bref = pool.bad_refs[source_id]
            rows.append({
                "form_position": slot + 1,
                "source_id": source_id,
                "system_id": "QC_BAD_REF",
                "is_bad_ref": "True",
                "is_repeat_second_showing": "False",
                "original_text": bref["original_text"],
                "displayed_detected_expression": bref["gold_detected_expression"],
                "system_replacement": bref["bad_reference"],
            })
        else:
            raise SystemExit(f"Unknown layout kind at slot {slot}: {tag}")

    return rows


def pick_slot_layout(rng: random.Random, seed: int) -> list[tuple]:
    """Pick a 20-entry layout assigning each position a role.

    Returns a list of 20 tuples, one per position:
      - ``('plain_real',)``               — 14 of these
      - ``('first_of_repeat', pair_id)``  — 2 of these (pair_id in 0..1)
      - ``('second_of_repeat', pair_id)`` — 2 of these
      - ``('bad_ref', bf_id)``            — 2 of these (bf_id in 0..1)

    Invariants:
      - Exactly 14 plain + 2 first + 2 second + 2 bad_ref = 20.
      - For each pair_id, slot[second_of_repeat] - slot[first_of_repeat] ≥ MIN_REPEAT_GAP.
      - One bad_ref slot is in [0, N_TOTAL//2); the other is in [N_TOTAL//2, N_TOTAL).

    Uses retry with the supplied RNG; raises if no valid layout found after 200 attempts.
    """
    for attempt in range(200):
        layout: list[tuple | None] = [None] * N_TOTAL
        used: set[int] = set()

        # Bad-refs: one per half.
        bf_1 = rng.choice(range(0, N_TOTAL // 2))
        bf_2 = rng.choice(range(N_TOTAL // 2, N_TOTAL))
        if bf_1 == bf_2:
            continue
        layout[bf_1] = ("bad_ref", 0)
        layout[bf_2] = ("bad_ref", 1)
        used = {bf_1, bf_2}

        # Repeat pairs: pick (first, second) with second - first ≥ MIN_REPEAT_GAP.
        success = True
        for pair_id in range(N_REPEAT):
            first_cands = [
                s for s in range(N_TOTAL) if s not in used
                and any(t not in used and t >= s + MIN_REPEAT_GAP for t in range(N_TOTAL))
            ]
            if not first_cands:
                success = False
                break
            first = rng.choice(first_cands)
            second_cands = [
                t for t in range(N_TOTAL)
                if t not in used and t != first and t >= first + MIN_REPEAT_GAP
            ]
            if not second_cands:
                success = False
                break
            second = rng.choice(second_cands)
            layout[first] = ("first_of_repeat", pair_id)
            layout[second] = ("second_of_repeat", pair_id)
            used.add(first)
            used.add(second)

        if not success:
            continue

        # Fill remaining slots with plain real items.
        for s in range(N_TOTAL):
            if layout[s] is None:
                layout[s] = ("plain_real",)
        return [t for t in layout if t is not None]  # type: ignore[misc]

    raise SystemExit(f"Could not find a valid 20-slot layout for seed {seed} after 200 attempts.")


def write_csv(rows: list[dict], out_path: Path) -> None:
    fieldnames = [
        "form_position", "source_id", "system_id", "is_bad_ref",
        "is_repeat_second_showing", "original_text",
        "displayed_detected_expression", "system_replacement",
    ]
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


FORM_HEADER = """# Microsoft Form — Respondent #{seed} (seed={seed})

Build this in Microsoft Forms one section at a time. Each "Item" below is one **Section** (page break) containing **3 Number questions** + **1 optional Text question**. Total: intro + calibration + 20 rated items = 22 sections, 80 questions.

Numeric question setup in MS Forms: type = **Number**; under "More settings for question" set **Min = 0**, **Max = 100**, **Required = OFF** (Mari Carmen 2026-05-15: rating items are optional so partial submissions are accepted).

---

## Section 0 — Welcome, ethics & eligibility

**Title**: Idiom easy2read adaptation evaluation

**Description (paste verbatim):**

Thank you for taking part in this survey. You will be shown 20 short English sentences that contain an idiomatic expression, alongside a system-generated literal paraphrase. For each sentence you will be asked to rate the paraphrase on three dimensions using a 0–100 numeric scale. The full survey takes approximately 20–25 minutes.

Your responses will be used in anonymous form for an academic thesis on language-model-based **easy2read adaptation** (https://www.inclusion-europe.eu/easy-to-read/) of figurative English. No personally identifying information is collected. You may stop at any time, and **individual ratings are optional** — if you get tired, feel free to skip remaining items and submit what you have.

**Information on data protection (paste verbatim, after the description above):**

> This questionnaire has been designed to ensure complete anonymity. However, we consider it appropriate to inform you about our privacy policy, in accordance with the provisions of the personal data protection regulations. If you agree to complete the questionnaire, we inform you that you consent to your data being processed by the Universidad Politécnica de Madrid (Ontology Engineering Group), which is responsible for this processing, for the purposes related to the aforementioned research. We also inform you that you may access, rectify and delete your data, as well as exercise other rights, under the terms indicated in the additional information available at the following link: https://oeg.fi.upm.es/protecciondatos.html (text is written in Spanish).

**Question E.1** (type: Choice, **required**, with branching)
> Which of the following describes you?
> ( ) I am a native English speaker.
> ( ) I am not a native English speaker, but I have lived in an English-speaking country (e.g. UK, USA, Ireland, Canada, Australia, New Zealand) for **10 years or more**.
> ( ) Neither of the above. *(Branch to end-of-form thank-you screen.)*

Branching: the third option ends the form immediately. The first two proceed.

**Question E.2** (type: Choice, **required**)
> I have read the description above and consent to my anonymous responses being used as described.
> ( ) I consent.
> ( ) I do not consent. *(Branch to end-of-form thank-you screen.)*

---

## Section 1 — How to rate (calibration, NOT scored)

**Description (paste verbatim):**

On each of the next 20 pages you will see:

1. an **Original sentence** containing an English idiomatic expression;
2. the **Idiom detected** by the system;
3. the **System's replacement** of the original sentence (the idiom should have been replaced with literal English);

and then three numeric fields to rate the system's replacement on:

- **Grammaticality** — is the system's output well-formed English? (0 = ungrammatical, 100 = perfect)
- **Meaning preservation** — does the system's replacement convey the same meaning as the original sentence? (0 = different meaning, 100 = exactly the same meaning)
- **Simplicity** — is the system's replacement easier to read than the original? (0 = harder, 100 = much easier)

Use the full 0–100 range freely. There is no "correct" middle value. All rating fields are **optional**; if you get tired, leave the rest blank and submit. There is also an optional free-text field where you can write your own preferred literal paraphrase if the system's output is poor.

**Worked example (not scored):**

> Original: *Unni, the stylist, is on cloud nine after having an opportunity to style the beard of his favourite star.*
> Detected idiom: *on cloud nine*
> System replacement: *Unni, the stylist, is extremely happy after having an opportunity to style the beard of his favourite star.*

Reasonable ratings for this output: grammaticality ~ 95 (well-formed), meaning preservation ~ 90 ("on cloud nine" → "extremely happy" is a faithful replacement), simplicity ~ 80 (the literal version is more accessible, but only one phrase changed).

It is possible that you will find poor replacements or repeated items. This is expected.

---
"""


def md_escape(text: str) -> str:
    return text.replace("\n", " ").strip()


def render_form(rows: list[dict], seed: int) -> str:
    parts = [FORM_HEADER.format(seed=seed)]
    for i, row in enumerate(rows, start=1):
        original = md_escape(row["original_text"])
        detected = md_escape(row["displayed_detected_expression"])
        replacement = md_escape(row["system_replacement"])
        parts.append(
            f"""## Section {i + 1} — Item {i}/20

**Section description (paste verbatim):**

> **Original sentence:** {original}
>
> **Idiom detected by the system:** *{detected}*
>
> **System's replacement:** {replacement}

**Q{i}.1** (Number, optional, min=0 max=100)
> Rate the **grammaticality** of the system's replacement (0 = ungrammatical, 100 = perfect English).

**Q{i}.2** (Number, optional, min=0 max=100)
> Rate the **meaning preservation** of the system's replacement against the original (0 = different meaning, 100 = exactly the same meaning).

**Q{i}.3** (Number, optional, min=0 max=100)
> Rate the **simplicity** of the system's replacement compared to the original (0 = harder to read, 100 = much easier to read).

**Q{i}.4** (Text, optional, long answer)
> If the system's replacement misses the mark, what would you write instead? (Optional — leave blank if the replacement is fine.)

---
"""
        )
    return "\n".join(parts)


def write_form(text: str, out_path: Path) -> None:
    out_path.write_text(text)


def parse_seed_arg(seeds: str | None, single: int | None) -> list[int]:
    if single is not None:
        return [single]
    if seeds is None:
        return [1]
    if "-" in seeds:
        a, b = seeds.split("-", 1)
        return list(range(int(a), int(b) + 1))
    return [int(s) for s in seeds.split(",")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--seed", type=int, help="Single seed (==respondent number).")
    parser.add_argument("--seeds", type=str, help="Range 'A-B' or comma-list 'A,B,C'.")
    args = parser.parse_args()

    survey_dir = args.vault / SURVEY_DIR_REL
    out_dir = survey_dir / "respondent_assignments"
    out_dir.mkdir(parents=True, exist_ok=True)

    pool = load_pool(survey_dir)
    seeds = parse_seed_arg(args.seeds, args.seed)
    max_seed = max(seeds)
    # Greedy batch produces all seeds 1..max_seed; prefix-stable so seeds
    # < max_seed have the same selection regardless of whether max_seed was 16
    # or 35. Print the batch coverage report at the end.
    batch = build_batch_assignments(pool, max_seed)

    # Track cross-respondent coverage for the reporter at the end (covers
    # only the seeds the user actually requested writing for — useful when
    # checking "what does N=16 look like").
    coverage: dict[tuple[str, str], int] = defaultdict(int)

    for seed in seeds:
        rows = build_assignment(pool, seed, real_pairs=batch[seed])
        for r in rows:
            if r["is_bad_ref"] == "True" or r["is_repeat_second_showing"] == "True":
                continue
            coverage[(r["source_id"], r["system_id"])] += 1

        csv_path = out_dir / f"respondent_{seed:02d}.csv"
        md_path = out_dir / f"respondent_{seed:02d}_form.md"
        write_csv(rows, csv_path)
        write_form(render_form(rows, seed), md_path)
        print(f"seed={seed}: wrote {csv_path.name} + {md_path.name}", file=sys.stderr)

    # Coverage report
    n_pairs = len(pool.sources) * len(SYSTEM_IDS)
    rated = sum(1 for k in coverage if coverage[k] >= 1)
    print(f"\nCoverage across seeds {seeds}:", file=sys.stderr)
    print(f"  total (source, system) pairs: {n_pairs}", file=sys.stderr)
    print(f"  pairs receiving ≥1 rating:    {rated}", file=sys.stderr)
    if coverage:
        counts = sorted(coverage.values())
        median = counts[len(counts) // 2]
        print(f"  ratings per pair — min={counts[0]}, median={median}, max={counts[-1]}", file=sys.stderr)
    uncovered = [
        (s["source_id"], sys)
        for s in pool.sources
        for sys in SYSTEM_IDS
        if (s["source_id"], sys) not in coverage
    ]
    if uncovered:
        print(f"  uncovered pairs ({len(uncovered)}):", file=sys.stderr)
        for s, sy in uncovered[:8]:
            print(f"    - {s} / {sy}", file=sys.stderr)
        if len(uncovered) > 8:
            print(f"    … and {len(uncovered) - 8} more", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
