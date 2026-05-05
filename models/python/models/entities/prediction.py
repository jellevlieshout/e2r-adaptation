"""
Prediction entity — PLAN.md §5.3.
Key format: prediction::{run_id}::{example_id}
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from models.types.shared import DatasetType, PhenomenonType, TaskType, DetectionResult


class PredictionData(BaseModel):
    """Data payload for a prediction document."""
    type: str = "prediction"
    run_id: str
    example_id: str
    dataset: DatasetType
    phenomenon: PhenomenonType
    task_type: TaskType
    input_text: str
    predicted_detection: Optional[DetectionResult] = None
    predicted_replacement: Optional[str] = None
    # Per-expression literal-meaning explanations from the pipeline_replace
    # graph's explain step. Stored as a list of {expression, meaning} dicts.
    # Populated only by pipeline_replace runs; None for other task types.
    # Required for post-hoc H4 (explanation ↔ correctness) analysis.
    intermediate_explanations: Optional[List[Dict[str, str]]] = None
    raw_model_output: Optional[str] = None
    latency_ms: Optional[float] = None
    token_usage: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def document_key(self) -> str:
        """Generate the Couchbase document key."""
        return f"prediction::{self.run_id}::{self.example_id}"
