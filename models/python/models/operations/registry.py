"""
Metric Registry — PLAN.md §14.
Maps metric names to their computation functions.
Designed for future extensibility (BERTScore, semantic similarity, etc.).
"""

from models.operations.evaluation import (
    compute_f1_token,
    compute_f1_span,
    compute_f1_sentence,
    compute_bleu,
    compute_bertscore,
)

METRIC_REGISTRY = {
    "f1_token": compute_f1_token,
    "f1_span": compute_f1_span,
    "f1_sentence": compute_f1_sentence,
    "bleu": compute_bleu,
    "bertscore_precision": compute_bertscore,
    "bertscore_recall": compute_bertscore,
    "bertscore_f1": compute_bertscore,
}
