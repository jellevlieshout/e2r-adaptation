import json
import logging
import os
from typing import Any, Dict, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from workflows.state import GraphState
from models.operations import load_prompt
from models.operations.spans import normalize_spans
from models.types.shared import DetectionResult, Span

logger = logging.getLogger(__name__)


class LLMDetectionResult(BaseModel):
    is_figurative: bool = Field(description="Whether the text contains figurative language")
    figurative_expressions: List[str] = Field(
        default_factory=list,
        description="Exact verbatim quotes of figurative expressions from the input text. Empty if is_figurative is false."
    )
    explanation: str = Field(description="Brief explanation of the detection reasoning")


class ReplacementDetails(BaseModel):
    literal_paraphrase: str


class TaskOutput(BaseModel):
    detection: LLMDetectionResult
    replacement: Optional[ReplacementDetails] = None


def _expressions_to_spans(expressions: List[str], input_text: str) -> List[Span]:
    """Convert verbatim expression quotes to character-offset Span objects."""
    spans = []
    for expr in expressions:
        pos = input_text.find(expr)
        if pos < 0:
            # Fallback: case-insensitive search
            pos = input_text.lower().find(expr.lower())
        if pos >= 0:
            spans.append(Span(start=pos, end=pos + len(expr)))
        else:
            logger.warning("Expression not found in input text: %r", expr)
    return normalize_spans(spans, len(input_text))


def _derive_token_labels(input_text: str, spans: List[Span]) -> List[int]:
    """Derive per-token binary labels (0=literal, 1=figurative) from character spans."""
    tokens = input_text.split()
    labels = []
    char_pos = 0
    for token in tokens:
        token_start = char_pos
        token_end = char_pos + len(token)
        # Token is figurative if any span overlaps it
        is_fig = any(
            span.start < token_end and span.end > token_start
            for span in spans
        )
        labels.append(1 if is_fig else 0)
        char_pos = token_end + 1  # +1 for space
    return labels


VLLM_MODEL_PREFIX = "vllm:"


def get_model(state: GraphState) -> ChatOpenAI:
    """Dispatch on a `vllm:` prefix in model_name to route to the UPM cluster.

    Examples:
        "google/gemini-3-flash-preview"            -> OpenRouter
        "vllm:Qwen/Qwen2.5-7B-Instruct"            -> UPM vLLM cluster
    """
    model_name: str = state["model_name"]
    temperature: float = state["temperature"]

    if model_name.startswith(VLLM_MODEL_PREFIX):
        from clients.vllm.client import VLLMClient
        client = VLLMClient()
        actual_model = model_name[len(VLLM_MODEL_PREFIX):]
        return client.get_chat_model(actual_model, temperature)

    from clients.openrouter.client import OpenRouterClient
    client = OpenRouterClient()
    return client.get_chat_model(model_name, temperature)

def _invoke_llm(state: GraphState, phenomenon: str, task_type: str) -> Dict[str, Any]:
    try:
        system_prompt = load_prompt(phenomenon, task_type)
        model = get_model(state)
        structured_llm = model.with_structured_output(TaskOutput)

        # Combine system prompt and human message for broader model compatibility.
        # Some models (like Gemma-3 on Google AI Studio) don't support separate system instructions.
        combined_prompt = f"{system_prompt}\n\nInput text: {state['input_text']}"
        messages = [
            HumanMessage(content=combined_prompt)
        ]

        result: TaskOutput = structured_llm.invoke(messages)

        # Convert verbatim expressions to spans
        input_text = state["input_text"]
        expressions = result.detection.figurative_expressions if result.detection.is_figurative else []
        spans = _expressions_to_spans(expressions, input_text)

        # Derive token_labels from spans
        token_labels = _derive_token_labels(input_text, spans)

        shared_detection = DetectionResult(
            is_figurative=result.detection.is_figurative,
            figurative_expressions=expressions,
            spans=spans,
            token_labels=token_labels,
        )

        updates = {
            "detection_result": shared_detection,
            "latency_ms": 0,
            "token_usage": {},
            "errors": []
        }

        if result.replacement:
            updates["replacement_result"] = result.replacement.literal_paraphrase
        else:
            updates["replacement_result"] = None

        return updates

    except Exception as e:
        return {"errors": [str(e)]}


def detect_metaphor(state: GraphState) -> Dict[str, Any]:
    return _invoke_llm(state, "metaphor", "detection")


def replace_metaphor(state: GraphState) -> Dict[str, Any]:
    return _invoke_llm(state, "metaphor", "replacement")


def detect_idiom(state: GraphState) -> Dict[str, Any]:
    return _invoke_llm(state, "idiom", "detection")


def replace_idiom(state: GraphState) -> Dict[str, Any]:
    return _invoke_llm(state, "idiom", "replacement")
