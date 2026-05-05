"""Generate bad-reference items for the Direct Assessment survey QC.

One bad-reference is generated per source sentence in `selected_sources.csv`.
Each bad-reference targets the **meaning preservation** rubric dimension —
the most binary and easiest to break cleanly (per Survey/PLAN.md §5a). The
strategy: take an existing literal paraphrase and modify it so it expresses
a *different* meaning, while keeping grammaticality intact.

A respondent who rates the bad-reference >= the system's actual replacement
on meaning preservation has likely not engaged with the rating task; the
filter rule (Survey/PLAN.md §5a) excludes annotators who fail both bad-refs
in their set. **Manual review is required** before sending the survey out:
the LLM occasionally produces (a) meaning-preserving outputs that miss the
"break it" instruction, or (b) ungrammatical outputs that confound the QC
(testing meaning, not grammaticality).

LLM provider: defaults to OpenRouter (`google/gemini-3-flash-preview`,
T=0.7 — slight randomness so generations don't collapse to a single
template). The bad-references are *survey instrumentation*, not thesis
results; using a hosted model here is appropriate. If you want to keep the
"open-weights only" boundary tight, set `--model vllm:...` and the API will
route to the cluster instead.

Usage:
    uv run python scripts/generate_bad_references.py \\
        --sources "/path/to/Vault/1 - Thesis/Survey/selected_sources.csv" \\
        --out "/path/to/Vault/1 - Thesis/Survey/bad_references_draft.csv" \\
        --model google/gemini-3-flash-preview

Output schema: source_id, example_id, original_text, gold_detected_expression,
agentic_8b_replacement (input), bad_reference (LLM output), notes (review).
"""

import argparse
import csv
import os
import sys
import time
import urllib.request
import urllib.error
import json
from pathlib import Path

PROMPT = """You are constructing a quality-control item for a translation-rating survey. The annotator will rate sentences on three axes — grammaticality, meaning preservation, and simplicity — using a 0–100 scale. Your task is to produce a *deliberately broken* version of the proposed simplification, targeting the **meaning preservation** dimension only.

You will be given:
- ORIGINAL: a sentence containing an idiomatic expression.
- IDIOM: the idiomatic expression in the original.
- PROPOSED: a literal paraphrase a system produced.

Produce a single rewritten sentence that:
- Is grammatical, fluent English (do not break grammaticality);
- Has a meaning that is plausibly related to the original (e.g. same topic, same subject) but **clearly different** from the original;
- Does not paraphrase the original idiom correctly — if anything, contradict it or substitute an unrelated meaning;
- Stays roughly the same length as the proposed paraphrase.

Output only the rewritten sentence. No explanation, no labels, no quotes.

ORIGINAL: {original}
IDIOM: {idiom}
PROPOSED: {proposed}"""


def call_openrouter(api_key: str, model: str, prompt: str) -> str:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 200,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"].strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="google/gemini-3-flash-preview")
    parser.add_argument("--limit", type=int, help="(Optional) cap rows for dry-run")
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY env var not set", file=sys.stderr)
        return 2

    with args.sources.open() as f:
        sources = list(csv.DictReader(f))
    if args.limit:
        sources = sources[: args.limit]
    print(f"Generating bad-references for {len(sources)} sources via {args.model}", file=sys.stderr)

    fieldnames = [
        "source_id",
        "example_id",
        "original_text",
        "gold_detected_expression",
        "agentic_8b_replacement",
        "bad_reference",
        "notes",
    ]
    rows_written = 0
    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, src in enumerate(sources, start=1):
            prompt = PROMPT.format(
                original=src["original_text"],
                idiom=src["gold_detected_expression"],
                proposed=src["agentic_8b_replacement"],
            )
            try:
                bad_ref = call_openrouter(api_key, args.model, prompt)
            except urllib.error.HTTPError as e:
                bad_ref = f"<<ERROR: {e.code} {e.reason}>>"
            except Exception as e:
                bad_ref = f"<<ERROR: {e}>>"

            writer.writerow(
                {
                    "source_id": src["source_id"],
                    "example_id": src["example_id"],
                    "original_text": src["original_text"],
                    "gold_detected_expression": src["gold_detected_expression"],
                    "agentic_8b_replacement": src["agentic_8b_replacement"],
                    "bad_reference": bad_ref,
                    "notes": "",
                }
            )
            rows_written += 1
            if i % 5 == 0:
                print(f"  generated {i}/{len(sources)}", file=sys.stderr)
            time.sleep(0.5)

    print(f"\nWrote {rows_written} bad-references to {args.out}", file=sys.stderr)
    print("\nNEXT STEP: review every row in the CSV. The 'notes' column is for review marks:", file=sys.stderr)
    print("  - 'OK' if the bad-reference is grammatical, plausibly related, and clearly different in meaning", file=sys.stderr)
    print("  - 'REGEN' if it failed (preserved meaning, broke grammar, or is too similar to original)", file=sys.stderr)
    print("  - 'EDIT: <rewrite>' to manually fix borderline cases", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
