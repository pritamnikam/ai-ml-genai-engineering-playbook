"""Generate one focused guide and an offline-first notebook for each concept."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from notebook_lessons import LESSONS, LessonStep, provider_lesson

ROOT = Path(__file__).resolve().parents[1]

# slug, title, track, plain-English idea, analogy, example, case study, code
TOPICS = [
    ("python-for-ai", "Python for AI", "Foundations",
     "Python supplies the data structures, numerical libraries, and APIs used to turn an AI idea into an experiment.",
     "It is the workbench: libraries are tools, data is the material, and tests are the measuring instruments.",
     "Represent a small set of measurements as a list, then calculate its mean.",
     "A data engineer validates and summarizes incoming sensor readings before training a model.",
     "readings = [18.2, 19.1, 17.7, 20.0]\nmean = sum(readings) / len(readings)\nprint(f\"mean={mean:.2f}\")"),
    ("ai", "Artificial intelligence", "Foundations",
     "AI is the broad goal of making a system perform tasks that normally require perception, reasoning, language, or decisions.",
     "A thermostat is intelligent in a narrow sense: it observes a signal, applies a policy, and chooses an action.",
     "Build a complete text-classification workflow: prepare labeled tickets, split data, train a TF-IDF + logistic-regression model, evaluate held-out results, and score new tickets.",
     "Compare a hand-authored keyword rule with a learned classifier for detecting urgent tickets; inspect missed urgent cases and keep a human in the loop.",
     "from sklearn.feature_extraction.text import TfidfVectorizer\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.pipeline import make_pipeline\n\nclassifier = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), LogisticRegression(max_iter=1000))\nclassifier.fit(train_texts, train_labels)\nprint(classifier.predict([\"Smoke is coming from my charger\"]))"),
    ("ml", "Machine learning", "Foundations",
     "Machine learning fits a model from examples so it can make predictions on new inputs.",
     "Instead of writing every rule for sorting fruit, show the model labeled examples and check what it learned.",
     "Split examples into training and test sets; measure accuracy only on examples held out from fitting.",
     "Estimate equipment failure from historical sensor readings without leaking future labels into training.",
     "examples = [(1, \"low\"), (2, \"low\"), (8, \"high\"), (9, \"high\")]\ntrain = examples[:3]\ntest = examples[3:]\nprediction = \"high\" if test[0][0] >= 5 else \"low\"\nprint({\"prediction\": prediction, \"actual\": test[0][1]})"),
    ("cnn", "Convolutional neural networks", "Neural networks",
     "A CNN applies small shared filters across an image to detect local patterns such as edges and textures.",
     "A stencil scans every part of a picture with the same pattern detector.",
     "A 2-by-2 edge-like filter produces a response at each valid image location.",
     "Classify manufacturing images while checking that the model attends to the defect, not the background.",
     "image = [[0, 0, 0], [0, 1, 1], [0, 1, 1]]\nkernel = [[1, -1], [1, -1]]\nresponses = []\nfor row in range(2):\n    responses.append([sum(image[row + i][col + j] * kernel[i][j]\n                          for i in range(2) for j in range(2)) for col in range(2)])\nprint(responses)"),
    ("rnn", "Recurrent neural networks", "Neural networks",
     "An RNN processes an ordered sequence one step at a time and carries a hidden state forward.",
     "It reads a sentence while keeping a small notepad of what it has seen so far.",
     "Accumulate a state over a sequence to illustrate dependence on earlier inputs.",
     "Forecast a machine's next reading using the recent history rather than treating each reading independently.",
     "sequence = [2, 3, 5]\nstate = 0\nfor value in sequence:\n    state = 0.5 * state + value\n    print(state)"),
    ("tf-idf", "TF-IDF", "Search",
     "TF-IDF weights a term by its frequency in one document and discounts terms common across the collection.",
     "A word earns attention when it is repeated in this report but is uncommon in the whole library.",
     "Calculate smoothed inverse document frequency for a term found in one of three documents.",
     "Rank support articles for a query while reducing the influence of generic words such as “account.”",
     "import math\nN, document_frequency = 3, 1\nidf = math.log((1 + N) / (1 + document_frequency)) + 1\nterm_frequency = 2\nprint(round(term_frequency * idf, 3))"),
    ("tf", "Term frequency (TF)", "Search",
     "Term frequency measures how often a term occurs in a document, sometimes normalized by document length.",
     "Count how many times a keyword appears in one report before comparing it with other reports.",
     "Compute raw and length-normalized frequency for one term.",
     "Compare mentions of a product code across a short note and a long manual without rewarding verbosity alone.",
     "tokens = [\"reset\", \"password\", \"reset\", \"account\"]\nterm = \"reset\"\nraw_tf = tokens.count(term)\nnormalized_tf = raw_tf / len(tokens)\nprint({\"raw_tf\": raw_tf, \"normalized_tf\": normalized_tf})"),
    ("idf", "Inverse document frequency (IDF)", "Search",
     "Inverse document frequency reduces the weight of terms that appear in many documents and increases the weight of rarer terms.",
     "A detail that distinguishes one folder matters more than a label printed on every folder.",
     "Calculate smoothed IDF for both a common and a rare term.",
     "Reduce generic words in a help center query while preserving a rare diagnostic code that identifies the right article.",
     "import math\ndocument_count = 10\nfrequencies = {\"account\": 9, \"E1042\": 1}\nidf = {term: math.log((1 + document_count) / (1 + df)) + 1 for term, df in frequencies.items()}\nprint({term: round(weight, 2) for term, weight in idf.items()})"),
    ("lstm", "Long short-term memory", "Neural networks",
     "An LSTM is a gated RNN designed to preserve or forget information over longer sequences.",
     "A gated notebook chooses which facts to keep, erase, or expose at every step.",
     "Use a sigmoid forget gate to scale an old memory value.",
     "A sequence model must retain an early warning signal through many ordinary sensor readings.",
     "import math\nsigmoid = lambda x: 1 / (1 + math.exp(-x))\nold_memory, gate_logit = 0.8, 1.0\nnew_memory = sigmoid(gate_logit) * old_memory\nprint(round(new_memory, 3))"),
    ("bert", "BERT", "Language models",
     "BERT is an encoder Transformer pretrained to build context-aware representations, classically using masked-token prediction.",
     "It reads both the left and right sides of a blank to infer the missing word.",
     "Mask one word in a sentence and identify which context on each side can inform it.",
     "Classify customer feedback with context-sensitive representations and a task-specific fine-tuning head.",
     "sentence = \"The battery lasts all day\"\nmasked = sentence.replace(\"battery\", \"[MASK]\")\nprint(masked)\nprint(\"Use left and right context to predict the masked token.\")"),
    ("transformers", "Transformers", "Language models",
     "Transformers use attention to let sequence positions combine information directly, with positional information added separately.",
     "Each word can consult a relevance-weighted group discussion rather than passing a message down a long chain.",
     "Compute a tiny scaled dot-product attention result for one query and two keys.",
     "Compare a long-range dependency handled by attention with the same dependency in a recurrent model.",
     "import math\nquery, keys, values = [1, 0], [[1, 0], [0, 1]], [[10, 0], [0, 10]]\nscores = [sum(a*b for a, b in zip(query, key)) / math.sqrt(2) for key in keys]\nweights = [math.exp(score) for score in scores]\nweights = [weight / sum(weights) for weight in weights]\nprint([round(sum(w * value[i] for w, value in zip(weights, values)), 2) for i in range(2)])"),
    ("vectorization", "Vectorization", "Foundations",
     "Vectorization maps symbolic inputs such as words into numeric features a mathematical model can process.",
     "It turns sentences into rows of numbers, like encoding ingredients as a shopping checklist.",
     "Build a tiny bag-of-words vector using a fixed vocabulary.",
     "Prepare a text classifier's input features and keep the vocabulary learned only from training data.",
     "vocabulary = {\"ai\": 0, \"search\": 1, \"model\": 2}\ntext = \"AI model search model\".lower().split()\nvector = [text.count(word) for word in vocabulary]\nprint(vector)"),
    ("gpt", "GPT", "Language models",
     "GPT-style models are decoder-only Transformers trained to predict the next token, then adapted for useful generation.",
     "It writes one word at a time, using everything already written as context.",
     "Show how a next-token choice extends a prompt by one token.",
     "Generate a draft answer, then require retrieval, validation, and human review where correctness matters.",
     "tokens = [\"A\", \"useful\", \"model\"]\nnext_token = \" predicts\"\nprint(\"\".join(tokens) + next_token)"),
    ("generative-ai", "Generative AI", "Language models",
     "Generative AI creates new text, images, audio, code, or other outputs conditioned on a prompt or context.",
     "A design assistant makes a new sketch from a brief; it does not retrieve the one correct sketch from a database.",
     "Separate a generation request from a factual lookup request.",
     "Draft product descriptions from approved product facts and check every generated claim against the source.",
     "approved_facts = {\"material\": \"recycled aluminum\", \"warranty_years\": 2}\ndraft = f\"A {approved_facts['material']} product with a {approved_facts['warranty_years']}-year warranty.\"\nprint(draft)"),
    ("llm", "Large language models", "Language models",
     "An LLM is a language model with enough learned parameters and data to handle many language tasks through prompting.",
     "A broad, compressed library of language patterns that still needs a task, context, and verification.",
     "Estimate prompt size using a rough whitespace token count and enforce a context budget.",
     "Design a support assistant with a finite context window, bounded output, and a fallback for uncertain answers.",
     "prompt = \"Summarize the incident and list two next steps.\"\nrough_tokens = len(prompt.split())\ncontext_budget = 100\nprint({\"rough_tokens\": rough_tokens, \"fits\": rough_tokens < context_budget})"),
    ("agents", "Agents", "Agents",
     "An agent combines a model with a bounded set of tools and state to pursue a goal over multiple steps.",
     "A careful intern can consult approved tools, but needs a clear task and limits on what they may change.",
     "Route a read-only calculator request to a named, allowlisted tool.",
     "An operations agent explains a failed job using logs but cannot restart production without approval.",
     "tools = {\"add\": lambda a, b: a + b}\nrequest = {\"tool\": \"add\", \"args\": {\"a\": 4, \"b\": 5}}\nif request[\"tool\"] not in tools:\n    raise ValueError(\"Tool is not allowlisted\")\nprint(tools[request[\"tool\"]](**request[\"args\"]))"),
    ("agent-loop", "The agent loop", "Agents",
     "The agent loop repeatedly observes context, chooses an action, receives a result, and stops at a limit or completion.",
     "A technician checks a gauge, takes one permitted action, checks the new reading, and stops when the job is done.",
     "Run a deterministic observe-act loop with a hard step limit.",
     "A troubleshooting assistant gathers one diagnostic signal per step and hands off rather than looping forever.",
     "observations = [\"temperature high\", \"cooling restored\", \"done\"]\nfor step, observation in enumerate(observations, start=1):\n    print(step, observation)\n    if observation == \"done\":\n        break\nelse:\n    raise RuntimeError(\"Step limit reached\")"),
    ("multi-agent", "Multi-agent systems", "Agents",
     "A multi-agent system assigns different scoped responsibilities to multiple cooperating agents or services.",
     "A small project team separates research, drafting, and review instead of giving every person unrestricted authority.",
     "Pass a report from a researcher to a reviewer with an explicit input/output contract.",
     "A research assistant gathers sources, a writer drafts a summary, and a verifier flags unsupported claims.",
     "facts = [\"source A supports claim 1\", \"source B supports claim 2\"]\ndraft = \"; \".join(facts)\nreview = {\"claims\": len(facts), \"needs_citations\": True}\nprint({\"draft\": draft, \"review\": review})"),
    ("full-text-search", "Full-text search", "Search",
     "Full-text search tokenizes text, applies language-aware processing, and matches query terms against an inverted index.",
     "A book index maps each word to the pages on which it appears.",
     "Match query terms against a tiny set of documents using token sets.",
     "Search product manuals for exact error codes and domain terms before adding more advanced retrieval.",
     "documents = {\"d1\": \"reset the account password\", \"d2\": \"account recovery guide\"}\nquery = {\"account\", \"reset\"}\nprint([key for key, text in documents.items() if query <= set(text.split())])"),
    ("rag", "Retrieval-augmented generation", "Search",
     "RAG retrieves relevant evidence at answer time and gives that evidence to a generator to ground its response.",
     "An open-book exam: first find the relevant pages, then write an answer that points back to them.",
     "Retrieve a matching fact and construct an answer that carries its source identifier.",
     "Answer policy questions from versioned manuals, cite passages, and abstain if evidence is missing.",
     "evidence = {\"doc-17\": \"The return window is 30 days.\"}\nquestion = \"How long is the return window?\"\nsource, passage = next(iter(evidence.items()))\nanswer = f\"{passage} [source: {source}]\" if \"return\" in question else \"I do not know.\"\nprint(answer)"),
    ("knowledge-graphs", "Knowledge graphs", "Search",
     "A knowledge graph represents entities as nodes and typed relationships as edges.",
     "A map labels places and the roads connecting them; the connection itself has meaning.",
     "Represent two entities and traverse a typed edge.",
     "Trace which product versions, components, and advisories are connected during an incident review.",
     "edges = [(\"Battery-7\", \"used_in\", \"Device-A\"), (\"Device-A\", \"affected_by\", \"Advisory-2\")]\nprint([target for source, relation, target in edges if source == \"Device-A\" and relation == \"affected_by\"])"),
    ("heuristic-search", "Heuristic search", "Search",
     "Heuristic search prioritizes promising paths using an estimate of remaining cost; A* combines that estimate with cost so far.",
     "On a road map, straight-line distance helps choose which route to explore first without claiming it is the road distance.",
     "Use a small admissible heuristic to prioritize routes in a toy graph.",
     "Plan a low-cost route through a warehouse while ensuring the heuristic does not overestimate remaining travel.",
     "frontier = [(0 + 2, \"A\"), (1 + 1, \"B\")]\nfrontier.sort()\nprint(\"expand next:\", frontier[0][1])"),
    ("graphrag", "GraphRAG", "Search",
     "GraphRAG uses entity relationships and graph structure alongside text retrieval to answer questions spanning connected facts.",
     "Instead of searching only for paragraphs, follow a map of people, events, and their relationships.",
     "Expand a seed entity to its one-hop neighbors before selecting evidence.",
     "Summarize a project history by finding linked teams, decisions, and incidents across many documents.",
     "graph = {\"Team A\": [\"Project X\"], \"Project X\": [\"Decision 3\", \"Incident 8\"]}\nseed = \"Team A\"\nfirst_hop = graph.get(seed, [])\nsecond_hop = [node for item in first_hop for node in graph.get(item, [])]\nprint(first_hop + second_hop)"),
    ("embeddings", "Embeddings", "Search",
     "An embedding is a learned numeric representation intended to place similar items near one another in vector space.",
     "A map coordinate is useful when nearby places tend to share a purpose; embedding coordinates similarly encode learned relationships.",
     "Compare two short vectors with cosine similarity.",
     "Embed support passages and queries using the same model and version, then monitor retrieval quality after model changes.",
     "import math\na, b = [1, 0], [0.8, 0.2]\ncosine = sum(x*y for x, y in zip(a, b)) / (math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b)))\nprint(round(cosine, 3))"),
    ("semantic-search", "Semantic search", "Search",
     "Semantic search retrieves by similarity of meaning, often through embeddings, rather than only exact token overlap.",
     "A librarian can find a “car” book when asked for “automobile,” even if the exact word differs.",
     "Rank candidate vectors by cosine similarity to a query vector.",
     "Search paraphrased questions against product help content and evaluate with real user-language queries.",
     "query = [1.0, 0.0]\ncandidates = {\"car\": [0.9, 0.1], \"recipe\": [0.0, 1.0]}\nscores = {name: sum(a*b for a, b in zip(query, vector)) for name, vector in candidates.items()}\nprint(sorted(scores, key=scores.get, reverse=True))"),
    ("bm25", "BM25", "Search",
     "BM25 is a probabilistic lexical ranking function that accounts for term frequency, rarity, and document length.",
     "A long document should not win merely because it repeats a query word many times.",
     "Score documents with a compact BM25 implementation and compare a short and long passage.",
     "Retrieve exact terminology and identifiers in manuals where vector similarity can miss a critical literal match.",
     "import math\nN, df, k1, b, avgdl = 3, 1, 1.5, 0.75, 4\nidf = math.log(1 + (N - df + 0.5) / (df + 0.5))\ntf, dl = 2, 4\nscore = idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))\nprint(round(score, 3))"),
    ("rrf", "Reciprocal-rank fusion", "Search",
     "RRF combines ranked result lists using reciprocal rank, so systems with different score scales can contribute fairly.",
     "A judge combines where each candidate placed on several independent leaderboards, not the raw points on each.",
     "Fuse a lexical ranking and a semantic ranking while counting each document once per list.",
     "Blend BM25 and vector search for a mixed query containing both a part number and a natural-language description.",
     "rankings = [[\"part-7\", \"part-8\"], [\"part-8\", \"part-9\"]]\nk = 60\nscores = {}\nfor ranking in rankings:\n    for rank, item in enumerate(ranking, start=1):\n        scores[item] = scores.get(item, 0) + 1 / (k + rank)\nprint(sorted(scores.items(), key=lambda pair: (-pair[1], pair[0])))"),
    ("langchain", "LangChain", "Frameworks",
     "LangChain provides composable integrations and runnable abstractions for building model-powered applications.",
     "It is a box of compatible adapters and connectors; the application still owns its contracts and failure behavior.",
     "Compose retrieval, prompt formatting, and a model call as explicit stages.",
     "Build a small FAQ chain, then test retrieval and model output separately rather than hiding them in one opaque call.",
     "def retrieve(question):\n    return [\"Reset a password from account settings.\"] if \"password\" in question else []\ndef format_context(question, docs):\n    return f\"Question: {question}\\nEvidence: {' '.join(docs)}\"\nprint(format_context(\"Reset password?\", retrieve(\"Reset password?\")))"),
    ("langgraph", "LangGraph", "Frameworks",
     "LangGraph models an agent or workflow as state transitions between named nodes, with explicit edges and stop conditions.",
     "A flowchart with typed shared state makes branching, retries, and human approval visible.",
     "Execute a tiny state transition and stop at an explicit terminal state.",
     "Pause an assistant before a side effect, request human approval, then resume from saved state.",
     "state = {\"approved\": False, \"action\": \"send_email\"}\nif state[\"approved\"]:\n    state[\"status\"] = \"sent\"\nelse:\n    state[\"status\"] = \"awaiting_human_approval\"\nprint(state[\"status\"])"),
    ("langsmith", "LangSmith", "Frameworks",
     "LangSmith supports tracing, dataset-based evaluation, and monitoring of LLM application runs.",
     "A flight recorder and test lab let an engineer inspect each component of a model workflow.",
     "Score a predicted response against an expected answer with a simple exact-match check.",
     "Trace retrieval and generation separately to find whether a wrong answer came from search, context, or the model.",
     "expected, predicted = \"30 days\", \"30 days\"\nscore = int(expected == predicted)\nprint({\"exact_match\": score})"),
    ("llamaindex", "LlamaIndex", "Frameworks",
     "LlamaIndex provides data connectors and indexing/query abstractions to organize private data for LLM applications.",
     "It is an indexing desk that turns a pile of documents into a structured, searchable reference collection.",
     "Create a tiny document list and retrieve the item with the matching topic.",
     "Ingest versioned internal policy documents, keep source metadata, and evaluate which chunks answer representative queries.",
     "documents = [{\"text\": \"Vacation allowance is 20 days\", \"source\": \"policy-v2\"}]\nquery = \"vacation allowance\"\nhits = [item for item in documents if all(term in item[\"text\"].lower() for term in query.split())]\nprint(hits)"),
    ("ollama", "Ollama", "Integrations",
     "Ollama runs supported open models locally and exposes a local API for experimentation.",
     "A private workshop hosts a model on your machine, trading some speed and capability for local control.",
     "Inspect the local endpoint pattern without requiring a downloaded model.",
     "Prototype prompt behavior offline, but still measure hardware needs and validate model licenses before deployment.",
     "endpoint = \"http://localhost:11434/api/chat\"\npayload = {\"model\": \"your-local-model\", \"messages\": [{\"role\": \"user\", \"content\": \"Explain BM25\"}]}\nprint(endpoint, payload[\"model\"])"),
    ("openai", "OpenAI", "Integrations",
     "The OpenAI API provides hosted models and embeddings through authenticated SDK or HTTP requests.",
     "A managed specialist is available over a network API; you must account for latency, cost, data handling, and outages.",
     "Read credentials from the environment and make a provider call only when explicitly configured.",
     "Use a hosted model for a grounded support answer, record model/version metadata, and review data-retention requirements.",
     "import os\nconfigured = bool(os.getenv(\"OPENAI_API_KEY\"))\nprint(\"Credentials configured; follow examples/integrations/model_providers.py\" if configured else \"Set OPENAI_API_KEY to run the optional provider example.\")"),
    ("gemini", "Gemini", "Integrations",
     "Gemini is Google's model family and API; its models and interfaces can support text, image, audio, and other tasks.",
     "A multimodal specialist can inspect several kinds of input, but each modality still needs task-specific evaluation.",
     "Check for an API key before trying a provider request.",
     "Extract structured fields from approved documents and validate the output against a schema.",
     "import os\nprint(\"GEMINI_API_KEY configured\" if os.getenv(\"GEMINI_API_KEY\") else \"Set GEMINI_API_KEY for the optional Gemini example.\")"),
    ("anthropic", "Anthropic", "Integrations",
     "Anthropic provides hosted Claude models through an API and SDK, with model-specific features and constraints.",
     "A capable analyst still needs a clear brief, source material, and a verification checklist.",
     "Keep the provider key outside code and inspect the opt-in integration example.",
     "Summarize retrieved evidence with explicit citations and evaluate unsupported-claim rates.",
     "import os\nprint(\"ANTHROPIC_API_KEY configured\" if os.getenv(\"ANTHROPIC_API_KEY\") else \"Set ANTHROPIC_API_KEY for the optional Anthropic example.\")"),
    ("docker-model-runner", "Docker Model Runner", "Integrations",
     "Docker Model Runner runs supported models with Docker Desktop and offers a local OpenAI-compatible endpoint.",
     "A local appliance exposes a familiar API while Docker manages the model runtime.",
     "Print the local endpoint and a non-executing command template.",
     "Develop and test an API integration locally before deciding whether local inference meets latency and quality goals.",
     "endpoint = \"http://localhost:12434/engines/v1\"\nprint(\"Configure your OpenAI-compatible client base URL:\", endpoint)\nprint(\"Model pull/run commands depend on Docker Desktop version and model availability.\")"),
    ("amazon-sagemaker", "Amazon SageMaker", "Integrations",
     "Amazon SageMaker is a managed AWS service for building, training, deploying, and operating machine-learning models.",
     "A managed ML workshop provides scalable training and hosted endpoints, with access and cost controls to plan.",
     "Keep AWS SDK calls opt-in and never create billable resources from an introductory notebook.",
     "Deploy a batch inference workflow with role-based access, explicit instance sizing, and endpoint cleanup steps.",
     "import os\nregion = os.getenv(\"AWS_DEFAULT_REGION\", \"not-configured\")\nprint(\"Region:\", region)\nprint(\"Review cost, IAM role, endpoint lifecycle, and data location before provisioning.\")"),
    ("amazon-bedrock", "Amazon Bedrock", "Integrations",
     "Amazon Bedrock provides managed access to foundation models and related capabilities through AWS APIs.",
     "A managed model catalog can simplify access, while model selection, permissions, and cost remain application decisions.",
     "Check the configured AWS region without making a network request.",
     "Compare approved model options for a RAG application and grant only the required model invocation permission.",
     "import os\nprint(\"Bedrock region:\", os.getenv(\"AWS_DEFAULT_REGION\", \"not-configured\"))\nprint(\"No AWS request is made by this offline lesson.\")"),
    ("fastapi", "FastAPI", "Production",
     "FastAPI is a Python web framework for defining typed HTTP APIs and automatically documenting their schemas.",
     "It is a labeled, validated front desk between callers and application services.",
     "Validate an incoming query with a small function before passing it to retrieval.",
     "Expose a search endpoint with bounded inputs and an explicit timeout/error contract.",
     "def validate_query(query: str) -> str:\n    cleaned = query.strip()\n    if not cleaned or len(cleaned) > 500:\n        raise ValueError(\"Query must contain 1 to 500 characters\")\n    return cleaned\n\nprint(validate_query(\"  find a manual  \"))"),
    ("postgresql", "PostgreSQL", "Production",
     "PostgreSQL is a relational database that provides transactions, constraints, indexing, and full-text search.",
     "A reliable ledger enforces rules and commits related changes together.",
     "Insert a document and its outbox event inside one database transaction.",
     "Persist source documents and an indexing event atomically so a crash cannot silently lose the indexing request.",
     "transaction = [\"BEGIN\", \"INSERT INTO documents ...\", \"INSERT INTO outbox_events ...\", \"COMMIT\"]\nprint(\" -> \".join(transaction))"),
    ("qdrant", "Qdrant", "Production",
     "Qdrant is a vector database for storing vectors with payload metadata and retrieving nearest neighbors.",
     "A map of learned coordinates lets you find nearby ideas, with labels attached to each point.",
     "Check that stored and query vectors have the same dimension before similarity search.",
     "Store chunk identifiers and access-control metadata alongside vectors; apply authorization filters at query time.",
     "stored, query = [0.2, 0.1, 0.7], [0.1, 0.1, 0.7]\nassert len(stored) == len(query), \"Vector dimensions must match\"\nprint(\"compatible vector dimension:\", len(query))"),
    ("transactional-outbox", "PostgreSQL transactional outbox", "Production",
     "A transactional outbox writes application data and an event record in one database transaction, then publishes the event asynchronously.",
     "The order and its dispatch note go into the same locked ledger; a separate courier can retry delivery.",
     "Model a committed document and pending event, then retry an idempotent delivery.",
     "Index a saved document into Qdrant after commit, tolerating worker restarts and duplicate event delivery.",
     "database = {\"document_saved\": True, \"outbox\": {\"status\": \"pending\", \"event_id\": \"evt-1\"}}\n\ndef deliver(event_id):\n    print(\"idempotent upsert for\", event_id)\n    database[\"outbox\"][\"status\"] = \"processed\"\n\ndeliver(database[\"outbox\"][\"event_id\"])\ndeliver(database[\"outbox\"][\"event_id\"])\nprint(database[\"outbox\"][\"status\"])"),
    ("data-preparation", "Data preparation for machine learning", "Foundations",
     "Data preparation checks quality, handles missing values, and converts raw records into a consistent dataset before modeling.",
     "It is mise en place: measure and prepare ingredients before cooking so the recipe is repeatable.",
     "Validate a small sensor table, impute a missing value, and separate predictors from the target.",
     "Prepare sensor data while preserving missingness information and preventing future measurements from leaking into training.",
     "records = [{\"temperature\": 20.0, \"status\": \"ok\"}, {\"temperature\": None, \"status\": \"ok\"}]\nvalues = [row[\"temperature\"] for row in records if row[\"temperature\"] is not None]\nmean = sum(values) / len(values)\nprint([row[\"temperature\"] if row[\"temperature\"] is not None else mean for row in records])"),
    ("linear-algebra", "Linear algebra for machine learning", "Foundations",
     "Vectors and matrices represent examples, features, weights, and transformations used by machine-learning models.",
     "A vector is a compact measurement list; a matrix applies the same weighted recipe to many examples.",
     "Calculate a linear model's score using a feature vector and a weight vector.",
     "Turn machine telemetry into a consistent feature matrix and verify dimensions before inference.",
     "features = [2.0, 3.0]\nweights = [0.4, -0.2]\nbias = 0.1\nscore = sum(x * w for x, w in zip(features, weights)) + bias\nprint(score)"),
    ("probability-statistics", "Probability and statistics for AI", "Foundations",
     "Statistics summarizes data and uncertainty; probability describes uncertainty in outcomes and model predictions.",
     "Statistics describes the measurements you observed; probability quantifies what might happen next.",
     "Estimate a positive-event rate and calculate a simple conditional probability from counts.",
     "Compare model error rates across equipment groups without confusing noisy samples with reliable evidence.",
     "observations = [0, 0, 1, 0, 1, 0, 0, 1]\nrate = sum(observations) / len(observations)\nprint({\"positive_rate\": rate, \"sample_size\": len(observations)})"),
    ("ml-evaluation", "Machine-learning evaluation", "Machine learning",
     "Model evaluation estimates generalization with data kept separate from fitting and uses metrics tied to the real cost of errors.",
     "A fair exam uses unseen questions and a scoring rubric that reflects which mistakes matter.",
     "Compare a majority baseline with a classifier using precision, recall, and a confusion matrix.",
     "Choose a decision threshold for a rare but costly equipment failure instead of relying on accuracy alone.",
     "from sklearn.metrics import precision_score, recall_score\nactual = [1, 1, 1, 0, 0, 0]\npredicted = [1, 0, 1, 0, 1, 0]\nprint({\"precision\": precision_score(actual, predicted), \"recall\": recall_score(actual, predicted)})"),
    ("supervised-learning", "Supervised learning", "Machine learning",
     "Supervised learning learns a mapping from labeled inputs to targets, including classification labels or numeric regression values.",
     "A tutor gives worked examples with answers, then asks the learner to solve new examples.",
     "Fit a classifier to labeled numeric examples and score a held-out case.",
     "Predict whether a machine will fail within a defined window using only features available before that window.",
     "from sklearn.linear_model import LogisticRegression\nX = [[0], [1], [2], [8], [9], [10]]\ny = [0, 0, 0, 1, 1, 1]\nmodel = LogisticRegression().fit(X, y)\nprint(\"prediction:\", model.predict([[7]])[0])"),
    ("classical-models", "Classical machine-learning models", "Machine learning",
     "Classical models such as linear models, decision trees, and ensembles provide strong baselines for structured data.",
     "Different tools make different trade-offs: a ruler is interpretable, while a panel of experts can capture complex patterns.",
     "Compare logistic regression and a shallow decision tree on the same held-out split.",
     "Benchmark a transparent baseline against a more flexible model before selecting an operational predictor.",
     "from sklearn.linear_model import LogisticRegression\nfrom sklearn.tree import DecisionTreeClassifier\nX = [[0], [1], [2], [8], [9], [10]]\ny = [0, 0, 0, 1, 1, 1]\nfor model in (LogisticRegression(), DecisionTreeClassifier(max_depth=2, random_state=0)):\n    model.fit(X, y)\n    print(type(model).__name__, model.predict([[7]])[0])"),
    ("unsupervised-learning", "Unsupervised learning", "Machine learning",
     "Unsupervised learning finds structure in inputs without target labels, for example clusters or lower-dimensional representations.",
     "Instead of providing answer keys, ask the learner to group similar examples and describe the patterns.",
     "Cluster unlabeled points and inspect the resulting groups.",
     "Explore customer behavior groups without presenting clusters as ground-truth customer types.",
     "from sklearn.cluster import KMeans\npoints = [[1, 1], [1.2, 0.9], [8, 8], [8.2, 7.9]]\nclusters = KMeans(n_clusters=2, random_state=0, n_init=10).fit_predict(points)\nprint(clusters.tolist())"),
    ("semi-supervised-learning", "Semi-supervised learning", "Machine learning",
     "Semi-supervised learning combines a small labeled set with a larger unlabeled set to improve learning when labels are scarce.",
     "A teacher labels a few examples; the learner uses them to organize a much larger unlabeled pile.",
     "Propagate labels across a small synthetic dataset, then compare known and inferred labels.",
     "Use pseudo-labels for document triage only after estimating error and keeping uncertain examples for human review.",
     "from sklearn.semi_supervised import LabelSpreading\nX = [[0.0], [0.2], [0.4], [5.0], [5.2], [5.4]]\ny = [0, -1, -1, -1, -1, 1]\nmodel = LabelSpreading(kernel=\"knn\", n_neighbors=2).fit(X, y)\nprint(\"inferred labels:\", model.transduction_.tolist())"),
    ("reinforcement-learning", "Reinforcement learning", "Machine learning",
     "Reinforcement learning learns a policy through actions and reward signals received while interacting with an environment.",
     "A learner tries choices in a game and improves from reward or penalty rather than an answer key for every state.",
     "Train a tiny tabular Q-learning agent to move toward a goal in a short line world.",
     "Optimize a controllable process only in a safe simulator before any real-world policy can affect equipment.",
     "import random\nrandom.seed(3)\nq = [[0.0, 0.0] for _ in range(4)]\nfor _ in range(250):\n    state = 0\n    while state < 3:\n        action = 1 if random.random() < 0.8 else 0\n        next_state = max(0, min(3, state + (1 if action else -1)))\n        reward = 1.0 if next_state == 3 else -0.01\n        q[state][action] += 0.2 * (reward + 0.9 * max(q[next_state]) - q[state][action])\n        state = next_state\nprint(\"best first action:\", max(range(2), key=lambda action: q[0][action]))"),
    ("recommendation-systems", "Recommendation systems", "Machine learning",
     "Recommendation systems rank items for a user using signals such as item content, user-item interactions, or both.",
     "A librarian combines what you said you like with what similar readers borrowed.",
     "Create a user-item matrix and recommend an unseen item from similar users' ratings.",
     "Evaluate recommendations with a temporal holdout and check popularity bias, cold starts, and coverage.",
     "ratings = {\"A\": {\"book-1\": 5, \"book-2\": 4}, \"B\": {\"book-1\": 5, \"book-3\": 4}, \"C\": {\"book-2\": 5, \"book-3\": 4}}\nuser = \"A\"\nscores = {}\nfor other, items in ratings.items():\n    if other != user:\n        for item, rating in items.items():\n            if item not in ratings[user]:\n                scores[item] = scores.get(item, 0) + rating\nprint(sorted(scores.items(), key=lambda pair: (-pair[1], pair[0])))"),
    ("feature-engineering", "Feature engineering", "Machine learning",
     "Feature engineering transforms raw fields into useful model inputs while preserving meaning and preventing leakage.",
     "It turns raw ingredients into a form a particular recipe can use without accidentally adding the answer.",
     "Derive a time-based feature and encode a category with a scikit-learn pipeline.",
     "Build time-safe features for failure prediction and review them for target leakage and unstable definitions.",
     "from sklearn.compose import ColumnTransformer\nfrom sklearn.preprocessing import OneHotEncoder, StandardScaler\nfrom sklearn.pipeline import make_pipeline\nfrom sklearn.impute import SimpleImputer\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.pipeline import Pipeline\nnumeric = Pipeline([(\"impute\", SimpleImputer()), (\"scale\", StandardScaler())])\ncategorical = OneHotEncoder(handle_unknown=\"ignore\")\npreprocess = ColumnTransformer([(\"number\", numeric, [0]), (\"category\", categorical, [1])])\nprint(preprocess)"),
    ("neural-networks", "Neural networks", "Deep learning",
     "A neural network composes weighted sums and nonlinear activations into a model that can learn complex input-output relationships.",
     "Each layer transforms a signal, and stacked layers build increasingly useful representations.",
     "Run a small feed-forward network through a hidden layer and sigmoid output.",
     "Inspect how changing learned weights changes a classifier's output, rather than treating a neural network as a black box.",
     "import numpy as np\nsigmoid = lambda x: 1 / (1 + np.exp(-x))\nx = np.array([0.6, 0.2])\nW1 = np.array([[0.5, -0.4], [0.3, 0.8]])\nW2 = np.array([[0.7], [-0.2]])\nhidden = np.tanh(x @ W1)\nprobability = sigmoid((hidden @ W2)[0])\nprint(\"hidden:\", hidden.round(3), \"output probability:\", round(float(probability), 3))"),
    ("backpropagation", "Backpropagation and gradient descent", "Deep learning",
     "Backpropagation applies the chain rule to compute how each parameter affects loss; gradient descent updates parameters to reduce that loss.",
     "Trace an error backward through a chain of calculations, then adjust each knob in the direction that reduces it.",
     "Compute a linear model's gradient and perform one explicit gradient-descent update.",
     "Use training and validation curves to detect when optimization stops improving generalization.",
     "x, target, weight, bias, learning_rate = 2.0, 5.0, 0.5, 0.0, 0.1\nprediction = weight * x + bias\nerror = prediction - target\ngrad_weight = 2 * error * x\ngrad_bias = 2 * error\nweight -= learning_rate * grad_weight\nbias -= learning_rate * grad_bias\nprint({\"updated_weight\": weight, \"updated_bias\": bias, \"new_prediction\": weight * x + bias})"),
    ("deep-learning", "Deep learning", "Deep learning",
     "Deep learning trains neural networks with multiple layers to learn representations from data, often using accelerator hardware and large datasets.",
     "A deep stack builds from simple patterns to more abstract ones, but also needs more data and careful validation.",
     "Fit a small multilayer perceptron and compare its held-out predictions with a baseline.",
     "Choose a compact architecture and report training time, validation quality, and resource use for an image task.",
     "from sklearn.datasets import make_moons\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.neural_network import MLPClassifier\nX, y = make_moons(n_samples=120, noise=0.15, random_state=8)\nX_train, X_test, y_train, y_test = train_test_split(X, y, random_state=8, stratify=y)\nmodel = MLPClassifier(hidden_layer_sizes=(16, 8), max_iter=500, random_state=8).fit(X_train, y_train)\nprint(\"held-out accuracy:\", round(model.score(X_test, y_test), 3))"),
    ("generative-models", "Generative models: VAE, GAN, and diffusion", "Deep learning",
     "Generative models learn patterns in data to create new samples; VAEs, GANs, and diffusion models use different learning and sampling mechanisms.",
     "One learns a compressed probabilistic map, one trains a generator against a critic, and one learns to undo gradually added noise.",
     "Compare a simple noise-to-signal denoising step with the repeated refinement used by diffusion sampling.",
     "Select a generative family based on output type, data rights, quality measures, and compute rather than novelty alone.",
     "import numpy as np\nclean = np.array([0.2, 0.8, 0.4, 0.6])\nnoise = np.array([0.1, -0.2, 0.2, -0.1])\nnoisy = clean + noise\nestimated_noise = noisy - clean\nreconstructed = noisy - estimated_noise\nprint(\"reconstruction:\", reconstructed.round(2).tolist())"),
    ("text-preprocessing", "Text preprocessing and tokenization", "Natural language processing",
     "Text preprocessing turns raw text into tokens or normalized forms while preserving distinctions important to the task.",
     "A tokenizer cuts a continuous stream into labeled pieces; normalization is a deliberate choice about which distinctions to keep.",
     "Normalize a sentence and tokenize words, punctuation, and a simple contraction.",
     "Keep identifiers, negation, and domain-specific symbols during support-ticket preprocessing.",
     "import re\ntext = \"Can't reset device E-1042!\"\nnormalized = text.lower()\ntokens = re.findall(r\"[a-z]+(?:'[a-z]+)?|[a-z]+-\\d+|[^\\w\\s]\", normalized)\nprint(tokens)"),
    ("bag-of-words", "Bag-of-words representations", "Natural language processing",
     "Bag of words represents each document by token counts, ignoring word order while retaining vocabulary membership and frequency.",
     "It is a shopping receipt of words: what appeared and how often, but not the order they were used.",
     "Build a fixed vocabulary and count each term in several short documents.",
     "Use sparse bag-of-words features as a fast baseline, then test whether losing word order harms the task.",
     "from collections import Counter\ntexts = [\"reset password\", \"password reset failed\"]\nvocabulary = sorted(set(\" \".join(texts).split()))\nrows = [[Counter(text.split())[word] for word in vocabulary] for text in texts]\nprint(vocabulary)\nprint(rows)"),
    ("word2vec", "Word2Vec", "Natural language processing",
     "Word2Vec learns dense word vectors by predicting nearby context words or a target word from its context.",
     "Words become coordinates based on the neighborhoods they tend to appear with.",
     "Create a tiny context co-occurrence representation and compare words by cosine similarity.",
     "Inspect learned neighbors for domain terms and remember that similarity reflects training data, not verified meaning.",
     "import numpy as np\nvectors = {\"battery\": np.array([1.0, 0.8, 0.0]), \"charger\": np.array([0.9, 0.7, 0.1]), \"invoice\": np.array([0.0, 0.1, 1.0])}\nquery = vectors[\"battery\"]\ncosine = {word: float(query @ vector / (np.linalg.norm(query) * np.linalg.norm(vector))) for word, vector in vectors.items() if word != \"battery\"}\nprint(sorted(cosine.items(), key=lambda pair: -pair[1]))"),
    ("attention", "Attention mechanisms", "Language models",
     "Attention computes input-dependent weights that let each position combine information from other positions.",
     "A reader assigns different focus to each reference while interpreting a sentence.",
     "Compute scaled dot-product attention for a query, keys, and value vectors.",
     "Inspect attention weights as a model computation aid, not automatically as a faithful explanation of its decision.",
     "import numpy as np\nquery = np.array([1.0, 0.0])\nkeys = np.array([[1.0, 0.0], [0.0, 1.0]])\nvalues = np.array([[3.0, 0.0], [0.0, 6.0]])\nscores = query @ keys.T / np.sqrt(query.size)\nweights = np.exp(scores - scores.max()); weights /= weights.sum()\nprint(\"weights:\", weights.round(3), \"attended:\", (weights @ values).round(3))"),
    ("prompt-engineering", "Prompt engineering", "Language models",
     "Prompt engineering makes instructions, context, constraints, and output formats explicit to improve model behavior.",
     "A precise work order states the task, evidence to use, boundaries, and the format for delivery.",
     "Construct a grounded prompt from a task, trusted context, and output schema.",
     "Test prompts against a fixed set of representative and adversarial inputs instead of judging from one impressive response.",
     "task = \"Answer the customer's question using only the supplied policy.\"\ncontext = \"Returns are accepted within 30 days with a receipt.\"\nquestion = \"Can I return this after 20 days?\"\nprompt = f\"{task}\\nPolicy: {context}\\nQuestion: {question}\\nReturn JSON with answer and evidence.\"\nprint(prompt)"),
    ("llm-inference", "LLM inference and decoding", "Language models",
     "LLM inference generates tokens stepwise; decoding settings such as temperature, top-k, and top-p affect diversity and determinism.",
     "The model proposes continuations, while decoding is the rule for choosing among them.",
     "Apply temperature-scaled softmax to logits and sample reproducibly from the resulting token distribution.",
     "Use deterministic decoding for repeatable structured tasks and measure quality before allowing higher sampling variance.",
     "import numpy as np\nlogits = np.array([2.0, 1.0, 0.1])\ntemperature = 0.7\nscaled = logits / temperature\nprobabilities = np.exp(scaled - scaled.max()); probabilities /= probabilities.sum()\nprint(\"token probabilities:\", probabilities.round(3).tolist())"),
    ("fine-tuning", "Fine-tuning and parameter-efficient adaptation", "Language models",
     "Fine-tuning adapts pretrained model parameters to a task; parameter-efficient methods such as LoRA train a smaller set of added parameters.",
     "Instead of retraining a whole library, add a small task-specific index tab that changes how it is used.",
     "Estimate trainable parameter savings when a low-rank adapter replaces a full weight update.",
     "Compare prompting, retrieval, and adapter fine-tuning on a held-out task set before taking on data and deployment costs.",
     "input_dim, output_dim, rank = 4096, 4096, 8\nfull_parameters = input_dim * output_dim\nadapter_parameters = rank * (input_dim + output_dim)\nprint({\"full\": full_parameters, \"adapter\": adapter_parameters, \"reduction\": round(1 - adapter_parameters / full_parameters, 4)})"),
    ("multimodal-ai", "Multimodal AI", "Language models",
     "Multimodal models process or connect different input and output types such as text, images, audio, and video.",
     "A system combines specialists for different senses while aligning their representations and timing.",
     "Represent a multimodal request as typed content parts and validate modality-specific metadata.",
     "Ground image descriptions in visible evidence, preserve source references, and evaluate each modality independently.",
     "request = {\"parts\": [{\"type\": \"text\", \"text\": \"Describe the visible damage.\"}, {\"type\": \"image\", \"media_type\": \"image/jpeg\", \"source\": \"approved-image-001\"}]}\nassert all(part[\"type\"] in {\"text\", \"image\", \"audio\", \"video\"} for part in request[\"parts\"])\nprint(request)"),
    ("llm-evaluation", "LLM application evaluation", "Language models",
     "LLM evaluation tests task quality, groundedness, safety, latency, and cost with representative examples and explicit rubrics.",
     "A model needs more than a spelling test: it is graded on correctness, evidence, and safe behavior across many cases.",
     "Score whether an answer is supported by retrieved evidence and flag unsupported claims.",
     "Run a versioned regression set when changing prompts, models, chunking, or retrieval settings.",
     "cases = [(\"Returns last 30 days\", \"Returns accepted within 30 days\", True), (\"Free lifetime returns\", \"Returns accepted within 30 days\", False)]\nfor answer, evidence, supported in cases:\n    measured = answer in evidence or answer == evidence\n    print({\"answer\": answer, \"expected_supported\": supported, \"simple_check\": measured})"),
    ("responsible-ai", "Responsible and safe AI", "Engineering practice",
     "Responsible AI makes privacy, fairness, transparency, security, and human oversight part of system design and evaluation.",
     "A good engineering system includes guardrails, audit trails, and a safe stop—not only a fast route to output.",
     "Measure a simple group-level error-rate difference and define a human-review threshold.",
     "Review sensitive data flows, subgroup performance, misuse paths, and appeal mechanisms before deployment.",
     "from collections import defaultdict\ngroups = {\"group-A\": ([1, 1, 0, 0], [1, 0, 0, 0]), \"group-B\": ([1, 1, 0, 0], [1, 1, 1, 0])}\nfor group, (actual, predicted) in groups.items():\n    positives = sum(actual)\n    recall = sum(a == p == 1 for a, p in zip(actual, predicted)) / positives\n    print(group, \"positive recall:\", round(recall, 2))"),
    ("tool-calling", "LLM tool calling", "Agents",
     "Tool calling lets a model request a named operation with structured arguments; application code validates and authorizes before execution.",
     "The model may fill in a request form, but a trusted operator checks the form and permissions before acting.",
     "Validate a proposed structured lookup call against an allowlist and typed arguments.",
     "Keep tools least-privileged, bounded, and auditable; require approval before external side effects.",
     "ALLOWED_TOOLS = {\"lookup_order\"}\ndef dispatch(name, arguments):\n    if name not in ALLOWED_TOOLS:\n        raise ValueError(f\"tool not allowed: {name}\")\n    order_id = arguments.get(\"order_id\")\n    if not isinstance(order_id, str) or not order_id.startswith(\"ORD-\"):\n        raise ValueError(\"invalid order_id\")\n    return {\"status\": \"found\", \"order_id\": order_id}\nprint(dispatch(\"lookup_order\", {\"order_id\": \"ORD-1042\"}))"),
    ("mlops", "MLOps and model deployment lifecycle", "Production",
     "MLOps manages data and model versions, deployment, monitoring, and rollback so machine-learning systems remain reliable after release.",
     "It is the maintenance plan for a machine: versioned parts, health checks, and a safe rollback path.",
     "Track a model version and flag a change in input distribution with a simple drift statistic.",
     "Monitor quality and data drift, route alerts to an owner, and retain a tested rollback artifact.",
     "training = [10, 11, 9, 10, 10]\nserving = [18, 19, 17, 18, 20]\ntrain_mean = sum(training) / len(training)\nserve_mean = sum(serving) / len(serving)\nprint({\"model_version\": \"ticket-risk-v1\", \"training_mean\": train_mean, \"serving_mean\": serve_mean, \"mean_shift\": serve_mean - train_mean})"),
]

ROADMAP_SECTIONS = [
    ("1. Programming and mathematical foundations", [
        "python-for-ai", "data-preparation", "linear-algebra", "probability-statistics", "ai",
        "heuristic-search", "ml",
    ]),
    ("2. Core machine learning", [
        "ml-evaluation", "supervised-learning", "classical-models", "unsupervised-learning",
        "semi-supervised-learning", "reinforcement-learning", "recommendation-systems",
        "feature-engineering", "vectorization",
    ]),
    ("3. Neural networks and deep learning", [
        "neural-networks", "backpropagation", "deep-learning", "cnn", "rnn", "lstm",
        "generative-ai", "generative-models",
    ]),
    ("4. Natural language processing and representations", [
        "text-preprocessing", "bag-of-words", "tf", "idf", "tf-idf", "word2vec", "embeddings",
    ]),
    ("5. Transformers and language-model applications", [
        "attention", "transformers", "bert", "gpt", "llm", "prompt-engineering",
        "llm-inference", "fine-tuning", "multimodal-ai", "llm-evaluation", "responsible-ai",
    ]),
    ("6. Search, retrieval, and knowledge", [
        "full-text-search", "bm25", "semantic-search", "rrf", "rag", "knowledge-graphs",
        "graphrag",
    ]),
    ("7. Agents and orchestration frameworks", [
        "agents", "tool-calling", "agent-loop", "multi-agent", "langchain", "langgraph",
        "langsmith", "llamaindex",
    ]),
    ("8. Production systems and integrations", [
        "fastapi", "postgresql", "qdrant", "transactional-outbox", "mlops", "ollama",
        "docker-model-runner", "openai", "gemini", "anthropic", "amazon-sagemaker",
        "amazon-bedrock",
    ]),
]

LEARNING_ORDER = [slug for _section, slugs in ROADMAP_SECTIONS for slug in slugs]


def build_guide(topic: tuple[str, ...], notebook_name: str) -> str:
    """Render a standalone guide whose links use the topic's assigned sequence."""
    _, title, track, idea, analogy, example, case_study, _code = topic
    return f"""# {title}

**Track:** {track}  
**Notebook:** [Open the hands-on lesson](../../notebooks/{notebook_name})

## What it is

{idea}

## Intuition

{analogy}

## How to reason about it

Start from the input and desired output. Identify what the method learns or
stores, what assumptions it makes, and how you will measure whether it works.
For production use, also define data boundaries, latency/cost limits, and a
safe failure path.

## Concept map

```mermaid
flowchart LR
    A[Input or goal] --> B[{title}]
    B --> C[Observable output]
    C --> D[Measure and verify]
```

## Small example

{example}

## Engineering case study

{case_study}

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
"""


