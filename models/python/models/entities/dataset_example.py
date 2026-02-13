"""
Dataset Example entity — PLAN.md §5.1.
Key format: dataset::{dataset_name}::{example_id}
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from models.types.shared import DatasetType, PhenomenonType, DetectionResult


class DatasetExampleData(BaseModel):
    """Data payload for a dataset example document."""
    type: str = "dataset_example"
    dataset: DatasetType
    phenomenon: PhenomenonType
    example_id: str
    text: str
    tokens: Optional[List[str]] = None
    gold_detection: Optional[DetectionResult] = None
    gold_replacement: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_dataset_rules(self):
        """Enforce per-dataset validation rules from PLAN.md §5.1."""
        if self.dataset == DatasetType.VU_AMSTERDAM:
            # VU: token_labels required, gold_replacement must be null
            if self.gold_detection is None or self.gold_detection.token_labels is None:
                raise ValueError("VU Amsterdam examples require gold_detection.token_labels")
            if self.gold_replacement is not None:
                raise ValueError("VU Amsterdam examples must have gold_replacement = null")

        elif self.dataset == DatasetType.SEMEVAL:
            # SemEval: spans required, gold_replacement required
            if self.gold_detection is None or not self.gold_detection.spans:
                raise ValueError("SemEval examples require gold_detection.spans")
            if self.gold_replacement is None:
                raise ValueError("SemEval examples require gold_replacement")

        # Manual: gold fields optional — no validation needed
        return self

    def document_key(self) -> str:
        """Generate the Couchbase document key."""
        return f"dataset::{self.dataset.value}::{self.example_id}"
