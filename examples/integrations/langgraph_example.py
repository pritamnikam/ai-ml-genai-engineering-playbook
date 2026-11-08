"""A small deterministic LangGraph workflow with a human-approval branch."""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class WorkflowState(TypedDict):
    approved: bool
    action: str
    status: str


def decide(state: WorkflowState) -> WorkflowState:
    return {
        **state,
        "status": "executed" if state["approved"] else "awaiting_human_approval",
    }


def route(state: WorkflowState) -> Literal["finish", "approval_required"]:
    return "finish" if state["approved"] else "approval_required"


def build_workflow():
    graph = StateGraph(WorkflowState)
    graph.add_node("decide", decide)
    graph.add_edge(START, "decide")
    graph.add_conditional_edges(
        "decide",
        route,
        {"finish": END, "approval_required": END},
    )
    return graph.compile()


if __name__ == "__main__":
    workflow = build_workflow()
    print(workflow.invoke({"approved": False, "action": "send_email", "status": "new"}))
