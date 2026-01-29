from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import uuid
import datetime
from workflows.metaphor import process_text

# Define models here since they are simple and specific to this endpoint for now
class AdaptationRequest(BaseModel):
    text: str

class FigurativeExpression(BaseModel):
    id: str
    type: str
    original: str
    startIndex: int
    endIndex: int
    explanation: str
    simplifiedVersion: str

class AdaptationResponse(BaseModel):
    id: str
    originalText: str
    adaptedText: str
    expressions: List[FigurativeExpression]
    createdAt: str

router = APIRouter()

@router.post("/adapt", response_model=AdaptationResponse)
async def adapt_text(request: AdaptationRequest):
    """
    Receive text, log it to console, and return a mock response.
    """
    # Log to console as requested
    print(f"Received adaptation request: {request.text}")

    # Run workflow
    result = process_text(request.text)

    # Mock response
    return AdaptationResponse(
        id=str(uuid.uuid4()),
        originalText=request.text,
        adaptedText=result, # Result from LangGraph workflow
        expressions=[],
        createdAt=datetime.datetime.now().isoformat()
    )
