"""
Shared types and enums for the experiment framework.
Per PLAN.md §5-6: dataset types, phenomena, task types, run statuses, spans, detection results.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DatasetType(str, Enum):
    """Dataset source type."""
    VU_AMSTERDAM = "vu_amsterdam"
    SEMEVAL = "semeval"
    MANUAL = "manual"


class PhenomenonType(str, Enum):
    """Figurative language phenomenon type."""
    METAPHOR = "metaphor"
    IDIOM = "idiom"


class TaskType(str, Enum):
    """Experiment task type."""
    DETECTION = "detection"
    REPLACEMENT = "replacement"
    DETECT_THEN_REPLACE = "detect_then_replace"
    MONOLITHIC_REPLACE = "monolithic_replace"
    PIPELINE_REPLACE = "pipeline_replace"


class RunStatus(str, Enum):
    """Experiment run status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MetricName(str, Enum):
    """Supported evaluation metric names."""
    F1_TOKEN = "f1_token"
    F1_SPAN = "f1_span"
    F1_SENTENCE = "f1_sentence"
    BLEU = "bleu"
    PRECISION_TOKEN = "precision_token"
    RECALL_TOKEN = "recall_token"
    PRECISION_SPAN = "precision_span"
    RECALL_SPAN = "recall_span"
    BERTSCORE_PRECISION = "bertscore_precision"
    BERTSCORE_RECALL = "bertscore_recall"
    BERTSCORE_F1 = "bertscore_f1"


class Span(BaseModel):
    """Character-offset span. start is inclusive, end is exclusive."""
    start: int = Field(..., description="Inclusive start character offset")
    end: int = Field(..., description="Exclusive end character offset")

    def __eq__(self, other):
        if not isinstance(other, Span):
            return NotImplemented
        return self.start == other.start and self.end == other.end

    def __hash__(self):
        return hash((self.start, self.end))


class DetectionResult(BaseModel):
    """Structured detection output — used in both gold and predicted fields."""
    is_figurative: bool = False
    figurative_expressions: List[str] = Field(default_factory=list)
    token_labels: Optional[List[int]] = None
    spans: List[Span] = Field(default_factory=list)
