import operator
from typing import Annotated, List, Optional, TypedDict, Union

from models.types.shared import DetectionResult


class GraphState(TypedDict):
    """
    Represents the state of the graph.
    """
    input_text: str
    dataset: str  # vu_amsterdam, semeval
    phenomenon: str  # metaphor, idiom
    model_name: str
    temperature: float
    
    # Results
    detection_result: Optional[DetectionResult]
    replacement_result: Optional[str]
    
    # Metadata
    latency_ms: float
    token_usage: dict
    
    # Error handling
    errors: Annotated[List[str], operator.add]
