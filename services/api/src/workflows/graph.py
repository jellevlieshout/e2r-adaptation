from langgraph.graph import StateGraph, START, END

from workflows.nodes import (
    detect_metaphor,
    detect_idiom,
    replace_metaphor,
    replace_idiom,
    monolithic_replace_metaphor,
    monolithic_replace_idiom,
    pipeline_detect_idiom,
    pipeline_explain_idiom,
    pipeline_transform_idiom,
    pipeline_detect_metaphor,
    pipeline_explain_metaphor,
    pipeline_transform_metaphor,
)
from workflows.state import GraphState


def create_metaphor_detection_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("detect_metaphor", detect_metaphor)
    workflow.add_edge(START, "detect_metaphor")
    workflow.add_edge("detect_metaphor", END)
    return workflow.compile()


def create_idiom_detection_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("detect_idiom", detect_idiom)
    workflow.add_edge(START, "detect_idiom")
    workflow.add_edge("detect_idiom", END)
    return workflow.compile()


def create_metaphor_detect_then_replace_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("replace_metaphor", replace_metaphor)
    workflow.add_edge(START, "replace_metaphor")
    workflow.add_edge("replace_metaphor", END)
    return workflow.compile()


def create_idiom_detect_then_replace_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("replace_idiom", replace_idiom)
    workflow.add_edge(START, "replace_idiom")
    workflow.add_edge("replace_idiom", END)
    return workflow.compile()


def create_metaphor_monolithic_replace_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("monolithic_replace_metaphor", monolithic_replace_metaphor)
    workflow.add_edge(START, "monolithic_replace_metaphor")
    workflow.add_edge("monolithic_replace_metaphor", END)
    return workflow.compile()


def create_idiom_monolithic_replace_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("monolithic_replace_idiom", monolithic_replace_idiom)
    workflow.add_edge(START, "monolithic_replace_idiom")
    workflow.add_edge("monolithic_replace_idiom", END)
    return workflow.compile()


def create_idiom_pipeline_replace_graph():
    """Three-step agentic pipeline (RQ2): detect → explain → transform.

    Each step is its own LLM call; intermediate state (detected expressions,
    per-expression explanations) flows through GraphState. The output is a
    free-text rewritten sentence on the same contract as the other replace
    graphs, plus an `explanations_pipeline` field persisted alongside the
    prediction document for H4 analysis.
    """
    workflow = StateGraph(GraphState)
    workflow.add_node("pipeline_detect_idiom", pipeline_detect_idiom)
    workflow.add_node("pipeline_explain_idiom", pipeline_explain_idiom)
    workflow.add_node("pipeline_transform_idiom", pipeline_transform_idiom)
    workflow.add_edge(START, "pipeline_detect_idiom")
    workflow.add_edge("pipeline_detect_idiom", "pipeline_explain_idiom")
    workflow.add_edge("pipeline_explain_idiom", "pipeline_transform_idiom")
    workflow.add_edge("pipeline_transform_idiom", END)
    return workflow.compile()


def create_metaphor_pipeline_replace_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("pipeline_detect_metaphor", pipeline_detect_metaphor)
    workflow.add_node("pipeline_explain_metaphor", pipeline_explain_metaphor)
    workflow.add_node("pipeline_transform_metaphor", pipeline_transform_metaphor)
    workflow.add_edge(START, "pipeline_detect_metaphor")
    workflow.add_edge("pipeline_detect_metaphor", "pipeline_explain_metaphor")
    workflow.add_edge("pipeline_explain_metaphor", "pipeline_transform_metaphor")
    workflow.add_edge("pipeline_transform_metaphor", END)
    return workflow.compile()


# Exposed graphs
metaphor_detection_graph = create_metaphor_detection_graph()
idiom_detection_graph = create_idiom_detection_graph()
metaphor_detect_then_replace_graph = create_metaphor_detect_then_replace_graph()
idiom_detect_then_replace_graph = create_idiom_detect_then_replace_graph()
metaphor_monolithic_replace_graph = create_metaphor_monolithic_replace_graph()
idiom_monolithic_replace_graph = create_idiom_monolithic_replace_graph()
metaphor_pipeline_replace_graph = create_metaphor_pipeline_replace_graph()
idiom_pipeline_replace_graph = create_idiom_pipeline_replace_graph()


# Helper to get the correct graph
def get_graph(phenomenon: str, task_type: str):
    if phenomenon == "metaphor":
        if task_type == "detection":
            return metaphor_detection_graph
        elif task_type == "detect_then_replace":
            return metaphor_detect_then_replace_graph
        elif task_type == "monolithic_replace":
            return metaphor_monolithic_replace_graph
        elif task_type == "pipeline_replace":
            return metaphor_pipeline_replace_graph
    elif phenomenon == "idiom":
        if task_type == "detection":
            return idiom_detection_graph
        elif task_type == "detect_then_replace":
            return idiom_detect_then_replace_graph
        elif task_type == "monolithic_replace":
            return idiom_monolithic_replace_graph
        elif task_type == "pipeline_replace":
            return idiom_pipeline_replace_graph

    raise ValueError(f"No graph found for phenomenon={phenomenon}, task_type={task_type}")
