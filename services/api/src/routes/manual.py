import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.entities.dataset_example import DatasetExample, DatasetExampleData
from models.types.shared import DatasetType, PhenomenonType, DetectionResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manual", tags=["manual"])


class CreateManualExampleRequest(BaseModel):
    text: str
    phenomenon: PhenomenonType
    example_id: Optional[str] = None


class AnnotateManualExampleRequest(BaseModel):
    gold_detection: Optional[DetectionResult] = None
    gold_replacement: Optional[str] = None


@router.post("", response_model=DatasetExampleData)
async def create_manual_example(request: CreateManualExampleRequest):
    """
    Create a new manual dataset example.
    """
    example_id = request.example_id or str(uuid.uuid4())
    
    data = DatasetExampleData(
        dataset=DatasetType.MANUAL,
        phenomenon=request.phenomenon,
        example_id=example_id,
        text=request.text,
        created_at=datetime.utcnow()
    )
    
    try:
        DatasetExample.create_with_key(data)
        logger.info(f"Created manual example: {example_id}")
        return data
    except Exception as e:
        logger.error(f"Error creating manual example: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating example: {e}")


@router.post("/{example_id}/annotate", response_model=DatasetExampleData)
async def annotate_manual_example(example_id: str, request: AnnotateManualExampleRequest):
    """
    Annotate an existing manual example with gold labels/replacements.
    """
    ks = DatasetExample.get_keyspace()
    doc_id = f"dataset::manual::{example_id}"
    
    try:
        # Fetch existing
        result = ks.get_collection().get(doc_id)
        current_data = DatasetExampleData(**result.content_as[dict])
        
        # Update fields
        if request.gold_detection is not None:
            current_data.gold_detection = request.gold_detection
        if request.gold_replacement is not None:
            current_data.gold_replacement = request.gold_replacement
            
        # Upsert
        ks.get_collection().upsert(doc_id, current_data.model_dump(mode="json"))
        
        logger.info(f"Annotated manual example: {example_id}")
        return current_data
        
    except Exception as e:
        logger.error(f"Error annotating manual example {example_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Example {example_id} not found or update failed")
