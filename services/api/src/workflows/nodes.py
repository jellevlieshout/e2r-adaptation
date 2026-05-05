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


def _invoke_llm_monolithic(state: GraphState, phenomenon: str) -> Dict[str, Any]:
    """Single LLM call producing only a free-text rewritten sentence.

    Differs from `_invoke_llm` in two load-bearing ways:
    - The prompt is a stub asking for a rewrite, with no explicit identify /
      reason / rewrite decomposition.
    - No structured output: `replacement_result` is the LLM's raw text reply,
      `detection_result` stays None.

    This is the RQ2 ablation against the agentic detect-then-replace graphs,
    isolating the effect of decomposition on replacement quality at fixed
    backbone, prompt-format conventions, and inference temperature.
    """
    try:
        system_prompt = load_prompt(phenomenon, "monolithic_replace")
        model = get_model(state)

        combined_prompt = f"{system_prompt}\n\nInput sentence: {state['input_text']}"
        messages = [HumanMessage(content=combined_prompt)]

        result = model.invoke(messages)
        replacement = result.content if hasattr(result, "content") else str(result)

        return {
            "detection_result": None,
            "replacement_result": replacement.strip(),
            "latency_ms": 0,
            "token_usage": {},
            "errors": [],
        }
    except Exception as e:
        return {"errors": [str(e)]}


def monolithic_replace_idiom(state: GraphState) -> Dict[str, Any]:
    return _invoke_llm_monolithic(state, "idiom")


def monolithic_replace_metaphor(state: GraphState) -> Dict[str, Any]:
    return _invoke_llm_monolithic(state, "metaphor")


# ---------------------------------------------------------------------------
# Pipeline (RQ2 — true 3-step agentic decomposition: detect → explain → transform)
#
# Each step is a separate LLM call with its own prompt. Intermediate state
# (detected expressions, per-expression explanations) is carried in GraphState
# so each step can read what the previous step wrote. This is the
# implementation H2 actually claims to test against the monolithic baseline.
# ---------------------------------------------------------------------------


class PipelineExplainItem(BaseModel):
    expression: str = Field(description="exact figurative expression (verbatim from the detected list)")
    meaning: str = Field(description="literal restatement of the expression's meaning in this context")


class PipelineExplainOutput(BaseModel):
    explanations: List[PipelineExplainItem]


def _pipeline_detect(state: GraphState, phenomenon: str) -> Dict[str, Any]:
    """Step 1 — detect figurative expressions. Reuses the existing detection
    prompt for `phenomenon`; writes `detection_result` to state. Equivalent
    behaviour to the standalone detect_idiom / detect_metaphor nodes.
    """
    return _invoke_llm(state, phenomenon, "detection")


def _pipeline_explain(state: GraphState, phenomenon: str) -> Dict[str, Any]:
    """Step 2 — for each detected expression, produce a literal-meaning
    paraphrase. Reads `detection_result.figurative_expressions`; writes
    `explanations_pipeline = [{expression, meaning}, …]` to state.

    If detection found nothing, short-circuit with empty explanations.
    """
    try:
        detection = state.get("detection_result")
        expressions: List[str] = []
        if detection is not None and getattr(detection, "is_figurative", False):
            expressions = list(detection.figurative_expressions or [])

        if not expressions:
            return {"explanations_pipeline": [], "errors": []}

        system_prompt = load_prompt(phenomenon, "explain")
        model = get_model(state)
        structured_llm = model.with_structured_output(PipelineExplainOutput)

        combined_prompt = (
            f"{system_prompt}\n\n"
            f"Sentence: {state['input_text']}\n"
            f"Detected {phenomenon}s: {json.dumps(expressions)}"
        )
        result: PipelineExplainOutput = structured_llm.invoke([HumanMessage(content=combined_prompt)])

        explanations = [{"expression": e.expression, "meaning": e.meaning} for e in result.explanations]
        return {"explanations_pipeline": explanations, "errors": []}

    except Exception as e:
        # Fall through with empty explanations rather than killing the run.
        # The transform step then operates on detection only (graceful degrade).
        logger.warning(f"pipeline_explain failed for {phenomenon}: {e}")
        return {"explanations_pipeline": [], "errors": [f"explain: {e}"]}


def _pipeline_transform(state: GraphState, phenomenon: str) -> Dict[str, Any]:
    """Step 3 — given the sentence, detected expressions, and per-expression
    meanings, produce the literal paraphrase. Reads `detection_result` and
    `explanations_pipeline`; writes `replacement_result` (free text).

    If detection found nothing, return the original sentence unchanged.
    """
    try:
        detection = state.get("detection_result")
        is_fig = detection is not None and getattr(detection, "is_figurative", False)

        if not is_fig:
            # No figurative expression detected — by contract the rewrite is
            # the original sentence (matches the existing detect-then-replace
            # behaviour).
            return {"replacement_result": state["input_text"], "errors": []}

        expressions = list(detection.figurative_expressions or [])
        explanations_records = state.get("explanations_pipeline") or []
        meanings_by_expr = {e.get("expression"): e.get("meaning", "") for e in explanations_records}
        meanings = [meanings_by_expr.get(expr, "") for expr in expressions]

        system_prompt = load_prompt(phenomenon, "transform")
        model = get_model(state)

        combined_prompt = (
            f"{system_prompt}\n\n"
            f"=== INPUT ===\n"
            f"Sentence: {state['input_text']}\n"
            f"Detected {phenomenon}s: {json.dumps(expressions)}\n"
            f"Meanings: {json.dumps(meanings)}"
        )
        result = model.invoke([HumanMessage(content=combined_prompt)])
        replacement = result.content if hasattr(result, "content") else str(result)
        return {"replacement_result": replacement.strip(), "errors": []}

    except Exception as e:
        return {"errors": [f"transform: {e}"]}


def pipeline_detect_idiom(state: GraphState) -> Dict[str, Any]:
    return _pipeline_detect(state, "idiom")


def pipeline_explain_idiom(state: GraphState) -> Dict[str, Any]:
    return _pipeline_explain(state, "idiom")


def pipeline_transform_idiom(state: GraphState) -> Dict[str, Any]:
    return _pipeline_transform(state, "idiom")


def pipeline_detect_metaphor(state: GraphState) -> Dict[str, Any]:
    return _pipeline_detect(state, "metaphor")


def pipeline_explain_metaphor(state: GraphState) -> Dict[str, Any]:
    return _pipeline_explain(state, "metaphor")


def pipeline_transform_metaphor(state: GraphState) -> Dict[str, Any]:
    return _pipeline_transform(state, "metaphor")
