"""
Dataset Example entity — PLAN.md §5.1.
Key format: dataset::{dataset_name}::{example_id}
"""

from typing import Optional, List, Dict, Any, ClassVar
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from models.types.shared import DatasetType, PhenomenonType, DetectionResult
from clients.couchbase.couchbase import BaseModelCouchbase


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
            # SemEval: gold_detection required but spans may be empty if MWE
            # not found verbatim in text. gold_replacement is null because
            # SubTask B replacements are stored in metadata instead.
            if self.gold_detection is None:
                raise ValueError("SemEval examples require gold_detection")

        # Manual: gold fields optional — no validation needed
        return self

    def document_key(self) -> str:
        """Generate the Couchbase document key."""
        return f"dataset::{self.dataset.value}::{self.example_id}"


class DatasetExample(BaseModelCouchbase[DatasetExampleData]):
    """Couchbase document wrapper for dataset examples."""
    _collection_name: ClassVar[str] = "datasets"
    _bucket_name: ClassVar[str] = "main"

    @classmethod
    def get_keyspace(cls):
        """Override to use the 'main' bucket where experiment collections live."""
        from clients.couchbase.couchbase import get_keyspace as _get_keyspace
        return _get_keyspace(cls._collection_name, bucket_name=cls._bucket_name)

    @classmethod
    def create_with_key(cls, data: DatasetExampleData) -> "DatasetExample":
        """Create or upsert a document using the data's document_key()."""
        key = data.document_key()
        collection = cls.get_keyspace().get_collection()
        collection.upsert(key, data.model_dump(mode="json"))
        return cls(id=key, data=data)

