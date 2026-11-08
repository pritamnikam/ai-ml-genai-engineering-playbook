# Hybrid-search API

A local reference architecture that wires together FastAPI, PostgreSQL,
Qdrant, BM25, reciprocal-rank fusion (RRF), and a PostgreSQL transactional
outbox. It is an educational example, not a production-ready service.

## Run locally with Compose

From the repository root:

```powershell
docker compose -f examples/hybrid_search_api/compose.yaml up --build
```

PostgreSQL is published on `127.0.0.1:5433` by default to avoid common local
PostgreSQL port conflicts. The API and worker connect to PostgreSQL over the
Compose network on port `5432`; this host mapping does not change their
connection. If host port `5433` is also unavailable, choose another port before
starting Compose:

```powershell
$env:POSTGRES_HOST_PORT = "15432"
docker compose -f examples/hybrid_search_api/compose.yaml up --build
```

In another PowerShell window, use the same host port if connecting to PostgreSQL
directly from your machine. Clear the override afterward if you want to return
to the default:

```powershell
Remove-Item Env:POSTGRES_HOST_PORT
```

Open [http://localhost:8000/docs](http://localhost:8000/docs). Add a document:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/documents `
  -ContentType "application/json" `
  -Body '{"title":"Password reset","content":"Reset a password from account settings."}'
```

Search it:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/search?q=password%20reset"
```

`POST /documents` writes the document and an outbox event in one PostgreSQL
transaction. The worker claims pending events with `FOR UPDATE SKIP LOCKED`,
upserts the vector, and marks the event processed. A worker crash after the
upsert can cause a repeat delivery; Qdrant upsert by the stable document UUID
makes that operation idempotent. A crashed claim can be reclaimed after its
one-minute lease expires.

## Components

- `app/retrieval.py`: small BM25 ranker and RRF; both are covered by unit tests.
- `app/embeddings.py`: deterministic signed-hash vectors solely for exercising
  the data path. These do **not** encode semantic meaning.
- `app/main.py`: typed API, document/outbox transaction, lexical + vector
  retrieval, and RRF response.
- `worker.py`: asynchronous, leased outbox delivery to Qdrant.
- `init.sql`: relational constraints, outbox state, and a PostgreSQL full-text
  search index for further exercises.
- `compose.yaml`: local PostgreSQL, Qdrant, API, and worker services.

## Run API and worker outside containers

Start PostgreSQL and Qdrant using Compose, install the repository package, and
copy `.env.example` to `.env`. Set environment variables in the shell or load
them with a local environment manager; the application does not load `.env`
files implicitly.

```powershell
python -m pip install -e .
python -m uvicorn examples.hybrid_search_api.app.main:app --reload
```

In another terminal:

```powershell
python -m examples.hybrid_search_api.worker
```

## Exercises

1. Replace the demo vectorizer with one real embedding model. Version the model
   and reindex when its output dimension or behavior changes.
2. Add authorization filters to both database and vector retrieval. Never
   expose a vector match without checking access to its source document.
3. Compare BM25, vector search, and RRF using a labeled query set. Track
   Recall@k, MRR or nDCG, and inspect failure cases.
4. Add retry backoff, dead-letter handling, metrics, and an outbox retention
   policy.
5. Add authentication, rate limiting, timeouts, input quotas, and tenant
   isolation before exposing an API beyond localhost.

The Compose password is a local demo value. Do not reuse it outside this
isolated development setup. Compose binds published ports to localhost.
