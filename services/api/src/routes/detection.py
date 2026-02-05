from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from workflows.metaphor import process_text_structured, DetectionOutput, MetaphorSpan

router = APIRouter(tags=["detection"])

class DetectionInput(BaseModel):
    task: str = Field(..., pattern="^metaphor_detection$")
    text: str
    language: str = Field("en", pattern="^en$")

class DetectionResponse(BaseModel):
    metaphor_spans: List[MetaphorSpan]

@router.post("/detect", response_model=DetectionResponse)
async def detect_metaphors(request: DetectionInput):
    """
    Detect metaphors in the given text using the configured LLM.
    Returns structured output with character offsets.
    """
    try:
        result: DetectionOutput = process_text_structured(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
