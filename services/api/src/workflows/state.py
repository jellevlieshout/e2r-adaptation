import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict, Union

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

    # Pipeline (RQ2 — true 3-step decomposition: detect → explain → transform)
    # Populated only by the pipeline_replace task type. The explain step writes
    # explanations_pipeline; the transform step reads it. Persisted alongside
    # the prediction document so post-hoc H4 analysis (explanation quality vs
    # final-replacement correctness) is possible.
    explanations_pipeline: Optional[List[Dict[str, str]]]

    # Metadata
    latency_ms: float
    token_usage: dict

    # Error handling
    errors: Annotated[List[str], operator.add]
