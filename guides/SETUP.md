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

PostgreSQL is mapped to host port `5433` by default; the containers use the
internal PostgreSQL port `5432`. If `5433` is unavailable too, set a free host
port before starting Compose, for example:

```powershell
$env:POSTGRES_HOST_PORT = "15432"
docker compose -f examples/hybrid_search_api/compose.yaml up --build
```

The Compose stack also starts Qdrant and a local Ollama embedding service,
pulls `nomic-embed-text` on its first start, and runs the indexing worker.
Allow the initial model download to finish, then open
`http://localhost:8000/docs`. Upload a PDF at `POST /documents/pdf`, search it
with `GET /search?q=...`, and follow the returned `source_url#page=N` to view
the evidence page. See the [API guide](../examples/hybrid_search_api/README.md)
for the full workflow, limits, and cleanup instructions.

Compose supplies the service URLs and model configuration to both the API and
worker. Stop the local services with
`docker compose -f examples/hybrid_search_api/compose.yaml down`. This preserves
the named volumes; adding `-v` deletes the database, uploaded PDFs, Qdrant
vectors, and downloaded embedding model. Clear the optional port override with
`Remove-Item Env:POSTGRES_HOST_PORT`.

## Provider credentials

Provider examples are opt-in. Set the relevant provider's environment
variables only when running that example. Never commit API keys, AWS
credentials, access tokens, or real user data. Cloud examples may incur costs;
use least-privilege identities, review the provider's pricing, and clean up
resources after experiments.
