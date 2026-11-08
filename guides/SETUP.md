# Environment setup

## Create an environment

From the repository root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,notebooks]"
```

This installs the notebook dependencies, including NumPy, scikit-learn,
JupyterLab, FastAPI test support, and Qdrant's local in-memory client. On
macOS/Linux, activate with `source .venv/bin/activate`.

## Run notebooks

```powershell
jupyter lab
```

Alternatively, open `notebooks/` in VS Code and select the `.venv` interpreter
as the notebook kernel. Start with `notebooks/001-python-for-ai.ipynb`; use
`guides/ROADMAP.md` to choose a learning order.

## Run the reference service

```powershell
docker compose -f examples/hybrid_search_api/compose.yaml up --build
```

Open `http://localhost:8000/docs` for the interactive API documentation.
Create a document using `POST /documents`, then search using `GET /search?q=...`.
Run the indexing worker in another terminal:

```powershell
python -m examples.hybrid_search_api.worker
```

The worker and API require the same environment variables. The application
does not automatically load `.env` files; use your shell or a local environment
manager when running outside Compose. Stop the local services with
`docker compose -f examples/hybrid_search_api/compose.yaml down`.

## Provider credentials

Provider examples are opt-in. Set the relevant provider's environment
variables only when running that example. Never commit API keys, AWS
credentials, access tokens, or real user data. Cloud examples may incur costs;
use least-privilege identities, review the provider's pricing, and clean up
resources after experiments.
