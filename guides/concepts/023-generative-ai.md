# Generative AI

**Track:** Language models  
**Notebook:** [Open the hands-on lesson](../../notebooks/023-generative-ai.ipynb)

## What it is

Generative AI creates new text, images, audio, code, or other outputs conditioned on a prompt or context.

## Intuition

A design assistant makes a new sketch from a brief; it does not retrieve the one correct sketch from a database.

## How to reason about it

Start from the input and desired output. Identify what the method learns or
stores, what assumptions it makes, and how you will measure whether it works.
For production use, also define data boundaries, latency/cost limits, and a
safe failure path.

## Concept map

```mermaid
flowchart LR
    A[Input or goal] --> B[Generative AI]
    B --> C[Observable output]
    C --> D[Measure and verify]
```

## Small example

Separate a generation request from a factual lookup request.

## Engineering case study

Draft product descriptions from approved product facts and check every generated claim against the source.

## Trade-offs and common mistakes

- Treat a useful analogy or demo as an intuition, not proof of production
  quality.
- Compare against a simple baseline and inspect examples where it fails.
- Avoid data leakage: split evaluation data before fitting or tuning.
- Keep provenance and privacy requirements visible when using external data
  or hosted models.
- Measure the end-to-end user outcome, not only a model score.

## Practice

1. Run the matching notebook and explain each code cell in your own words.
2. Change one input or assumption. Predict the outcome before rerunning.
3. Write one test that would catch a plausible failure in the case study.
4. Record what you would need to validate before deploying the idea.

## Related concepts

Use the [roadmap](../ROADMAP.md) to follow prerequisites and neighboring topics.
The [hybrid-search reference app](../../examples/hybrid_search_api/README.md)
shows how several search and production concepts fit together.
