import json
import os
from typing import Any, Dict, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from workflows.state import GraphState
from models.operations import load_prompt

class DetectionResult(BaseModel):
    is_figurative: bool
    explanation: str

class ReplacementDetails(BaseModel):
    literal_paraphrase: str

class TaskOutput(BaseModel):
    detection: DetectionResult
    replacement: Optional[ReplacementDetails] = None

def get_model(state: GraphState) -> ChatOpenAI:
    # Import locally to avoid potential circular dependencies if any
    from clients.openrouter.client import OpenRouterClient
    client = OpenRouterClient()
    return client.get_chat_model(state["model_name"], state["temperature"])

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
        
        updates = {
            "detection_result": result.detection,
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
