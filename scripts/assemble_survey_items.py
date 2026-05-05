"""Assemble the 90-row survey items table from three Couchbase runs.

For each of the 30 source sentences listed in `selected_sources.csv`, this
script combines outputs from three system conditions into a single CSV
suitable for loading into the Direct Assessment survey form. See
`1 - Thesis/Survey/PLAN.md` §4 for the multi-system design and §6 for the
form-side wiring.

Three system conditions:
  - 8b_agentic     : Llama-3.1-8B-Instruct + agentic v2 detect-then-replace
  - 8b_monolithic  : Llama-3.1-8B-Instruct + monolithic single-prompt rewrite
  - 70b_agentic    : Llama-3.3-70B-Instruct-AWQ + agentic v2 detect-then-replace

The `displayed_detected_expression` column shows the **SemEval gold idiom** for
all three conditions on the same source, so annotators see the same anchor
regardless of which system produced the replacement (see 22f decision in
`TODOS.md`). The agentic systems' actual `figurative_expressions` field is
kept in `system_detected_expression` for analysis-side detection metrics, but
is *not* surfaced to annotators.

Usage:
    uv run python scripts/assemble_survey_items.py \\
        --sources "/path/to/Vault/1 - Thesis/Survey/selected_sources.csv" \\
        --agentic-8b   <run_id> \\
        --monolithic-8b <run_id> \\
        --agentic-70b  <run_id> \\
        --api http://localhost:3030 \\
        --out "/path/to/Vault/1 - Thesis/Survey/survey_items.csv"

Output schema: item_id, source_id, system_id, example_id, original_text,
displayed_detected_expression, system_replacement, system_detected_expression.
"""

import argparse
import csv
import json
import sys
import urllib.request
from pathlib import Path


def fetch_predictions(api: str, run_id: str) -> dict[str, dict]:
    """Return {example_id: prediction_record} for a run."""
    with urllib.request.urlopen(f"{api}/runs/{run_id}/predictions", timeout=60) as resp:
        rows = json.loads(resp.read())
    out: dict[str, dict] = {}
    for r in rows:
        eid = r.get("example_id")
        if eid:
            out[eid] = r
    return out


def extract_replacement(pred: dict | None) -> str:
    if not pred:
        return ""
    return (pred.get("predicted_replacement") or "").strip()


def extract_detected_expressions(pred: dict | None) -> str:
    if not pred:
        return ""
    det = pred.get("predicted_detection")
    if not det:
        return ""
    exprs = det.get("figurative_expressions") or []
    return "; ".join(exprs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--agentic-8b", required=True, help="run_id for 8B agentic detect-then-replace v2")
    parser.add_argument("--monolithic-8b", required=True, help="run_id for 8B monolithic_replace")
    parser.add_argument("--agentic-70b", required=True, help="run_id for 70B agentic detect-then-replace v2")
    parser.add_argument("--api", default="http://localhost:3030")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    with args.sources.open() as f:
        sources = list(csv.DictReader(f))
    print(f"Loaded {len(sources)} sources from {args.sources}", file=sys.stderr)

    print("Fetching predictions:", file=sys.stderr)
    print(f"  agentic_8b    run={args.agentic_8b}", file=sys.stderr)
    preds_8b_agentic = fetch_predictions(args.api, args.agentic_8b)
    print(f"  monolithic_8b run={args.monolithic_8b}", file=sys.stderr)
    preds_8b_mono = fetch_predictions(args.api, args.monolithic_8b)
    print(f"  agentic_70b   run={args.agentic_70b}", file=sys.stderr)
    preds_70b_agentic = fetch_predictions(args.api, args.agentic_70b)

    conditions = [
        ("8b_agentic", preds_8b_agentic),
        ("8b_monolithic", preds_8b_mono),
        ("70b_agentic", preds_70b_agentic),
    ]

    fieldnames = [
        "item_id",
        "source_id",
        "system_id",
        "example_id",
        "original_text",
        "displayed_detected_expression",
        "system_replacement",
        "system_detected_expression",
    ]

    rows_written = 0
    missing: list[str] = []
    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        item_counter = 0
        for source in sources:
            example_id = source["example_id"]
            for system_id, preds in conditions:
                pred = preds.get(example_id)
                if pred is None:
                    missing.append(f"{system_id}:{example_id}")
                writer.writerow(
                    {
                        "item_id": f"item_{item_counter:03d}",
                        "source_id": source["source_id"],
                        "system_id": system_id,
                        "example_id": example_id,
                        "original_text": source["original_text"],
                        "displayed_detected_expression": source["gold_detected_expression"],
                        "system_replacement": extract_replacement(pred),
                        "system_detected_expression": extract_detected_expressions(pred),
                    }
                )
                item_counter += 1
                rows_written += 1

    print(f"\nWrote {rows_written} rows to {args.out}", file=sys.stderr)
    if missing:
        print(f"WARN: {len(missing)} predictions missing:", file=sys.stderr)
        for m in missing[:10]:
            print(f"  - {m}", file=sys.stderr)
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more", file=sys.stderr)
        return 1
    print("All 90 items present.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
