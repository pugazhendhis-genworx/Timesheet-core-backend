from langgraph.graph import END, StateGraph

from src.control.agents.email_state import EmailProcessingState
from src.control.agents.nodes.email_nodes import (
    classify_email,
    extract_attachment_text,
    extract_timesheet,
    load_email,
)


def route_after_classification(state):
    if state.get("classification") == "TIMESHEET":
        return "extract_timesheet"
    return END


def route_after_extraction(state):
    """Skip classification if attachment extraction errored out."""
    if state.get("error"):
        return END
    return "classify_email"


def build_graph():

    graph = StateGraph(EmailProcessingState)

    graph.add_node("load_email", load_email)

    graph.add_node("extract_attachment_text", extract_attachment_text)

    graph.add_node("classify_email", classify_email)

    graph.add_node("extract_timesheet", extract_timesheet)

    graph.set_entry_point("load_email")

    graph.add_edge("load_email", "extract_attachment_text")

    graph.add_conditional_edges("extract_attachment_text", route_after_extraction)

    graph.add_conditional_edges("classify_email", route_after_classification)

    graph.add_edge("extract_timesheet", END)

    return graph.compile()


email_processing_graph = build_graph()
