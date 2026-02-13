"""
Evaluation entity — PLAN.md §5.4.
Key format: evaluation::{run_id}::{metric_name}
"""

from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from models.types.shared import MetricName


class EvaluationData(BaseModel):
    """Data payload for an evaluation document."""
    type: str = "evaluation"
    run_id: str
    metric_name: MetricName
    value: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def document_key(self) -> str:
        """Generate the Couchbase document key."""
        return f"evaluation::{self.run_id}::{self.metric_name.value}"
