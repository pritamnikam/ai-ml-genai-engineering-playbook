# Semantic document search with FAISS

**Track:** Applied search

**Notebook:** [Open the runnable lesson](../../notebooks/070-semantic-document-search.ipynb)

## What it does

Semantic document search retrieves passages by meaning rather than requiring
the query and passage to share the same words. This lesson reads PDF, DOCX,
and text files, splits them into manageable chunks, embeds each chunk with a
Sentence Transformers model, and indexes normalized vectors with FAISS.

The notebook uses `all-MiniLM-L6-v2`, a compact text embedding model. Its first
run downloads the model from Hugging Face; after that, the files are cached
locally. Install the project notebook extra with
`python -m pip install -e ".[notebooks]"` from the repository root.

## How retrieval works

1. **Extract:** Parse supported files into text. PDF page text is extracted
   with `pypdf`; DOCX paragraphs use `python-docx`.
2. **Chunk:** Split long text into smaller units that fit the embedding model
   and can be returned as focused evidence.
3. **Embed:** Map chunks and the query to vectors in the same model space.
4. **Normalize:** Unit-normalize vectors. Then the inner product between a
   query and document vector equals cosine similarity.
5. **Index and search:** FAISS `IndexFlatIP` performs exact inner-product
   search and returns the nearest chunk IDs and similarity scores.
6. **Ground the result:** Resolve each hit back to its source document and
   show a text preview.

```mermaid
flowchart LR
    F[PDF DOCX TXT files] --> E[Extract text]
    E --> C[Create text chunks]
    C --> M[Sentence Transformer]
    M --> V[Normalize vectors]
    V --> I[FAISS inner product index]
    Q[User query] --> M
    I --> R[Top similar chunks]
    R --> S[Source and text preview]
```

## Why use FAISS here?

FAISS provides efficient vector indexing and nearest-neighbor search. The
notebook starts with `IndexFlatIP`, which is exact and easy to reason about.
For a small study corpus, it is a useful baseline. Larger datasets may need an
approximate index, a managed vector database, filtering, persistence, and
reindexing/versioning practices.

The model's embedding quality and FAISS's search speed are separate concerns:
FAISS finds nearest vectors; the model determines whether those vectors
represent useful semantic similarity.

## Engineering example

Ask a question using different wording from the source, such as searching for
"how computers learn patterns" when a passage discusses "machine learning."
Semantic retrieval can surface that passage even when exact token overlap is
limited. The notebook also searches the local `documents/` examples and shows
the matching file and chunk.

## Trade-offs and limitations

- Semantic similarity is not proof that a passage answers a question. Inspect
  the retrieved text and tune thresholds with representative queries.
- Embedding models have finite context lengths. Chunking that is too large
  dilutes relevance; chunking that is too small loses context.
- This example's flat FAISS index is in memory and exact. It must be rebuilt
  after restart and may become costly for large corpora.
- The notebook preserves the source filename, but its simple chunking does not
  guarantee precise page citations. Use page-aware chunk metadata for citation
  requirements.
- Image-only PDFs need OCR; the text extractor cannot recover text that is
  only present in pixels.
- A first model run needs network access and enough disk space for the model
  cache. Do not send sensitive documents to a hosted model without an approved
  data-handling design.

## Practice

1. Run the notebook from top to bottom after installing `.[notebooks]`.
2. Compare a keyword query with a paraphrased query and inspect the ranked
   passages.
3. Change the chunk size and evaluate whether useful context is gained or
   lost.
4. Keep a small set of query-to-relevant-document examples and measure
   recall@k before changing models or index settings.
5. Continue with [hybrid document search](071-hybrid-document-search.md) to
   combine semantic retrieval with lexical ranking, taxonomy filters, and
   knowledge-graph evidence.