def build_roadmap(topics_by_slug: dict[str, tuple[str, ...]]) -> str:
    """Render the ordered roadmap from the same sections used for file numbering."""
    lines = [
        "# Learning roadmap",
        "",
        "Each item links to a standalone guide; its hands-on companion has the same",
        "filename under `notebooks/`. Follow the sequence to build prerequisites",
        "before moving from foundational methods to deployed AI systems.",
        "",
    ]
    sequence = 0
    for section, slugs in ROADMAP_SECTIONS:
        lines.extend([f"## {section}", ""])
        for slug in slugs:
            sequence += 1
            title = topics_by_slug[slug][1]
            guide_name = f"{sequence:03d}-{slug}.md"
            lines.append(f"{sequence}. [{title}](concepts/{guide_name})")
        lines.append("")

    lines.extend(
        [
            "## Suggested project sequence",
            "",
            "1. Prepare a small labeled dataset, establish a baseline, and compare",
            "   supervised and unsupervised approaches using a held-out evaluation set.",
            "2. Build a content-based and collaborative-filtering recommender; inspect",
            "   coverage, cold starts, and popularity bias.",
            "3. Build lexical and semantic search, combine results with reciprocal-rank",
            "   fusion, and measure retrieval quality on representative queries.",
            "4. Add grounded answers with citations, then evaluate faithfulness, safety,",
            "   latency, and cost against a versioned test set.",
            "5. Build the hybrid-search reference app and test retries, idempotency,",
            "   authorization, monitoring, and rollback behavior.",
            "",
            "For every project, define data boundaries, cost limits, failure behavior,",
            "and a human escalation path before exposing it to users.",
            "",
            "## Scope boundaries",
            "",
            "This curriculum is a practical core, not an exhaustive catalog. Advanced",
            "electives include time-series forecasting, causal inference, Bayesian",
            "modeling, graph neural networks, distributed training, and specialized",
            "reinforcement-learning algorithms. Add them after the core when they match",
            "your application domain.",
            "",
        ]
    )
    return "\n".join(lines)


