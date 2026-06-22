"""
Recompute detection metrics on the survey-pool sources from the FROZEN
3-step-pipeline predictions that the human survey actually rated.

Motivation (WRITING_PLAN.md TODO(verify) / TODOS.md 25c): the automatic numbers
in tab:rq2-automatic (F1-sent 0.609/0.767, F1-span 0.282/...) and the
discussion scale-dependence paragraph predate the 2026-05-05 switch from the
single-call structured-CoT variant to the true 3-step pipeline (detect -> explain
-> transform). The survey rated the 3-step pipeline (runs aea60b3d / 460d4b15 /
10366af9). This script re-derives detection metrics from the survey items so the
reported numbers describe the system the survey rated.

Zero external dependencies (stdlib only). Detection F1 is binary; span F1 reuses
the IoU>=0.5 one-to-one matching from models/operations/evaluation.py.

BLEU / BERTScore are intentionally NOT recomputed: SemEval-2022 Task A has no gold
literal-paraphrase reference (columns: DataID, Language, MWE, Setting, Previous,
Target, Next, Label), so reference-based replacement metrics are not well defined
for this task. That is the methodological point the human survey exists to address.

Inputs (in the vault Survey dir):
  selected_sources.csv : source_id, example_id, original_text, gold_detected_expression, ...
  survey_items.csv     : item_id, source_id, system_id, original_text,
                         system_replacement, system_detected_expression, ...

Run: python3 scripts/recompute_survey_pool_detection.py
"""

import csv
import os

SURVEY_DIR = os.path.expanduser(
    "~/Documents/Obsidian Vault/1 - Thesis/Survey"
)
DETECTION_SYSTEMS = ["8b_agentic", "70b_agentic"]  # monolithic has no detect step
IOU_THRESHOLD = 0.5


def find_span(needle: str, haystack: str):
    """First case-insensitive occurrence of needle in haystack -> (start, end) or None."""
    if not needle or not needle.strip():
        return None
    i = haystack.lower().find(needle.strip().lower())
    if i < 0:
        return None
    return (i, i + len(needle.strip()))


def iou(a, b) -> float:
    if a is None or b is None:
        return 0.0
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = (a[1] - a[0]) + (b[1] - b[0]) - inter
    return inter / union if union else 0.0


def binary_prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * p * r / (p + r)) if (p + r) else 0.0
    return p, r, f1


def main():
    sources = {}
    with open(os.path.join(SURVEY_DIR, "selected_sources.csv")) as f:
        for row in csv.DictReader(f):
            sources[row["source_id"]] = row

    # system -> source_id -> detected expression string
    items = {s: {} for s in DETECTION_SYSTEMS}
    with open(os.path.join(SURVEY_DIR, "survey_items.csv")) as f:
        for row in csv.DictReader(f):
            sid = row["system_id"]
            if sid in items:
                items[sid][row["source_id"]] = row

    n_sources = len(sources)
    print(f"Survey pool: {n_sources} sources (all figurative; src_18 dropped).\n")
    print(f"{'system':<14} {'det/total':>10} {'sentP':>7} {'sentR':>7} {'sentF1':>7} "
          f"{'spanP':>7} {'spanR':>7} {'spanF1':>7} {'unmatched_str':>14}")

    results = {}
    for sysid in DETECTION_SYSTEMS:
        # sentence-level: gold_label is always 1 here; pred_label = detected
        sent_tp = sent_fp = sent_fn = 0
        span_tp = span_fp = span_fn = 0
        unmatched = 0  # detected string not locatable in source text
        detected = 0
        for src_id, src in sources.items():
            item = items[sysid].get(src_id)
            det = (item["system_detected_expression"].strip() if item else "")
            gold_span = find_span(src["gold_detected_expression"], src["original_text"])

            # sentence-level (gold positive for every survey source)
            pred_pos = bool(det)
            if pred_pos:
                detected += 1
                sent_tp += 1  # gold positive, predicted positive
            else:
                sent_fn += 1

            # span-level
            if det:
                pred_span = find_span(det, src["original_text"])
                if pred_span is None:
                    unmatched += 1
                    span_fp += 1  # produced a span we cannot localise -> not a TP
                elif gold_span and iou(pred_span, gold_span) >= IOU_THRESHOLD:
                    span_tp += 1
                else:
                    span_fp += 1
                    span_fn += 1
            else:
                span_fn += 1  # gold span exists, none predicted

        sp, sr, sf = binary_prf(sent_tp, sent_fp, sent_fn)
        pp, pr, pf = binary_prf(span_tp, span_fp, span_fn)
        results[sysid] = dict(detected=detected, n=n_sources,
                              sentP=sp, sentR=sr, sentF1=sf,
                              spanP=pp, spanR=pr, spanF1=pf, unmatched=unmatched)
        print(f"{sysid:<14} {f'{detected}/{n_sources}':>10} {sp:>7.3f} {sr:>7.3f} {sf:>7.3f} "
              f"{pp:>7.3f} {pr:>7.3f} {pf:>7.3f} {unmatched:>14}")

    print("\nNote: every survey-pool source is figurative (gold positive), so there are")
    print("no negative examples; sentence-level precision is 1.0 and sentence F1 reduces")
    print("to a function of detection recall. The proper P/R/F1 detection comparison with")
    print("negatives is the 200-example deterministic slice reported in RQ1.")
    return results


if __name__ == "__main__":
    main()
