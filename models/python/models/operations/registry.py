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
)

METRIC_REGISTRY = {
    "f1_token": compute_f1_token,
    "f1_span": compute_f1_span,
    "f1_sentence": compute_f1_sentence,
    "bleu": compute_bleu,
}
