import asyncio
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from clients.vuamc.client import VUAMCClient
from clients.vuamc.models import Token as VUAMCToken, Sentence as VUAMCSentence

router = APIRouter(prefix="/vuamc", tags=["vuamc"])

# Path to the dataset in the container
DATASET_PATH = Path("/datasets/vu-amsterdam-metaphor-corpus/VUAMC.xml")

class TokenResponse(BaseModel):
    text: str
    lemma: str
    pos: str
    is_metaphor: bool
    metaphor_type: Optional[str] = None
    function: Optional[str] = None
    status: Optional[str] = None

class SentenceResponse(BaseModel):
    id: str
    text: str
    tokens: List[TokenResponse]

class MetaphorResponse(BaseModel):
    token: TokenResponse
    sentence: SentenceResponse
    document_id: str

_client: Optional[VUAMCClient] = None

def get_client() -> VUAMCClient:
    global _client
    if _client is None:
        if not DATASET_PATH.exists():
            raise HTTPException(status_code=500, detail=f"Dataset not found at {DATASET_PATH}")
        _client = VUAMCClient(str(DATASET_PATH))
    return _client

@router.get("/metaphors", response_model=List[MetaphorResponse])
async def list_metaphors(
    search: Optional[str] = Query(None, description="Search term for metaphor text"),
    limit: int = Query(50, ge=1, le=200, description="Max number of results to return"),
    metaphor_type: Optional[str] = Query(None, description="Filter by metaphor type")
):
    """
    Search and list metaphors from the VUAMC dataset.
    This is a naive implementation that iterates through the XML on request.
    For production, this should be indexed in a database.
    """
    client = get_client()
    
    results = []
    
    # We'll limit how many documents we check to avoid timeouts if scanning everything
    # But since we stream, we can just stop when we hit the limit
    
    try:
        # Run the CPU-bound XML parsing in a thread pool to avoid blocking the event loop
        # However, the client is an iterator. We might need to handle this carefully.
        # For simplicity in this first pass, we'll iterate directly but be mindful of performance.
        
        count = 0
        for doc in client.documents():
            for sentence in doc.sentences:
                for token in sentence.tokens:
                    # Note: We now treat mFlags as metaphors too (is_metaphor=True in client if mFlag)
                    if token.is_metaphor:
                        # Apply filters
                        if search and search.lower() not in token.text.lower():
                            continue
                        if metaphor_type and token.metaphor_type != metaphor_type:
                            continue
                        
                        # Match found
                        results.append(MetaphorResponse(
                            token=TokenResponse(
                                text=token.text,
                                lemma=token.lemma,
                                pos=token.pos,
                                is_metaphor=token.is_metaphor,
                                metaphor_type=token.metaphor_type,
                                function=token.function,
                                status=token.status
                            ),
                            sentence=SentenceResponse(
                                id=sentence.id,
                                text=sentence.text,
                                tokens=[
                                    TokenResponse(
                                        text=t.text,
                                        lemma=t.lemma,
                                        pos=t.pos,
                                        is_metaphor=t.is_metaphor,
                                        metaphor_type=t.metaphor_type,
                                        function=t.function,
                                        status=t.status
                                    ) for t in sentence.tokens
                                ]
                            ),
                            document_id=doc.id
                        ))
                        count += 1
                        
                        if count >= limit:
                            return results
                            
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")
