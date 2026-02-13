"""
Evaluation metrics — PLAN.md §8 + §14.
Pure functions that compute metrics from gold vs. predicted data.
"""

from typing import List, Dict, Optional
from models.types.shared import Span


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def span_iou(a: Span, b: Span) -> float:
    """Compute Intersection-over-Union for two character-offset spans."""
    intersection_start = max(a.start, b.start)
    intersection_end = min(a.end, b.end)
    intersection = max(0, intersection_end - intersection_start)

    union = (a.end - a.start) + (b.end - b.start) - intersection
    if union == 0:
        return 0.0
    return intersection / union


# ---------------------------------------------------------------------------
# Token-level F1 (§8.1)
# ---------------------------------------------------------------------------

def compute_f1_token(
    gold_labels: List[int],
    pred_labels: List[int],
) -> Dict[str, float]:
    """
    Token-level precision / recall / F1 using sklearn.
    Labels are binary: 0 = literal, 1 = figurative.

    Returns:
        {"precision_token": ..., "recall_token": ..., "f1_token": ...}
    """
    from sklearn.metrics import precision_recall_fscore_support

    precision, recall, f1, _ = precision_recall_fscore_support(
        gold_labels, pred_labels, average="binary", zero_division=0
    )
    return {
        "precision_token": float(precision),
        "recall_token": float(recall),
        "f1_token": float(f1),
    }


# ---------------------------------------------------------------------------
# Span-level F1 (§8.1 + §8.2) — IoU ≥ 0.5
# ---------------------------------------------------------------------------

def compute_f1_span(
    gold_spans: List[Span],
    pred_spans: List[Span],
    iou_threshold: float = 0.5,
) -> Dict[str, float]:
    """
    Span-level precision / recall / F1.
    A predicted span is a true positive if it overlaps any unmatched gold span
    with IoU >= iou_threshold.

    Returns:
        {"precision_span": ..., "recall_span": ..., "f1_span": ...}
    """
    matched_gold: set[int] = set()
    tp = 0

    for pred in pred_spans:
        for gi, gold in enumerate(gold_spans):
            if gi in matched_gold:
                continue
            if span_iou(pred, gold) >= iou_threshold:
                tp += 1
                matched_gold.add(gi)
                break  # one-to-one matching

    fp = len(pred_spans) - tp
    fn = len(gold_spans) - tp

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "precision_span": precision,
        "recall_span": recall,
        "f1_span": f1,
    }


# ---------------------------------------------------------------------------
# Sentence-level F1 (§8.2) — binary: is_figurative = len(spans) > 0
# ---------------------------------------------------------------------------

def compute_f1_sentence(
    gold_spans: List[Span],
    pred_spans: List[Span],
) -> Dict[str, float]:
    """
    Sentence-level binary F1.
    A sentence is figurative iff it has at least one span.

    Returns:
        {"f1_sentence": ...}
    """
    from sklearn.metrics import precision_recall_fscore_support

    gold_label = 1 if len(gold_spans) > 0 else 0
    pred_label = 1 if len(pred_spans) > 0 else 0

    precision, recall, f1, _ = precision_recall_fscore_support(
        [gold_label], [pred_label], average="binary", zero_division=0
    )
    return {"f1_sentence": float(f1)}


# ---------------------------------------------------------------------------
# BLEU (§8.3) — idiom replacement only
# ---------------------------------------------------------------------------

def compute_bleu(
    gold_replacement: Optional[str],
    pred_replacement: Optional[str],
) -> Dict[str, float]:
    """
    Compute sentence-level BLEU between gold and predicted replacement.
    Only applicable when gold_replacement is not None (idiom task).

    Returns:
        {"bleu": ...}
    """
    if gold_replacement is None or pred_replacement is None:
        return {"bleu": 0.0}

    from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

    reference = [gold_replacement.split()]
    hypothesis = pred_replacement.split()

    score = sentence_bleu(
        reference,
        hypothesis,
        smoothing_function=SmoothingFunction().method1,
    )
    return {"bleu": float(score)}
