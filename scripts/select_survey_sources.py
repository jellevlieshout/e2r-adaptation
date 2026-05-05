"""Sample 30 source sentences from the v2 candidate pool for the human-eval survey.

Reads the 50-row pool produced by `select_survey_candidates.py` (Step 19b /
21e-survey) and writes a 30-row deterministic sample. The selected sources are
the *anchors* of the survey: each gets rated under three system conditions
(Llama-3.1-8B agentic, Llama-3.1-8B monolithic, Llama-3.3-70B-AWQ agentic),
yielding 30 * 3 = 90 survey items. See `1 - Thesis/Survey/PLAN.md` §4.

The sampling is balanced across sentence length terciles so the survey doesn't
over-represent short or long sentences. `random.seed(...)` makes the selection
reproducible and recoverable from the source pool alone.

Usage:
    uv run python scripts/select_survey_sources.py \
        --pool "/path/to/Vault/1 - Thesis/Survey/survey_candidates_v2.csv" \
        --out  "/path/to/Vault/1 - Thesis/Survey/selected_sources.csv" \
        --n 30 \
        --seed 19260817
"""

import argparse
import csv
import random
from pathlib import Path


def stratified_sample(rows: list[dict], n: int, seed: int) -> list[dict]:
    """Sample n rows stratified by sentence-length terciles.

    Splits the pool into three length-ordered terciles and samples roughly n/3
    from each, then shuffles the result. Guarantees the survey covers the full
    length distribution rather than over-sampling either end.
    """
    if len(rows) < n:
        raise ValueError(f"Pool has only {len(rows)} rows; need ≥ {n}")

    sorted_rows = sorted(rows, key=lambda r: len(r["original_text"]))
    tercile_size = len(sorted_rows) // 3
    terciles = [
        sorted_rows[:tercile_size],
        sorted_rows[tercile_size : 2 * tercile_size],
        sorted_rows[2 * tercile_size :],
    ]

    rng = random.Random(seed)
    per_tercile = [n // 3] * 3
    for i in range(n - sum(per_tercile)):
        per_tercile[i] += 1

    selected: list[dict] = []
    for tercile, k in zip(terciles, per_tercile):
        selected.extend(rng.sample(tercile, k))

    rng.shuffle(selected)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--seed", type=int, default=19260817)
    args = parser.parse_args()

    with args.pool.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    selected = stratified_sample(rows, args.n, args.seed)

    fieldnames = [
        "source_id",
        "example_id",
        "original_text",
        "gold_detected_expression",
        "agentic_8b_replacement",
    ]
    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(selected):
            writer.writerow(
                {
                    "source_id": f"src_{i:02d}",
                    "example_id": row["example_id"],
                    "original_text": row["original_text"],
                    "gold_detected_expression": row["detected_expression"],
                    "agentic_8b_replacement": row["system_replacement"],
                }
            )

    lengths = [len(r["original_text"]) for r in selected]
    print(f"Selected {len(selected)} sources -> {args.out}")
    print(
        f"Sentence length: min={min(lengths)} median={sorted(lengths)[len(lengths) // 2]} max={max(lengths)}"
    )


if __name__ == "__main__":
    main()
