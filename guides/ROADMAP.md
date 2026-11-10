# Learning roadmap

Each item links to a standalone guide; its hands-on companion has the same
filename under `notebooks/`. Follow the sequence to build prerequisites
before moving from foundational methods to deployed AI systems.

## 1. Programming and mathematical foundations

1. [Python for AI](concepts/001-python-for-ai.md)
2. [Data preparation for machine learning](concepts/002-data-preparation.md)
3. [Linear algebra for machine learning](concepts/003-linear-algebra.md)
4. [Probability and statistics for AI](concepts/004-probability-statistics.md)
5. [Artificial intelligence](concepts/005-ai.md)
6. [Heuristic search](concepts/006-heuristic-search.md)
7. [Machine learning](concepts/007-ml.md)

## 2. Core machine learning

8. [Machine-learning evaluation](concepts/008-ml-evaluation.md)
9. [Supervised learning](concepts/009-supervised-learning.md)
10. [Classical machine-learning models](concepts/010-classical-models.md)
11. [Unsupervised learning](concepts/011-unsupervised-learning.md)
12. [Semi-supervised learning](concepts/012-semi-supervised-learning.md)
13. [Reinforcement learning](concepts/013-reinforcement-learning.md)
14. [Recommendation systems](concepts/014-recommendation-systems.md)
15. [Feature engineering](concepts/015-feature-engineering.md)
16. [Vectorization](concepts/016-vectorization.md)

## 3. Neural networks and deep learning

17. [Neural networks](concepts/017-neural-networks.md)
18. [Backpropagation and gradient descent](concepts/018-backpropagation.md)
19. [Deep learning](concepts/019-deep-learning.md)
20. [Convolutional neural networks](concepts/020-cnn.md)
21. [Recurrent neural networks](concepts/021-rnn.md)
22. [Long short-term memory](concepts/022-lstm.md)
23. [Generative AI](concepts/023-generative-ai.md)
24. [Generative models: VAE, GAN, and diffusion](concepts/024-generative-models.md)

## 4. Natural language processing and representations

25. [Text preprocessing and tokenization](concepts/025-text-preprocessing.md)
26. [Bag-of-words representations](concepts/026-bag-of-words.md)
27. [Term frequency (TF)](concepts/027-tf.md)
28. [Inverse document frequency (IDF)](concepts/028-idf.md)
29. [TF-IDF](concepts/029-tf-idf.md)
30. [Word2Vec](concepts/030-word2vec.md)
31. [Embeddings](concepts/031-embeddings.md)

## 5. Transformers and language-model applications

32. [Attention mechanisms](concepts/032-attention.md)
33. [Transformers](concepts/033-transformers.md)
34. [BERT](concepts/034-bert.md)
35. [GPT](concepts/035-gpt.md)
36. [Large language models](concepts/036-llm.md)
37. [Prompt engineering](concepts/037-prompt-engineering.md)
38. [LLM inference and decoding](concepts/038-llm-inference.md)
39. [Fine-tuning and parameter-efficient adaptation](concepts/039-fine-tuning.md)
40. [Multimodal AI](concepts/040-multimodal-ai.md)
41. [LLM application evaluation](concepts/041-llm-evaluation.md)
42. [Responsible and safe AI](concepts/042-responsible-ai.md)

## 6. Search, retrieval, and knowledge

43. [Full-text search](concepts/043-full-text-search.md)
44. [BM25](concepts/044-bm25.md)
45. [Semantic search](concepts/045-semantic-search.md)
46. [Reciprocal-rank fusion](concepts/046-rrf.md)
47. [Retrieval-augmented generation](concepts/047-rag.md)
48. [Taxonomy, ontology, and knowledge graphs](concepts/048-knowledge-graphs.md)
49. [GraphRAG](concepts/049-graphrag.md)

## 7. Agents and orchestration frameworks

50. [Agents](concepts/050-agents.md)
51. [LLM tool calling](concepts/051-tool-calling.md)
52. [The agent loop](concepts/052-agent-loop.md)
53. [Multi-agent systems](concepts/053-multi-agent.md)
54. [LangChain](concepts/054-langchain.md)
55. [LangGraph](concepts/055-langgraph.md)
56. [LangSmith](concepts/056-langsmith.md)
57. [LlamaIndex](concepts/057-llamaindex.md)

## 8. Production systems and integrations

58. [FastAPI](concepts/058-fastapi.md)
59. [PostgreSQL](concepts/059-postgresql.md)
60. [Qdrant](concepts/060-qdrant.md)
61. [PostgreSQL transactional outbox](concepts/061-transactional-outbox.md)
62. [MLOps and model deployment lifecycle](concepts/062-mlops.md)
63. [Ollama](concepts/063-ollama.md)
64. [Docker Model Runner](concepts/064-docker-model-runner.md)
65. [OpenAI](concepts/065-openai.md)
66. [Gemini](concepts/066-gemini.md)
67. [Anthropic](concepts/067-anthropic.md)
68. [Amazon SageMaker](concepts/068-amazon-sagemaker.md)
69. [Amazon Bedrock](concepts/069-amazon-bedrock.md)

## 9. Applied document search

70. [Semantic document search with FAISS](concepts/070-semantic-document-search.md)
71. [Hybrid document search with taxonomy, ontology, and knowledge graphs](concepts/071-hybrid-document-search.md)

## Suggested project sequence

1. Prepare a small labeled dataset, establish a baseline, and compare
   supervised and unsupervised approaches using a held-out evaluation set.
2. Build a content-based and collaborative-filtering recommender; inspect
   coverage, cold starts, and popularity bias.
3. Build lexical and semantic search, combine results with reciprocal-rank
   fusion, and measure retrieval quality on representative queries.
4. Add grounded answers with citations, then evaluate faithfulness, safety,
   latency, and cost against a versioned test set.
5. Build the hybrid-search reference app and test retries, idempotency,
   authorization, monitoring, and rollback behavior.

For every project, define data boundaries, cost limits, failure behavior,
and a human escalation path before exposing it to users.

## Scope boundaries

This curriculum is a practical core, not an exhaustive catalog. Advanced
electives include time-series forecasting, causal inference, Bayesian
modeling, graph neural networks, distributed training, and specialized
reinforcement-learning algorithms. Add them after the core when they match
your application domain.
