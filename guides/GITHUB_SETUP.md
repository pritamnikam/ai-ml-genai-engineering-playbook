# Publish this playbook on GitHub

## Suggested repository details

- **Name:** `ai-ml-genai-engineering-playbook`
- **Description:** `A hands-on AI/ML and GenAI engineering curriculum with 69 runnable notebooks, concept guides, and a FastAPI hybrid-search reference app.`
- **Visibility:** Public is useful for sharing a portfolio and learning resource; choose private if you want to review the repository before publishing.

The workspace already has Git initialized on `main`, but it has no commits or
remote configured. Create the GitHub repository **empty**: do not initialize it
with a README, license, or `.gitignore`, because those files already exist here.

## Option A: create the repository with GitHub CLI

Install and authenticate with GitHub CLI (`gh auth login`), then run these
commands from the workspace root in PowerShell:

```powershell
gh repo create ai-ml-genai-engineering-playbook --source . --remote origin --public --description "A hands-on AI/ML and GenAI engineering curriculum with 69 runnable notebooks, concept guides, and a FastAPI hybrid-search reference app."
git add .
git status --short
git diff --cached --check
git commit -m "Initial AI and GenAI engineering playbook"
git push -u origin main
```

Use `--private` instead of `--public` if you prefer a private repository.
Review the staged file list before committing. `.venv/`, local `.env*` files
(except `.env.example`), Python caches, and notebook checkpoints are ignored;
`.env.example` contains no credentials.

## Option B: create the repository in a browser

1. On GitHub, choose **New repository**.
2. Enter `ai-ml-genai-engineering-playbook`, add the description above, and
   select public or private visibility.
3. Leave **Add a README**, **Add .gitignore**, and **Choose a license**
   unchecked; the workspace already includes those files.
4. Create the empty repository and copy its HTTPS or SSH URL.
5. From this workspace root in PowerShell, stage, review, commit, and push:

   ```powershell
   git add .
   git status --short
   git diff --cached --check
   git commit -m "Initial AI and GenAI engineering playbook"
   git remote add origin https://github.com/YOUR-USERNAME/ai-ml-genai-engineering-playbook.git
   git push -u origin main
   ```

   Replace `YOUR-USERNAME` and the URL with the repository URL GitHub shows
   you. Use the SSH URL if SSH authentication is configured.

## Before publishing

- Check `git status --short` and `git diff --cached` to confirm only intended
  files are staged.
- Never stage `.env` files containing real credentials, private datasets, or
  generated model weights. If a secret was staged, remove it from the index
  before committing and rotate the credential if it was exposed.
- Confirm the repository visibility is what you intended.
- The GitHub Actions workflow runs tests and Ruff on Python 3.11–3.14. Provider
  calls are opt-in and should not need secrets in CI.

## Start using the playbook effectively

1. **Set a cadence.** Work through one or two concepts per study session rather
   than trying to run all 69 notebooks at once.
2. **Follow the roadmap.** Start with [Python for AI](../notebooks/001-python-for-ai.ipynb)
   and continue in numeric order. Read the matching guide before opening the
   notebook.
3. **Run, predict, change, explain.** Run each notebook top to bottom; before
   changing an input, predict what will happen. Modify an example, rerun it,
   and write a short explanation in your own notes.
4. **Build retrieval foundations before frameworks.** Learn search, embeddings,
   ranking, and RAG before adding LangChain, LangGraph, or a provider API.
   Keep provider calls disabled until you intentionally configure credentials.
5. **Create evidence of learning.** For each track, keep a small project or
   experiment, record its baseline and evaluation, and note limitations—not
   just screenshots of successful outputs.
6. **Finish with the reference app.** Use the hybrid-search API to connect
   FastAPI, PostgreSQL, Qdrant, BM25, reciprocal-rank fusion, and the
   transactional outbox.
7. **Re-run checks when you make changes.** From the repository root:

   ```powershell
   python -m pip install -e ".[dev,notebooks]"
   python -m pytest -q
   python -m ruff check .
   ```

Notebooks are small educational implementations, not production-ready models.
Cloud lessons may incur costs when their optional calls or resources are used;
review provider permissions, pricing, and cleanup before experimenting.
