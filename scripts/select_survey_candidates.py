"""
Select N survey candidates from a `/runs/{run_id}/export` CSV.

Step 19b of the thesis TODOS (RQ3 human-evaluation pipeline). Designed for
SemEval idiom `detect_then_replace` runs but works on any export with the
standard column set.

Filter criteria (per `1 - Thesis/Survey/PLAN.md` and [[evaluation-strategy]]):
  - text < N words (manageable cognitive load for annotators; default 30,
    relaxed from 20 because SemEval sentences run long, median ~25 words).
  - figurative_expression non-empty (system actually detected something).
  - predicted_replacement non-empty (system actually produced output).
  - detected expression <= M words (default 4 — proxy for unambiguity).
  - prefer rows where SemEval has a Task B paraphrase (curation signal,
    NOT shown to annotators — see PLAN.md for why).

Output columns match the Direct Assessment annotation template
(continuous 0-100 rating per Graham 2013):
  example_id | original_text | detected_expression | system_replacement
  | human_rating_0_10000 | human_alternative_paraphrase

Usage:
  curl -s http://localhost:3030/runs/<run_id>/export > export.csv
  python scripts/select_survey_candidates.py \\
    --input export.csv \\
    --output "1 - Thesis/Survey/survey_candidates_v1.csv" \\
    --n 50 --max-words 30 --max-expression-words 4 --seed 42
"""

import argparse
import csv
import random
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True, help="raw export CSV from /runs/{id}/export")
    p.add_argument("--output", required=True, help="annotation template CSV to write")
    p.add_argument("--n", type=int, default=50, help="how many candidates to select")
    p.add_argument("--max-words", type=int, default=20)
    p.add_argument("--max-expression-words", type=int, default=4)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    random.seed(args.seed)

    rows = list(csv.DictReader(Path(args.input).open(newline="", encoding="utf-8")))
    print(f"raw rows: {len(rows)}")

    pool = []
    for r in rows:
        text = (r.get("text") or "").strip()
        figurative = (r.get("figurative_expression") or "").strip()
        replacement = (r.get("predicted_replacement") or "").strip()
        if not text or not figurative or not replacement:
            continue
        n_words = len(text.split())
        if n_words >= args.max_words:
            continue
        # If multiple expressions joined by "; ", take the first one for unambiguity score.
        first_expr = figurative.split(";")[0].strip()
        n_expr_words = len(first_expr.split())
        if n_expr_words > args.max_expression_words:
            continue
        pool.append({
            "example_id": r["example_id"],
            "original_text": text,
            "detected_expression": figurative,
            "system_replacement": replacement,
            "gold_replacement": (r.get("gold_replacement") or "").strip(),
            "_words": n_words,
            "_expr_words": n_expr_words,
            "_has_gold": bool((r.get("gold_replacement") or "").strip()),
        })

    print(f"after filter: {len(pool)} candidates")
    print(f"  with gold_replacement: {sum(1 for x in pool if x['_has_gold'])}")
    print(f"  word-count bins: <10={sum(1 for x in pool if x['_words']<10)} 10-14={sum(1 for x in pool if 10<=x['_words']<15)} 15-19={sum(1 for x in pool if 15<=x['_words']<20)}")

    # Prefer rows with gold_replacement; shuffle within preference tiers.
    with_gold = [x for x in pool if x["_has_gold"]]
    without = [x for x in pool if not x["_has_gold"]]
    random.shuffle(with_gold)
    random.shuffle(without)
    selected = (with_gold + without)[: args.n]
    print(f"selected: {len(selected)} (with_gold tier: {sum(1 for x in selected if x['_has_gold'])})")

    cols = [
        "example_id",
        "original_text",
        "detected_expression",
        "system_replacement",
        "human_rating_0_100",
        "human_alternative_paraphrase",
    ]
    with Path(args.output).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for x in selected:
            w.writerow({
                "example_id": x["example_id"],
                "original_text": x["original_text"],
                "detected_expression": x["detected_expression"],
                "system_replacement": x["system_replacement"],
                "human_rating_0_100": "",
                "human_alternative_paraphrase": "",
            })

    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
