import json
import re
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]


def test_every_concept_has_a_guide_and_runnable_notebook() -> None:
    guides = sorted(
        path.stem for path in (ROOT / "guides" / "concepts").glob("[0-9][0-9][0-9]-*.md")
    )
    notebooks = sorted(
        path.stem for path in (ROOT / "notebooks").glob("[0-9][0-9][0-9]-*.ipynb")
    )
    expected_numbers = [f"{number:03d}" for number in range(1, len(guides) + 1)]
    assert len(guides) == len(notebooks)
    assert guides == notebooks
    assert [slug[:3] for slug in guides] == expected_numbers

    for slug in sorted(notebooks):
        notebook_path = ROOT / "notebooks" / f"{slug}.ipynb"
        guide_path = ROOT / "guides" / "concepts" / f"{slug}.md"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        nbformat.validate(nbformat.from_dict(notebook))
        guide_text = guide_path.read_text(encoding="utf-8")
        notebook_text = notebook_path.read_text(encoding="utf-8")
        assert f"../../notebooks/{slug}.ipynb" in guide_text
        assert f"../guides/concepts/{slug}.md" in notebook_text
        assert notebook["nbformat"] == 4
        assert notebook["nbformat_minor"] >= 5
        assert notebook["cells"]
        cell_ids = [cell.get("id") for cell in notebook["cells"]]
        assert all(
            isinstance(cell_id, str)
            and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", cell_id)
            for cell_id in cell_ids
        ), f"{notebook_path.name} has an invalid or missing cell ID"
        assert len(cell_ids) == len(set(cell_ids)), f"{notebook_path.name} has duplicate cell IDs"
        namespace = {"__name__": "__main__"}
        for cell in notebook["cells"]:
            assert cell["cell_type"] in {"code", "markdown", "raw"}
            assert isinstance(cell["source"], list)
            if cell["cell_type"] == "code":
                source = "".join(cell["source"])
                compile(source, str(notebook_path), "exec")
                exec(source, namespace)  # noqa: S102 - run trusted checked-in lessons
        code_cell_count = sum(cell["cell_type"] == "code" for cell in notebook["cells"])
        assert code_cell_count >= 3, f"{notebook_path.name} needs a multi-step implementation"
        if slug[4:] == "ai":
            assert namespace["predictions"][0]["action"] == "human_review"


def test_ai_lesson_is_a_complete_supervised_learning_workflow() -> None:
    notebook_path = next((ROOT / "notebooks").glob("[0-9][0-9][0-9]-ai.ipynb"))
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    code_cells = [
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]
    assert len(code_cells) >= 7
    complete_lesson = "\n".join(code_cells)
    for required_step in (
        "train_test_split",
        "TfidfVectorizer",
        "LogisticRegression",
        "model.fit",
        "classification_report",
        "confusion_matrix",
        "predict_proba",
        "human_review",
    ):
        assert required_step in complete_lesson


def test_roadmap_matches_numbered_lesson_order() -> None:
    roadmap = (ROOT / "guides" / "ROADMAP.md").read_text(encoding="utf-8")
    roadmap_guides = re.findall(r"\]\(concepts/(\d{3}-[a-z0-9-]+\.md)\)", roadmap)
    expected_guides = sorted(
        path.name
        for path in (ROOT / "guides" / "concepts").glob("[0-9][0-9][0-9]-*.md")
    )
    assert roadmap_guides == expected_guides
