"""Trace an ordinary Python function when LangSmith tracing is configured."""

from langsmith import traceable


@traceable(name="playbook-evidence-check")
def answer_from_evidence(question: str, evidence: list[str]) -> dict[str, object]:
    """Return matching evidence and abstain when no substring match is found.

    This deterministic toy check makes tracing visible without an LLM call; it
    is not a semantic search or production answer-quality evaluator.
    """
    matches = [item for item in evidence if question.lower() in item.lower()]
    return {"matches": matches, "abstained": not matches}


if __name__ == "__main__":
    print(answer_from_evidence("return window", ["Return window is 30 days."]))
