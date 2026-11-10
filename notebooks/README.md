# Notebooks

There are 72 concept notebooks. Open them in numeric order to follow the
recommended sequence, starting with `001-python-for-ai.ipynb`.
They pair with longer guides in `guides/concepts/`. Lessons combine
explanations, staged implementations, runnable examples, and exercises. The
lessons include data preparation and mathematics, supervised and unsupervised
learning, reinforcement learning, recommendation systems, neural networks,
language representations, LLM application patterns, retrieval/RAG workflows,
agent orchestration, and production engineering.
Provider notebooks are offline by default; live calls require an explicit
opt-in, credentials, and the relevant optional SDK.

Install notebook dependencies:

```powershell
python -m pip install -e ".[dev,notebooks]"
```

Then open a notebook in JupyterLab or VS Code, choose the project's Python
kernel, and run cells from top to bottom. The lesson examples are reproducible
demonstrations, not production systems. Start with the
[roadmap](../guides/ROADMAP.md), or open a lesson directly.

To validate notebook structure and execute every code cell:

```powershell
python -m pytest tests/test_notebooks.py
```

Provider examples are intentionally not run by the concept notebooks, so
exploring the core curriculum does not require credentials, network access, or
cloud resources. The applied semantic and hybrid document-search notebooks do
download the `all-MiniLM-L6-v2` model on first use; that model-dependent step
needs internet access, while the notebook tests skip only those tagged cells.
The LangGraph hybrid-search agent also needs the optional `langchain` and
`langgraph` extras; its Ollama answer-generation node is opt-in and requires a
local Ollama server and pulled model.
