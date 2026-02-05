from typing import TypedDict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
import conf

# --- Data Models ---

# This is the full output model required by the API
class MetaphorSpan(BaseModel):
    text: str = Field(description="The text of the metaphor")
    char_start: int = Field(description="Inclusive start index of the metaphor in the original text")
    char_end: int = Field(description="Exclusive end index of the metaphor in the original text")
    confidence: float = Field(description="Confidence score between 0 and 1")

class DetectionOutput(BaseModel):
    metaphor_spans: List[MetaphorSpan] = Field(description="List of detected metaphors")

# This is the simplified model for the LLM to generate
class LLMMetaphorSpan(BaseModel):
    text: str = Field(description="The text string of the identified metaphor.")
    confidence: float = Field(description="Confidence score between 0 and 1")

class LLMDetectionOutput(BaseModel):
    metaphor_spans: List[LLMMetaphorSpan] = Field(description="List of detected metaphors")

# --- State ---

class MetaphorState(TypedDict):
    text: str
    result: DetectionOutput

# --- Node ---

def metaphor_identification(state: MetaphorState):
    api_key = conf.get_openrouter_api_key()
    base_url = conf.get_openrouter_base_url()
    model_name = conf.get_openrouter_model()

    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model_name,
        temperature=0,
    )
    
    # Enforce structured output using the SIMPLIFIED model (no offsets)
    structured_llm = llm.with_structured_output(LLMDetectionOutput)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at identifying metaphors. Analyze the following text and identify metaphorical expressions."),
        ("system", "Return ONLY valid JSON. Extract the exact text of the metaphor."),
        ("user", "{text}")
    ])

    chain = prompt | structured_llm
    
    # Invoke LLM
    llm_response = chain.invoke({"text": state["text"]})
    
    if llm_response is None:
        llm_response = LLMDetectionOutput(metaphor_spans=[])

    # --- Post-processing: Calculate offsets ---
    validated_spans: List[MetaphorSpan] = []
    original_text = state["text"]
    
    # Track used indices to avoid overlapping logic if needed, or just finding the NEXT occurrence
    # For now, we'll try to find the best match.
    
    import re
    
    for span in llm_response.metaphor_spans:
        # We need to find 'span.text' in 'original_text'
        # We find ALL matches and pick the one that hasn't been used or just the first one?
        # A simple robust way for single sentences: find all, maybe pick first. 
        # But if the same word is used twice... let's just use the first occurrence for now.
        
        # Escape special regex chars in the metaphor text
        pattern = re.escape(span.text)
        
        # Search module
        match = re.search(pattern, original_text)
        
        if match:
            start_index = match.start()
            end_index = match.end()
            
            validated_spans.append(MetaphorSpan(
                text=span.text,
                char_start=start_index,
                char_end=end_index,
                confidence=span.confidence
            ))
        else:
            # LLM hallucinated text not in source. Skip.
            pass

    final_output = DetectionOutput(metaphor_spans=validated_spans)
    
    return {"result": final_output}

# --- Graph ---

builder = StateGraph(MetaphorState)
builder.add_node("metaphor_identification", metaphor_identification)
builder.add_edge(START, "metaphor_identification")
builder.add_edge("metaphor_identification", END)

graph = builder.compile()

def process_text_structured(text: str) -> DetectionOutput:
    """
    Process text through the Metaphor Identification Workflow and return structured data.
    """
    initial_state = {"text": text, "result": DetectionOutput(metaphor_spans=[])}
    final_state = graph.invoke(initial_state)
    return final_state["result"]

def process_text(text: str) -> str:
    """
    Legacy wrapper for process_text_structured to return a string representation.
    """
    result = process_text_structured(text)
    # Convert structured output to a simple string representation
    if not result.metaphor_spans:
        return "No metaphors detected."
    
    return "Detected metaphors: " + ", ".join([f"'{m.text}'" for m in result.metaphor_spans])


