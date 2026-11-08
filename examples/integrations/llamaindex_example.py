"""Offline LlamaIndex wiring example using mock model components."""

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM


def main() -> None:
    Settings.embed_model = MockEmbedding(embed_dim=8)
    Settings.llm = MockLLM(max_tokens=64)
    documents = [
        Document(
            text="The return window is 30 days.",
            metadata={"source": "returns-policy-v1"},
        ),
        Document(
            text="The support team is available on weekdays.",
            metadata={"source": "support-hours-v1"},
        ),
    ]
    index = VectorStoreIndex.from_documents(documents)
    response = index.as_query_engine().query("What is the return window?")
    print(response)


if __name__ == "__main__":
    main()
