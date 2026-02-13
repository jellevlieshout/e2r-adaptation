import json
import os
from typing import Any, Dict, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from models.types.shared import DetectionResult
from workflows.state import GraphState


class ReplacementOutput(BaseModel):
    literal_paraphrase: str


class TaskOutput(BaseModel):
    detection: DetectionResult
    replacement: Optional[ReplacementOutput] = None
    confidence: float = Field(description="Confidence score between 0 and 1")


# Initialize model
# We assume OPENAI_API_KEY is set in the environment or OPENROUTER_API_KEY
# If OPENROUTER_API_KEY is present, we configure for OpenRouter
def get_model(state: GraphState):
    model_name = state.get("model_name", "gpt-4o")
    temperature = state.get("temperature", 0.0)
    
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
    if openrouter_api_key:
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    
    return ChatOpenAI(model=model_name, temperature=temperature)


def _invoke_llm(state: GraphState, system_prompt: str) -> Dict[str, Any]:
    try:
        model = get_model(state)
        structured_llm = model.with_structured_output(TaskOutput)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Input text: {state['input_text']}")
        ]
        
        result: TaskOutput = structured_llm.invoke(messages)
        
        updates = {
            "detection_result": result.detection,
            "latency_ms": 0, # Placeholder, we can add timing logic if needed
            "token_usage": {}, # Placeholder, depending on if we can get usage from structured_output
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
    prompt = """You are an expert in linguistics and metaphor detection.
    Analyze the provided text and detect if it contains any metaphorical usage.
    Focus on the VU Amsterdam Metaphor Corpus guidelines.
    Return the detection results including is_figurative flag, token_labels (0 for literal, 1 for metaphor), and character-offset spans.
    For the replacement field, return null as we are only detecting."""
    
    return _invoke_llm(state, prompt)


def replace_metaphor(state: GraphState) -> Dict[str, Any]:
    # This node might be used in a different flow or after detection
    # For detect_then_replace, we can do it in one shot or chain them.
    # The plan implies separate workflows or combined.
    # If we already have detection, we might want to pass it? 
    # For now let's implement a direct replacement assuming input text.
    
    prompt = """You are an expert in linguistics.
    Identify any metaphors in the text and provide a literal paraphrase.
    Return both the detection details and the literal paraphrase."""
    
    return _invoke_llm(state, prompt)


def detect_idiom(state: GraphState) -> Dict[str, Any]:
    prompt = """You are an expert in linguistics and idiom detection.
    Analyze the provided text and detect if it contains any idiomatic expressions.
    Focus on SemEval Task 2 guidelines.
    Return the detection results including is_figurative flag and character-offset spans.
    Token labels are optional but spans are required.
    For the replacement field, return null as we are only detecting."""
    
    return _invoke_llm(state, prompt)


def replace_idiom(state: GraphState) -> Dict[str, Any]:
    prompt = """You are an expert in linguistics.
    Identify any idiomatic expressions in the text and provide a literal paraphrase.
    Return both the detection details and the literal paraphrase."""
    
    return _invoke_llm(state, prompt)