def build_notebook(
    topic: tuple[str, ...], guide_name: str
) -> dict[str, object]:
    """Choose the comprehensive local, AI-specific, or provider lesson builder."""
    slug, title, track, idea, analogy, example, case_study, code = topic
    if slug == "ai":
        return build_ai_notebook(guide_name)
    if slug in LESSONS:
        return build_comprehensive_notebook(topic, guide_name, LESSONS[slug])
    if slug in {
        "ollama",
        "openai",
        "gemini",
        "anthropic",
        "docker-model-runner",
        "amazon-sagemaker",
        "amazon-bedrock",
    }:
        return build_comprehensive_notebook(topic, guide_name, provider_lesson(slug))

    intro = f"""# {title}

**Track:** {track} · **Playbook guide:** [`guides/concepts/{guide_name}`](../guides/concepts/{guide_name})

## Goal

{idea}

> **Intuition:** {analogy}

## Engineering example

{example}

## Concept map

```mermaid
flowchart LR
    A[Input or goal] --> B[{title}]
    B --> C[Observable output]
    C --> D[Measure and verify]
```

## Run the toy example

The cell below uses only the Python standard library and runs offline. It is a
small illustration, not a production implementation.
"""
    exercise = f"""## Case study and exercises

**Case study:** {case_study}

1. Modify one input and predict the result before executing the code again.
2. Identify one limitation this toy example hides.
3. Add a check or test for a failure that matters in the case study.
4. What evidence would convince you that the production version works?

Continue with the [concept guide](../guides/concepts/{guide_name}) and the
[learning roadmap](../guides/ROADMAP.md).
"""
    code_lines = textwrap.dedent(code).splitlines(keepends=True)
    if code_lines and code_lines[0].startswith(("import ", "from ")):
        code_lines.insert(1, "\n")
    cells = [
        {
            "cell_type": "markdown",
            "id": f"{slug}-intro",
            "metadata": {},
            "source": intro.splitlines(keepends=True),
        },
        {
            "cell_type": "code",
            "id": f"{slug}-example",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": code_lines,
        },
        {
            "cell_type": "markdown",
            "id": f"{slug}-exercises",
            "metadata": {},
            "source": exercise.splitlines(keepends=True),
        },
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11+"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_comprehensive_notebook(
    topic: tuple[str, ...], guide_name: str, steps: list[LessonStep]
) -> dict[str, object]:
    """Build a runnable notebook with explanatory markdown before each code step.

    Keeping the explanation beside its implementation makes the notebooks
    self-guiding even when read outside the repository roadmap.
    """
    slug, title, track, idea, analogy, _example, case_study, _code = topic
    cells: list[dict[str, object]] = [
        {
            "cell_type": "markdown",
            "id": f"{slug}-intro",
            "metadata": {},
            "source": textwrap.dedent(f"""\
                # {title}: a hands-on implementation

                **Track:** {track} · **Guide:** [`{guide_name}`](../guides/concepts/{guide_name})

                {idea}

                > **Intuition:** {analogy}

                This lesson builds a small working example in stages: prepare inputs, implement
                the core idea, run it on a realistic toy case, and inspect its output and limits.
                It runs offline unless a cell is explicitly marked as an optional provider call.

                ```mermaid
                flowchart LR
                    A[Prepare inputs] --> B[Implement {title}]
                    B --> C[Run on example]
                    C --> D[Evaluate and inspect]
                ```

                **Case study:** {case_study}

                Run the cells from top to bottom. To install the notebook environment, follow
                [`guides/SETUP.md`](../guides/SETUP.md). The toy data and implementation are for
                learning, not a production quality, safety, or security guarantee.
                """).splitlines(keepends=True),
        }
    ]

    for index, lesson_step in enumerate(steps, start=1):
        cells.append(
            {
                "cell_type": "markdown",
                "id": f"{slug}-step-{index}-notes",
                "metadata": {},
                "source": textwrap.dedent(f"""\
                    ## {lesson_step.heading}

                    {lesson_step.explanation}
                    """).splitlines(keepends=True),
            }
        )
        source = textwrap.dedent(lesson_step.code).splitlines(keepends=True)
        if source and source[0].startswith(("import ", "from ")):
            last_import = 0
            for line_index, line in enumerate(source):
                if line.startswith(("import ", "from ")):
                    last_import = line_index
                elif line.strip():
                    break
            next_code = last_import + 1
            while next_code < len(source) and not source[next_code].strip():
                next_code += 1
            if next_code < len(source):
                statement = source[next_code].lstrip()
                required_blank_lines = (
                    2 if statement.startswith(("def ", "class ", "@")) else 1
                )
                existing_blank_lines = next_code - last_import - 1
                for _ in range(max(0, required_blank_lines - existing_blank_lines)):
                    source.insert(next_code, "\n")
                    next_code += 1
        cells.append(
            {
                "cell_type": "code",
                "id": f"{slug}-step-{index}-code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": source,
            }
        )

    cells.append(
        {
            "cell_type": "markdown",
            "id": f"{slug}-wrap-up",
            "metadata": {},
            "source": textwrap.dedent(f"""\
                ## Wrap-up and next steps

                - Identify what was learned, stored, retrieved, or generated in this implementation.
                - Change an input and observe how the output changes.
                - Test one failure case and decide when the system should abstain or ask for help.
                - Replace toy data/components only after you can evaluate the change against a
                  held-out or representative test set.

                Continue with the [concept guide](../guides/concepts/{guide_name}) and the
                [learning roadmap](../guides/ROADMAP.md).
                """).splitlines(keepends=True),
        }
    )

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11+"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def build_ai_notebook(guide_name: str) -> dict[str, object]:
    """Create an end-to-end, offline supervised-learning lesson for AI.

    Synthetic data keeps execution reproducible and private; held-out evaluation
    and a human-review action demonstrate why a toy classifier is not a safety
    decision system.
    """
    cells = [
        {
            "cell_type": "markdown",
            "id": "ai-intro",
            "metadata": {},
            "source": textwrap.dedent(f"""\
                # Artificial intelligence: build a ticket-triage model

                **Track:** Foundations · **Guide:** [`{guide_name}`](../guides/concepts/{guide_name})

                AI is a broad field, not a single algorithm. This hands-on lesson builds one
                practical AI system: a supervised text classifier that estimates whether a
                support ticket needs urgent human review.

                We will prepare labeled examples, hold out test data, train a TF-IDF +
                logistic-regression pipeline, measure its errors, compare it with a simple
                keyword baseline, and score new tickets. The training data is synthetic and
                tiny, so this is a learning demo—not a safety or production triage system.

                ```mermaid
                flowchart LR
                    A[Labeled example tickets] --> B[Train/test split]
                    B --> C[TF-IDF text features]
                    C --> D[Train classifier]
                    D --> E[Evaluate held-out tickets]
                    E --> F[Estimate urgency for a new ticket]
                ```

                **Requirements:** Python and scikit-learn. Install the project
                notebook extra as described in [`guides/SETUP.md`](../guides/SETUP.md).
                All cells run offline; no API key or cloud account is used.
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "markdown",
            "id": "ai-dataset-explanation",
            "metadata": {},
            "source": textwrap.dedent("""\
                ## 1. Create a small labeled dataset

                Each ticket has an input text and a human-assigned label. A real system
                would need carefully reviewed, representative, privacy-approved examples.
                We use synthetic examples here so the exercise is reproducible and private.
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "code",
            "id": "ai-dataset",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": textwrap.dedent("""\
                from collections import Counter

                tickets = [
                    ("Someone threatened to hurt me and knows where I live", "urgent"),
                    ("I may hurt myself and need help immediately", "urgent"),
                    ("An attacker broke into my account and is stealing funds", "urgent"),
                    ("Smoke is coming from the device and it is getting hot", "urgent"),
                    ("I was injured when the charger exploded", "urgent"),
                    ("Someone is following me after sending threats", "urgent"),
                    ("An intruder has my password and is taking money", "urgent"),
                    ("My device sparked and burned my hand", "urgent"),
                    ("The battery is swelling and smells like burning", "urgent"),
                    ("I received a threat that someone will attack me", "urgent"),
                    ("My account was hijacked and unauthorized transfers started", "urgent"),
                    ("I feel unsafe because my partner threatened violence", "urgent"),
                    ("I am thinking about harming myself tonight", "urgent"),
                    ("The adapter caught fire and damaged the desk", "urgent"),
                    ("Someone stole my login and changed all recovery details", "urgent"),
                    ("My child got an electric shock from the product", "urgent"),
                    ("How can I update my billing address", "routine"),
                    ("Please explain the monthly subscription charge", "routine"),
                    ("Where can I download the user manual", "routine"),
                    ("Can I change my order before it ships", "routine"),
                    ("The screen arrived scratched but still turns on", "routine"),
                    ("I forgot my password and need to reset it", "routine"),
                    ("Please cancel the renewal for next month", "routine"),
                    ("How long does standard delivery take", "routine"),
                    ("The app is slow when I open settings", "routine"),
                    ("I would like to return the wrong color item", "routine"),
                    ("Can I transfer my saved settings to a new phone", "routine"),
                    ("I received a duplicate receipt by email", "routine"),
                    ("The package is late and tracking has not changed", "routine"),
                    ("How do I pair the headphones to my laptop", "routine"),
                    ("The invoice has an incorrect company name", "routine"),
                    ("The keyboard key is sticky but the rest works", "routine"),
                ]

                texts = [text for text, _label in tickets]
                labels = [label for _text, label in tickets]
                print(f"Examples: {len(tickets)}")
                print(f"Label counts: {dict(Counter(labels))}")
                print(f"One example: {tickets[0]}")
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "markdown",
            "id": "ai-split-explanation",
            "metadata": {},
            "source": textwrap.dedent("""\
                ## 2. Split before learning

                Keep some labeled examples out of training. The test set estimates
                performance on examples the model did not fit on. `stratify` preserves the
                class balance in this small split; `random_state` makes it repeatable.
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "code",
            "id": "ai-split",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": textwrap.dedent("""\
                from sklearn.model_selection import train_test_split

                X_train, X_test, y_train, y_test = train_test_split(
                    texts,
                    labels,
                    test_size=0.25,
                    random_state=42,
                    stratify=labels,
                )
                print(f"Training examples: {len(X_train)}")
                print(f"Held-out test examples: {len(X_test)}")
                print(f"Test label counts: {dict(Counter(y_test))}")
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "markdown",
            "id": "ai-training-explanation",
            "metadata": {},
            "source": textwrap.dedent("""\
                ## 3. Build and train a machine-learning model

                TF-IDF turns ticket text into weighted word and phrase features. Logistic
                regression learns weights from the labeled training examples. Keeping
                vectorization and classification in one scikit-learn `Pipeline` ensures
                the vocabulary is fit on training data only and reused consistently for
                evaluation and predictions.
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "code",
            "id": "ai-training",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": textwrap.dedent("""\
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.linear_model import LogisticRegression
                from sklearn.pipeline import make_pipeline

                model = make_pipeline(
                    TfidfVectorizer(ngram_range=(1, 2), lowercase=True, sublinear_tf=True),
                    LogisticRegression(max_iter=1000, random_state=42),
                )
                model.fit(X_train, y_train)
                print("Learned labels:", list(model.classes_))
                print("Vocabulary size:", len(model.named_steps["tfidfvectorizer"].vocabulary_))
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "markdown",
            "id": "ai-evaluation-explanation",
            "metadata": {},
            "source": textwrap.dedent("""\
                ## 4. Evaluate on tickets the model did not train on

                Accuracy is only the fraction correct. The classification report also
                exposes precision and recall for each label. For a real safety-sensitive
                workflow, a missed urgent case can be much more costly than an extra
                human review, so inspect urgent-class recall and every error—not accuracy
                alone. This tiny holdout is illustrative and cannot establish readiness.
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "code",
            "id": "ai-evaluation",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": textwrap.dedent("""\
                from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

                test_predictions = model.predict(X_test)
                print(f"Held-out accuracy: {accuracy_score(y_test, test_predictions):.2f}")
                print(classification_report(y_test, test_predictions, zero_division=0))
                print("Confusion matrix (rows=true, columns=predicted):")
                print(confusion_matrix(y_test, test_predictions, labels=model.classes_))
                print("Label order:", list(model.classes_))
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "markdown",
            "id": "ai-baseline-explanation",
            "metadata": {},
            "source": textwrap.dedent("""\
                ## 5. Compare against a hand-written baseline

                A keyword rule is easier to explain, but only recognizes words explicitly
                listed by its author. Compare its held-out predictions with the learned
                model. Neither approach is automatically correct: look at missed urgent
                tickets and false alarms before choosing an approach.
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "code",
            "id": "ai-baseline",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": textwrap.dedent("""\
                from sklearn.metrics import precision_score, recall_score

                urgent_keywords = {
                    "hurt", "harm", "threat", "smoke", "fire", "injured",
                    "burned", "burning", "unsafe", "hijacked", "stole",
                    "stealing", "shock", "attacker", "exploded",
                }

                def keyword_baseline(text):
                    words = set(text.lower().replace(",", " ").replace(".", " ").split())
                    return "urgent" if words & urgent_keywords else "routine"

                rule_predictions = [keyword_baseline(text) for text in X_test]
                for name, predictions in (
                    ("keyword rule", rule_predictions),
                    ("TF-IDF + logistic regression", test_predictions),
                ):
                    print(
                        f"{name}: "
                        f"accuracy={accuracy_score(y_test, predictions):.2f}, "
                        f"urgent precision={precision_score(y_test, predictions, pos_label='urgent', zero_division=0):.2f}, "
                        f"urgent recall={recall_score(y_test, predictions, pos_label='urgent', zero_division=0):.2f}"
                    )
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "markdown",
            "id": "ai-inference-explanation",
            "metadata": {},
            "source": textwrap.dedent("""\
                ## 6. Score new tickets

                `predict_proba` gives model scores, not guaranteed probabilities of real-world
                risk. The example uses a configurable 0.50 review threshold to demonstrate a
                human-in-the-loop policy. Never use this tiny synthetic model to make real
                safety, account, or emergency decisions.
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "code",
            "id": "ai-inference",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": textwrap.dedent("""\
                from pprint import pprint


                def triage_ticket(text, review_threshold=0.50):
                    probabilities = model.predict_proba([text])[0]
                    urgent_index = list(model.classes_).index("urgent")
                    urgent_score = float(probabilities[urgent_index])
                    return {
                        "ticket": text,
                        "urgent_model_score": round(urgent_score, 3),
                        "predicted_label": model.classes_[probabilities.argmax()],
                        "action": (
                            "human_review"
                            if urgent_score >= review_threshold
                            else "standard_queue"
                        ),
                    }

                new_tickets = [
                    "There is a burning smell and smoke coming from my charger",
                    "How can I download a copy of my monthly invoice?",
                ]
                predictions = [triage_ticket(text) for text in new_tickets]
                pprint(predictions, sort_dicts=False)
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "markdown",
            "id": "ai-explainability",
            "metadata": {},
            "source": textwrap.dedent("""\
                ## 7. Inspect what the text model learned

                A linear model associates learned word features with each class. The
                weights are a useful debugging aid, not a causal explanation or guarantee
                that a prediction is fair. Check for spurious shortcuts and data leakage.
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "code",
            "id": "ai-feature-weights",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": textwrap.dedent("""\
                tfidf = model.named_steps["tfidfvectorizer"]
                classifier = model.named_steps["logisticregression"]
                feature_names = tfidf.get_feature_names_out()
                urgent_weights = classifier.coef_[0]

                most_urgent = sorted(
                    zip(urgent_weights, feature_names), reverse=True
                )[:10]
                most_routine = sorted(
                    zip(urgent_weights, feature_names)
                )[:10]
                print("Features associated with urgent:")
                print([feature for _weight, feature in most_urgent])
                print("Features associated with routine:")
                print([feature for _weight, feature in most_routine])
                """).splitlines(keepends=True),
        },
        {
            "cell_type": "markdown",
            "id": "ai-limitations",
            "metadata": {},
            "source": textwrap.dedent(f"""\
                ## What this example does—and does not—show

                This is a complete **small supervised-learning workflow**, an important
                branch of AI: labeled data → train/test split → feature extraction → model
                fitting → held-out evaluation → inference. The classifier learns patterns
                from examples; it is more than a hand-authored `if` statement.

                It is not a general reasoning system. The tiny synthetic dataset cannot
                represent real language, class imbalance, changing behavior, or the costs
                of mistakes. Do not deploy it for actual safety triage. A responsible
                system needs reviewed representative data, privacy controls, stronger
                evaluation, monitored human review, and a tested escalation process.

                **Exercises**

                1. Add several labeled examples of your own, retrain, and note the test
                   metrics. With this small sample, metrics will vary as the dataset changes.
                2. Inspect every false negative. Which one would have the highest impact?
                3. Change the human-review threshold and explain the precision/recall trade-off.
                4. Compare a rule, this learned classifier, and a language-model approach:
                   what data, latency, explainability, and failure controls would each need?

                Continue with the [AI concept guide](../guides/concepts/{guide_name}) and the
                [learning roadmap](../guides/ROADMAP.md).
                """).splitlines(keepends=True),
        },
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11+"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> None:
    """Generate guides, notebooks, and roadmap from the single topic registry."""
    concepts = ROOT / "guides" / "concepts"
    notebooks = ROOT / "notebooks"
    concepts.mkdir(parents=True, exist_ok=True)
    notebooks.mkdir(parents=True, exist_ok=True)
    topics_by_slug = {topic[0]: topic for topic in TOPICS}
    if len(topics_by_slug) != len(TOPICS) or set(topics_by_slug) != set(LEARNING_ORDER):
        raise ValueError("LEARNING_ORDER must contain every topic exactly once")
    # Fail before writing files if any topic would have only a shallow fallback
    # or no lesson at all; this protects the repository's runnable-depth promise.
    covered_topics = set(LESSONS) | {
        "ollama",
        "openai",
        "gemini",
        "anthropic",
        "docker-model-runner",
        "amazon-sagemaker",
        "amazon-bedrock",
        "ai",
    }
    if covered_topics != set(topics_by_slug):
        raise ValueError(
            f"Every concept needs a comprehensive lesson; "
            f"missing={sorted(set(topics_by_slug) - covered_topics)}, "
            f"unknown={sorted(covered_topics - set(topics_by_slug))}"
        )

    for sequence, slug in enumerate(LEARNING_ORDER, start=1):
        topic = topics_by_slug[slug]
        prefix = f"{sequence:03d}"
        guide_name = f"{prefix}-{slug}.md"
        notebook_name = f"{prefix}-{slug}.ipynb"
        (concepts / guide_name).write_text(
            build_guide(topic, notebook_name), encoding="utf-8"
        )
        (notebooks / notebook_name).write_text(
            json.dumps(build_notebook(topic, guide_name), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    (ROOT / "guides" / "ROADMAP.md").write_text(
        build_roadmap(topics_by_slug), encoding="utf-8"
    )
    expected_stems = {
        f"{sequence:03d}-{slug}"
        for sequence, slug in enumerate(LEARNING_ORDER, start=1)
    }
    for folder, suffix in ((concepts, ".md"), (notebooks, ".ipynb")):
        for stale_path in folder.glob(f"[0-9][0-9][0-9]-*{suffix}"):
            if stale_path.stem not in expected_stems:
                # Remove only numbered generated assets absent from the current
                # catalog; hand-authored files and unrelated files stay intact.
                stale_path.unlink()

    for slug in topics_by_slug:
        for stale_path in (concepts / f"{slug}.md", notebooks / f"{slug}.ipynb"):
            if stale_path.exists():
                stale_path.unlink()
    print(f"Generated {len(LEARNING_ORDER)} numbered concept guides and notebooks.")


if __name__ == "__main__":
    main()
