from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
import conf

# Define State
class MetaphorState(TypedDict):
    text: str
    result: str

# Define Node
def metaphor_identification(state: MetaphorState):
    api_key = conf.get_openrouter_api_key()
    base_url = conf.get_openrouter_base_url()
    model_name = conf.get_openrouter_model()

    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model_name,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert at identifying metaphors. Analyze the following text and determine if it contains any metaphors."),
        ("user", "{text}")
    ])

    chain = prompt | llm
    
    response = chain.invoke({"text": state["text"]})
    
    return {"result": response.content}

# Build Graph
builder = StateGraph(MetaphorState)
builder.add_node("metaphor_identification", metaphor_identification)
builder.add_edge(START, "metaphor_identification")
builder.add_edge("metaphor_identification", END)

graph = builder.compile()

def process_text(text: str) -> str:
    """
    Process text through the Metaphor Identification Workflow.
    """
    initial_state = {"text": text, "result": ""}
    final_state = graph.invoke(initial_state)
    return final_state["result"]
