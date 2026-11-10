"""Validate generated lesson links and execute every offline notebook cell."""

import json
import re
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]


def test_every_concept_has_a_guide_and_runnable_notebook() -> None:
    """Keep guide/notebook numbering aligned and each checked-in lesson runnable."""
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
                external_tags = {
                    "requires_model_download",
                    "requires_optional_dependencies",
                }
                if external_tags.intersection(cell.get("metadata", {}).get("tags", [])):
                    continue
                exec(source, namespace)  # noqa: S102 - run trusted checked-in lessons
        code_cell_count = sum(cell["cell_type"] == "code" for cell in notebook["cells"])
        assert code_cell_count >= 3, f"{notebook_path.name} needs a multi-step implementation"
        if slug[4:] == "ai":
            assert namespace["predictions"][0]["action"] == "human_review"
        if slug == "070-semantic-document-search":
            assert namespace["documents"]
            assert len(namespace["documents"]) == len(namespace["doc_sources"])
        if slug == "071-hybrid-document-search":
            assert all(namespace["validate_fact"](fact) for fact in namespace["facts"])
            assert not namespace["validate_fact"](namespace["invalid_fact"])
            assert "chunk-3" in namespace["graph_search"]("Device-D1")
            assert namespace["fused_demo"]
            import faiss
            from sklearn.feature_extraction.text import TfidfVectorizer

            vectorizer = TfidfVectorizer()
            test_vectors = vectorizer.fit_transform(
                [chunk["text"] for chunk in namespace["chunks"]]
            ).toarray().astype("float32")
            faiss.normalize_L2(test_vectors)
            test_index = faiss.IndexFlatIP(test_vectors.shape[1])
            test_index.add(test_vectors)

            class OfflineEmbedding:
                """Use deterministic local vectors to test fusion without model downloads."""

                def __init__(self, vectorizer):
                    self.vectorizer = vectorizer

                def encode(self, texts, convert_to_numpy=True):
                    return self.vectorizer.transform(texts).toarray().astype("float32")

            namespace.update(
                {
                    "embedding_model": OfflineEmbedding(vectorizer),
                    "vector_index": test_index,
                    "faiss": faiss,
                }
            )
            search_results = namespace["hybrid_search"](
                "Which security advisory affects the firmware on Device-D1?",
                category="ProductDocuments",
                seed_entity="Device-D1",
                top_k=5,
            )
            assert any(result["id"] == "chunk-3" for result in search_results)
            assert all(
                result["category"] in {"DeviceDocs", "SecurityDocs"}
                for result in search_results
            )
            graph_match = next(result for result in search_results if result["id"] == "chunk-3")
            assert "knowledge_graph" in graph_match["matched_by"]
        if slug == "072-hybrid-document-search-agent":
            assert "StateGraph" in notebook_text
            assert "draw_mermaid()" in notebook_text
            assert "ChatOllama" in notebook_text

            class FakeVector:
                """Stand in for an encoded query in the deterministic DAG test."""

                def astype(self, _dtype):
                    return self

            class FakeEmbeddingModel:
                """Avoid network access while testing the semantic node wiring."""

                def encode(self, _texts, **_kwargs):
                    return FakeVector()

            class FakeVectorIndex:
                """Return a known candidate ordering through the FAISS-style interface."""

                def search(self, _query_vector, limit):
                    order = [2, 1, 0, 3, 4, 5][:limit]
                    return [[1.0] * len(order)], [order]

            namespace.update(
                {
                    "embedding_model": FakeEmbeddingModel(),
                    "vector_index": FakeVectorIndex(),
                    "vector_document_ids": [chunk["id"] for chunk in namespace["chunks"]],
                }
            )
            state = {
                "query": "Which advisory affects firmware on Device-D1?",
                "category": "ProductDocuments",
                "seed_entity": "Device-D1",
                "top_k": 5,
                "generate_answer": False,
            }
            for node in (
                namespace["validate_request_node"],
                namespace["taxonomy_filter_node"],
                namespace["lexical_retrieval_node"],
                namespace["semantic_retrieval_node"],
                namespace["graph_retrieval_node"],
                namespace["fuse_and_resolve_node"],
            ):
                state.update(node(state))
            state.update(namespace["evidence_only_node"](state))
            evidence_ids = {item["id"] for item in state["evidence"]}
            assert "chunk-3" in evidence_ids
            assert all(
                item["category"] in {"DeviceDocs", "SecurityDocs"}
                for item in state["evidence"]
            )
            advisory = next(item for item in state["evidence"] if item["id"] == "chunk-3")
            assert advisory["citation"] == "security-bulletin.pdf#page=3"
            assert "knowledge_graph" in advisory["matched_by"]


def test_ai_lesson_is_a_complete_supervised_learning_workflow() -> None:
    """Guard the AI notebook's training, held-out evaluation, and review stages."""
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
    """Ensure every numbered guide appears once in the published roadmap order."""
    roadmap = (ROOT / "guides" / "ROADMAP.md").read_text(encoding="utf-8")
    roadmap_guides = re.findall(r"\]\(concepts/(\d{3}-[a-z0-9-]+\.md)\)", roadmap)
    expected_guides = sorted(
        path.name
        for path in (ROOT / "guides" / "concepts").glob("[0-9][0-9][0-9]-*.md")
    )
    assert roadmap_guides == expected_guides
