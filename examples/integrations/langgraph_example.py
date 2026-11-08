"""A small deterministic LangGraph workflow with a human-approval branch."""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class WorkflowState(TypedDict):
    """State carried through the approval decision graph."""

    approved: bool
    action: str
    status: str


def decide(state: WorkflowState) -> WorkflowState:
    """Record whether the action may proceed or needs human approval."""
    return {
        **state,
        "status": "executed" if state["approved"] else "awaiting_human_approval",
    }


def route(state: WorkflowState) -> Literal["finish", "approval_required"]:
    """Choose a named graph branch from the approval decision."""
    return "finish" if state["approved"] else "approval_required"


def build_workflow():
    """Compile the decision graph; this demo intentionally performs no side effect."""
    graph = StateGraph(WorkflowState)
    graph.add_node("decide", decide)
    graph.add_edge(START, "decide")
    graph.add_conditional_edges(
        "decide",
        route,
        # Both outcomes stop here: the example demonstrates routing, not sending
        # an email or pretending an unapproved action was executed.
        {"finish": END, "approval_required": END},
    )
    return graph.compile()


if __name__ == "__main__":
    workflow = build_workflow()
    print(workflow.invoke({"approved": False, "action": "send_email", "status": "new"}))
