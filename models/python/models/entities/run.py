"""
Run entity — PLAN.md §5.2.
Key format: run::{run_id}
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from models.types.shared import DatasetType, PhenomenonType, TaskType, RunStatus


class RunStats(BaseModel):
    """Counters tracking run progress."""
    total_examples: int = 0
    completed: int = 0
    failed: int = 0


class RunData(BaseModel):
    """Data payload for a run document."""
    type: str = "run"
    run_id: str
    dataset: DatasetType
    phenomenon: PhenomenonType
    task_type: TaskType
    model_name: str
    temperature: float = 0
    top_p: float = 1
    prompt_version: str
    prompt_hash: str = ""
    prompt_text: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: RunStatus = RunStatus.RUNNING
    stats: RunStats = Field(default_factory=RunStats)

    def document_key(self) -> str:
        """Generate the Couchbase document key."""
        return f"run::{self.run_id}"
