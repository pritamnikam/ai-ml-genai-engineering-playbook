"""Trace an ordinary Python function when LangSmith tracing is configured."""

from langsmith import traceable


@traceable(name="playbook-evidence-check")
def answer_from_evidence(question: str, evidence: list[str]) -> dict[str, object]:
    matches = [item for item in evidence if question.lower() in item.lower()]
    return {"matches": matches, "abstained": not matches}


if __name__ == "__main__":
    print(answer_from_evidence("return window", ["Return window is 30 days."]))
