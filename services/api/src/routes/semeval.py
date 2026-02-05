from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from clients.semeval2022.client import SemEval2022Client
from clients.semeval2022.models import SemEvalSample

router = APIRouter(prefix="/semeval", tags=["semeval"])

DATASET_PATH = Path("/datasets/SemEval2022_Task2")

# Pydantic model for response (can be same as client model or explicit)
# We'll redefine for clarity in API docs
class SemEvalSampleResponse(BaseModel):
    id: str
    mwe1: str
    language: str
    sentence1: str
    sentence2: Optional[str] = None
    mwe2: Optional[str] = None
    sim: Optional[str] = None
    label: Optional[str] = None
    context_previous: Optional[str] = None
    context_next: Optional[str] = None
    setting: Optional[str] = None
    alternative1: Optional[str] = None
    alternative2: Optional[str] = None

_client: Optional[SemEval2022Client] = None

def get_client() -> SemEval2022Client:
    global _client
    if _client is None:
        if not DATASET_PATH.exists():
            raise HTTPException(status_code=500, detail=f"Dataset not found at {DATASET_PATH}")
        _client = SemEval2022Client(str(DATASET_PATH))
    return _client

@router.get("/samples", response_model=List[SemEvalSampleResponse])
async def list_samples(
    task: Optional[str] = Query(None, description="Task A or B"),
    split: Optional[str] = Query(None, description="train, dev, or test"),
    language: Optional[str] = Query(None, description="Language code (e.g., EN, PT)"),
    limit: int = Query(50, ge=1, le=200, description="Max results")
):
    client = get_client()
    
    results = []
    count = 0
    try:
        # Client iterator handles parsing
        for sample in client.list_samples(task=task, split=split, language=language):
             results.append(SemEvalSampleResponse(
                 id=sample.id,
                 mwe1=sample.mwe1,
                 language=sample.language,
                 sentence1=sample.sentence1,
                 sentence2=sample.sentence2,
                 mwe2=sample.mwe2,
                 sim=sample.sim,
                 label=sample.label,
                 context_previous=sample.context_previous,
                 context_next=sample.context_next,
                 setting=sample.setting,
                 alternative1=sample.alternative1,
                 alternative2=sample.alternative2
             ))
             count += 1
             if count >= limit:
                 break
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading dataset: {str(e)}")
        
    return results
