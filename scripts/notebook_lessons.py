"""Runnable, offline implementations used to expand each concept notebook."""

from __future__ import annotations

from typing import NamedTuple


class LessonStep(NamedTuple):
    heading: str
    explanation: str
    code: str


def step(heading: str, explanation: str, code: str) -> LessonStep:
    return LessonStep(heading, explanation, code.strip("\n"))


LESSONS: dict[str, list[LessonStep]] = {
    "python-for-ai": [
        step("1. Load and inspect tabular data", "AI work starts with understanding the shape, types, and missing values in the input—not immediately calling a model.", """
import numpy as np

measurements = np.array([
    [20.1, 0.10], [19.8, 0.12], [21.0, 0.08], [20.6, 0.11],
    [23.4, 0.35], [24.0, 0.40], [22.9, 0.32], [23.8, 0.38],
])
labels = np.array(["normal"] * 4 + ["overheating"] * 4)
print("shape:", measurements.shape)
print("feature means:", measurements.mean(axis=0))
print("labels:", np.unique(labels, return_counts=True))
"""),
        step("2. Fit a small predictive pipeline", "A scikit-learn pipeline scales numeric inputs and trains a classifier. Splitting first prevents the scaler from learning from test rows.", """
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

X_train, X_test, y_train, y_test = train_test_split(
    measurements, labels, test_size=0.25, random_state=5, stratify=labels
)
model = make_pipeline(StandardScaler(), LogisticRegression(random_state=5))
model.fit(X_train, y_train)
predictions = model.predict(X_test)
print("predictions:", predictions.tolist())
"""),
        step("3. Measure performance and inspect an example", "Use a held-out score and inspect the model output. In real work, also check class-specific errors, calibration, drift, and the cost of mistakes.", """
from sklearn.metrics import accuracy_score, confusion_matrix

print("held-out accuracy:", accuracy_score(y_test, predictions))
print("confusion matrix:")
print(confusion_matrix(y_test, predictions, labels=model.classes_))
new_reading = np.array([[23.2, 0.34]])
print("new reading prediction:", model.predict(new_reading)[0])
"""),
    ],
    "ml": [
        step("1. Create labeled examples and split them", "Use a small, deterministic dataset and reserve a stratified test split before fitting any learned transform.", """
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

X, y = make_classification(
    n_samples=400, n_features=6, n_informative=4, n_redundant=0,
    class_sep=1.2, random_state=17,
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=17
)
print("train/test:", X_train.shape, X_test.shape)
"""),
        step("2. Fit a preprocessing-and-model pipeline", "Scaling is learned on the training data only because it is inside the pipeline.", """
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

model = make_pipeline(StandardScaler(), LogisticRegression(random_state=17))
model.fit(X_train, y_train)
predictions = model.predict(X_test)
print("learned classes:", model.classes_)
"""),
        step("3. Compare with a baseline", "Accuracy alone can hide class-specific failures. Compare with a majority-class baseline and inspect precision, recall, and the confusion matrix.", """
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
baseline_predictions = baseline.predict(X_test)
print(f"model accuracy: {accuracy_score(y_test, predictions):.3f}")
print(f"baseline accuracy: {accuracy_score(y_test, baseline_predictions):.3f}")
print(classification_report(y_test, predictions, zero_division=0))
print("confusion matrix:")
print(confusion_matrix(y_test, predictions))
"""),
    ],
    "cnn": [
        step("1. Create tiny labeled images", "Synthetic 5-by-5 images contain a vertical scratch, horizontal scratch, or no defect. They make convolution visible without downloads.", """
import numpy as np

def make_image(kind):
    image = np.zeros((5, 5), dtype=float)
    if kind == "vertical":
        image[:, 2] = 1
    elif kind == "horizontal":
        image[2, :] = 1
    elif kind != "clean":
        raise ValueError(f"unknown kind: {kind}")
    return image

labels = ["vertical", "horizontal", "clean"]
images = np.stack([make_image(label) for label in labels])
print("batch shape:", images.shape)
print(images[0])
"""),
        step("2. Convolve with a shared edge filter", "Slide the same small kernel across each image: weight sharing detects local patterns wherever they occur.", """
vertical_kernel = np.array([[-1, 2, -1], [-1, 2, -1], [-1, 2, -1]], dtype=float)

def convolve2d(image, kernel):
    height, width = image.shape
    kh, kw = kernel.shape
    output = np.zeros((height - kh + 1, width - kw + 1))
    for row in range(output.shape[0]):
        for col in range(output.shape[1]):
            output[row, col] = np.sum(image[row:row + kh, col:col + kw] * kernel)
    return output

feature_maps = [convolve2d(image, vertical_kernel) for image in images]
print("vertical responses:", [round(float(fmap.max()), 1) for fmap in feature_maps])
"""),
        step("3. Pool and classify by strongest evidence", "Global max pooling compresses each feature map. This hand-built detector illustrates a CNN component, not a trained deep network.", """
scores = [float(fmap.max()) for fmap in feature_maps]
predictions = [
    "vertical" if score > 0 else "not-vertical"
    for score in scores
]
for label, score, prediction in zip(labels, scores, predictions):
    print(f"true={label:10s} feature={score:4.1f} detector={prediction}")
"""),
    ],
    "rnn": [
        step("1. Encode a sequence", "A recurrent network consumes one timestep at a time. This toy sequence contains a persistent signal followed by a change.", """
import numpy as np

sequence = np.array([0.9, 0.8, 0.7, 0.1, 0.0], dtype=float)
print("timesteps:", len(sequence), "values:", sequence)
"""),
        step("2. Run a simple recurrent cell", "At each step, the hidden state mixes the new input with the previous state. Parameters are fixed here so the recurrence is easy to inspect.", """
def run_rnn(values, input_weight=0.8, recurrent_weight=0.5):
    state = 0.0
    states = []
    for value in values:
        state = np.tanh(input_weight * value + recurrent_weight * state)
        states.append(state)
    return np.array(states)

hidden_states = run_rnn(sequence)
print("hidden states:", np.round(hidden_states, 3))
"""),
        step("3. Use the final state as a summary", "A real RNN learns its weights from examples. Here, threshold the final state and inspect how a sequential summary differs from classifying each input alone.", """
threshold = 0.25
summary_prediction = "signal" if hidden_states[-1] > threshold else "no-signal"
print("last raw value:", sequence[-1])
print("last hidden state:", round(float(hidden_states[-1]), 3))
print("sequence-level prediction:", summary_prediction)
"""),
    ],
    "tf": [
        step("1. Tokenize a document", "Term frequency starts with counting tokens in each document; this lesson uses a tiny support-ticket corpus.", """
import re
from collections import Counter

documents = [
    "reset password reset account",
    "account billing question",
    "password reset failed again",
]
tokenized = [re.findall(r"[a-z]+", doc.lower()) for doc in documents]
counts = [Counter(tokens) for tokens in tokenized]
print("first document counts:", counts[0])
"""),
        step("2. Compare raw and normalized term frequency", "Raw count grows with document length. Dividing by length gives a simple length-normalized alternative.", """
term = "reset"
for index, (tokens, counter) in enumerate(zip(tokenized, counts), start=1):
    raw = counter[term]
    normalized = raw / len(tokens)
    print(f"doc {index}: count={raw}, normalized_tf={normalized:.3f}")
"""),
        step("3. Inspect the document-term matrix", "A fixed vocabulary maps each token to a consistent column so term counts can be compared across documents.", """
vocabulary = sorted({token for tokens in tokenized for token in tokens})
term_matrix = [
    [counter[token] for token in vocabulary]
    for counter in counts
]
print("columns:", vocabulary)
for row in term_matrix:
    print(row)
"""),
    ],
    "idf": [
        step("1. Build document frequencies", "Document frequency counts how many documents contain a term, not how many times it appears overall.", """
import math
import re
from collections import Counter

documents = [
    "reset password reset account",
    "account billing question",
    "password reset failed again",
    "account access help",
]
token_sets = [set(re.findall(r"[a-z]+", doc.lower())) for doc in documents]
document_frequency = Counter(term for terms in token_sets for term in terms)
print("document count:", len(documents))
print("document frequencies:", document_frequency)
"""),
        step("2. Calculate smoothed IDF", "Smoothing avoids division by zero and keeps IDF finite; frequent terms receive lower weights.", """
N = len(documents)
idf = {
    term: math.log((1 + N) / (1 + frequency)) + 1
    for term, frequency in document_frequency.items()
}
for term in ("account", "reset", "billing"):
    print(f"{term:8s} df={document_frequency[term]} idf={idf[term]:.3f}")
"""),
        step("3. Explain a query-weighting consequence", "A rare billing term is more discriminative in this corpus than a common account term; this depends on the collection.", """
query = ["account", "billing"]
query_weights = {term: idf[term] for term in query}
print("query weights:", query_weights)
assert query_weights["billing"] > query_weights["account"]
"""),
    ],
    "lstm": [
        step("1. Define the LSTM gates", "An LSTM keeps a cell memory and hidden state. Sigmoid gates choose what to forget, write, and expose.", """
import numpy as np

def sigmoid(values):
    return 1 / (1 + np.exp(-np.asarray(values, dtype=float)))

def lstm_step(x, h_previous, c_previous, parameters):
    gates = parameters["W"] @ np.array([x, h_previous]) + parameters["b"]
    forget, write, candidate, expose = np.split(gates, 4)
    forget, write, expose = sigmoid(forget), sigmoid(write), sigmoid(expose)
    candidate = np.tanh(candidate)
    cell = forget * c_previous + write * candidate
    hidden = expose * np.tanh(cell)
    return hidden.item(), cell.item()
"""),
        step("2. Process a sequence with memory", "Small fixed weights make the gates executable and inspectable. Training weights is a separate optimization task.", """
parameters = {
    "W": np.array([
        [0.4, 0.2], [0.7, 0.1], [0.8, -0.2], [0.5, 0.3],
    ]),
    "b": np.zeros(4),
}
values = [1.0, 0.0, 0.0, 0.0, 0.0]
h, c = 0.0, 0.0
history = []
for timestep, value in enumerate(values):
    h, c = lstm_step(value, h, c, parameters)
    history.append((timestep, value, round(h, 3), round(c, 3)))
print("step, input, hidden, cell:", history)
"""),
        step("3. Compare retained cell memory", "The cell state carries information separately from the exposed hidden state, helping gradients and information persist over longer sequences.", """
print("final cell memory:", history[-1][3])
assert np.isfinite(history[-1][3])
print("The weights are illustrative; a real LSTM learns them from sequence data.")
"""),
    ],
    "tf-idf": [
        step("1. Construct a tiny document-term matrix", "TF-IDF combines within-document term frequency with collection-wide inverse document frequency.", """
from sklearn.feature_extraction.text import TfidfVectorizer

documents = [
    "reset password reset account",
    "account billing address",
    "password reset failed",
]
vectorizer = TfidfVectorizer(norm=None, smooth_idf=True)
matrix = vectorizer.fit_transform(documents)
terms = vectorizer.get_feature_names_out()
print("terms:", list(terms))
print("matrix shape:", matrix.shape)
"""),
        step("2. Inspect TF-IDF weights", "Common terms are discounted relative to terms concentrated in fewer documents. Exact values depend on the vectorizer's TF and smoothing conventions.", """
for document_index, row in enumerate(matrix.toarray(), start=1):
    weighted_terms = {
        term: round(float(weight), 3)
        for term, weight in zip(terms, row)
        if weight
    }
    print(f"document {document_index}:", weighted_terms)
"""),
        step("3. Rank documents for a query", "Cosine similarity compares query and document vectors; normalization makes it less sensitive to document length.", """
from sklearn.metrics.pairwise import cosine_similarity

query_vector = vectorizer.transform(["password reset"])
scores = cosine_similarity(query_vector, matrix).ravel()
ranking = scores.argsort()[::-1]
for index in ranking:
    print(f"score={scores[index]:.3f}  {documents[index]}")
"""),
    ],
    "vectorization": [
        step("1. Fit a bag-of-words representation", "A vectorizer learns a vocabulary from training text and maps each document to a sparse numeric feature vector.", """
from sklearn.feature_extraction.text import CountVectorizer

train_documents = [
    "battery lasts all day",
    "battery will not charge",
    "delivery arrived today",
]
vectorizer = CountVectorizer(ngram_range=(1, 2))
X_train = vectorizer.fit_transform(train_documents)
print("vocabulary:", vectorizer.get_feature_names_out().tolist())
print("matrix shape:", X_train.shape, "nonzeros:", X_train.nnz)
"""),
        step("2. Transform unseen text without changing the vocabulary", "Use `transform`, not `fit_transform`, on evaluation or production text to avoid data leakage.", """
new_document = ["battery charge issue"]
X_new = vectorizer.transform(new_document)
print("new vector:", X_new.toarray())
print("unseen token is ignored; vocabulary stays fixed:", len(vectorizer.vocabulary_))
"""),
        step("3. Compare representations", "Counts retain frequency; binary features retain presence only. Choose based on data and evaluation.", """
from sklearn.feature_extraction.text import CountVectorizer

binary_vectorizer = CountVectorizer(binary=True)
binary_matrix = binary_vectorizer.fit_transform(["reset reset password"])
count_matrix = CountVectorizer().fit_transform(["reset reset password"])
print("binary:", binary_matrix.toarray().tolist())
print("counts:", count_matrix.toarray().tolist())
"""),
    ],
    "transformers": [
        step("1. Prepare query, key, and value vectors", "Self-attention compares a query with keys, then uses the resulting weights to mix values.", """
import numpy as np

tokens = ["the", "charger", "smokes"]
Q = np.array([[1.0, 0.0], [0.0, 1.0], [0.9, 0.1]])
K = Q.copy()
V = np.array([[0.1, 0.0], [0.0, 1.0], [1.0, 0.2]])
print("token count:", len(tokens), "embedding width:", Q.shape[1])
"""),
        step("2. Compute scaled dot-product attention", "Softmax turns scaled compatibility scores into weights. Each row says how much one token reads from every other token.", """
def softmax(values, axis=-1):
    shifted = values - values.max(axis=axis, keepdims=True)
    weights = np.exp(shifted)
    return weights / weights.sum(axis=axis, keepdims=True)

scores = Q @ K.T / np.sqrt(K.shape[1])
weights = softmax(scores)
context = weights @ V
print("attention weights:")
print(np.round(weights, 2))
print("context vectors:")
print(np.round(context, 2))
"""),
        step("3. Apply a causal mask", "A decoder-only language model must not look at future tokens when predicting the next token.", """
causal_mask = np.triu(np.ones_like(scores, dtype=bool), k=1)
masked_scores = np.where(causal_mask, -1e9, scores)
causal_weights = softmax(masked_scores)
print("causal weights:")
print(np.round(causal_weights, 2))
assert np.allclose(causal_weights[0, 1:], 0)
"""),
    ],
    "bert": [
        step("1. Represent a masked-token prediction task", "BERT's masked-language modeling objective predicts a hidden token using context on both its left and right.", """
import re
from collections import Counter, defaultdict

sentences = [
    "the battery lasts all day",
    "the battery charges quickly",
    "the screen looks bright",
    "the screen stays bright",
    "the battery feels warm",
]
tokens = [re.findall(r"[a-z]+", sentence) for sentence in sentences]
print("sample:", tokens[0])
"""),
        step("2. Learn a toy bidirectional context table", "For each center word, count neighboring words on both sides. This is a transparent miniature, not a Transformer or pretrained BERT.", """
context_counts = defaultdict(Counter)
for sentence in tokens:
    for index in range(1, len(sentence) - 1):
        context = (sentence[index - 1], sentence[index + 1])
        context_counts[context][sentence[index]] += 1

context = ("the", "lasts")
print("context:", context, "candidates:", context_counts[context])
"""),
        step("3. Predict a masked token from both sides", "Score vocabulary candidates with their observed left/right context pair and report when the training corpus has no matching evidence.", """
def predict_mask(left, right):
    candidates = context_counts[(left, right)]
    if not candidates:
        return []
    return candidates.most_common()

print("[the] battery [lasts] ->", predict_mask("the", "lasts"))
print("[the] screen [charges] ->", predict_mask("the", "charges"))
"""),
    ],
    "gpt": [
        step("1. Build a next-token training corpus", "GPT-style decoder-only models learn to predict the next token from the prefix. This miniature uses a token bigram model.", """
from collections import Counter, defaultdict
from itertools import pairwise

corpus = [
    "small models learn patterns",
    "large models learn language patterns",
    "language models predict the next token",
    "models predict one token at a time",
]
transitions = defaultdict(Counter)
for sentence in corpus:
    words = ["<BOS>", *sentence.split(), "<EOS>"]
    for current, following in pairwise(words):
        transitions[current][following] += 1
print("transitions from 'models':", transitions["models"])
"""),
        step("2. Implement next-token prediction", "Choose the most frequent successor for a deterministic demonstration. A trained GPT uses learned neural-network scores and sampling.", """
def next_token(prefix):
    current = prefix.split()[-1] if prefix.split() else "<BOS>"
    choices = transitions[current]
    if not choices:
        return "<EOS>"
    return choices.most_common(1)[0][0]

print("after 'language':", next_token("language"))
print("after 'models':", next_token("models"))
"""),
        step("3. Generate autoregressively", "Feed each generated token back as context, stopping at an end token or the maximum length.", """
def generate(prompt, max_tokens=8):
    generated = prompt.split()
    for _ in range(max_tokens):
        token = next_token(" ".join(generated))
        if token == "<EOS>":
            break
        generated.append(token)
    return " ".join(generated)

print(generate("language models"))
"""),
    ],
    "generative-ai": [
        step("1. Prepare approved source material", "Generative systems should receive a bounded task and source material; distinguish grounded facts from invented phrasing.", """
product = {
    "name": "TrailLight 2",
    "battery_hours": 12,
    "materials": ["recycled aluminum", "silicone"],
    "approved_claims": ["weather resistant"],
}
print(product)
"""),
        step("2. Build a constrained generation prompt", "A prompt sets role, allowed evidence, output format, and constraints. A prompt alone cannot guarantee correctness.", """
def build_prompt(product):
    return f\"\"\"Write a short product description using only these approved facts.
Name: {product['name']}
Battery: {product['battery_hours']} hours
Materials: {', '.join(product['materials'])}
Approved claims: {', '.join(product['approved_claims'])}
Do not add unsupported specifications. Return two sentences.\"\"\"

prompt = build_prompt(product)
print(prompt)
"""),
        step("3. Validate generated claims against evidence", "This deterministic renderer is a safe offline stand-in for a generator. Validate factual fields independently rather than trusting polished language.", """
draft = (
    f\"{product['name']} runs for up to {product['battery_hours']} hours. \"
    f\"It uses {product['materials'][0]} and is {product['approved_claims'][0]}.\"
)
required_facts = [product["name"], f"{product['battery_hours']} hours", *product["approved_claims"]]
unsupported = [fact for fact in required_facts if fact.lower() not in draft.lower()]
print(draft)
print("missing approved facts:", unsupported)
assert not unsupported
"""),
    ],
    "llm": [
        step("1. Train a tiny language model", "A language model learns a probability distribution over the next token. A smoothed bigram table is small enough to inspect.", """
from collections import Counter, defaultdict
from itertools import pairwise

training_text = [
    "retrieval finds useful evidence",
    "language models generate text",
    "retrieval helps language models",
    "evidence supports grounded answers",
]
bigram_counts = defaultdict(Counter)
unigram_counts = Counter()
for sentence in training_text:
    words = ["<BOS>", *sentence.split(), "<EOS>"]
    unigram_counts.update(words[:-1])
    for left, right in pairwise(words):
        bigram_counts[left][right] += 1
vocabulary = sorted(set(unigram_counts) | {"<EOS>"})
print("vocabulary size:", len(vocabulary))
"""),
        step("2. Compute next-token probabilities", "Additive smoothing assigns nonzero probability to unseen transitions; neural LLMs use far richer learned representations.", """
def next_token_distribution(context, alpha=0.2):
    current = context.split()[-1] if context.split() else "<BOS>"
    counts = bigram_counts[current]
    denominator = sum(counts.values()) + alpha * len(vocabulary)
    return {
        token: (counts[token] + alpha) / denominator
        for token in vocabulary
    }

distribution = next_token_distribution("language models")
print(sorted(distribution.items(), key=lambda item: -item[1])[:5])
"""),
        step("3. Generate with a bounded context window", "Generation repeatedly samples/chooses a next token. Bound output length and handle an end token; production LLMs also enforce token and tool limits.", """
import random

def generate_text(prompt, max_tokens=10, seed=3):
    rng = random.Random(seed)
    words = prompt.split()
    for _ in range(max_tokens):
        distribution = next_token_distribution(" ".join(words))
        tokens, probabilities = zip(*distribution.items())
        token = rng.choices(tokens, weights=probabilities, k=1)[0]
        if token == "<EOS>":
            break
        words.append(token)
    return " ".join(words)

print(generate_text("retrieval helps", max_tokens=8))
"""),
    ],
    "embeddings": [
        step("1. Represent items as vectors", "Real text embeddings are learned dense vectors. For a transparent offline example, define small vectors that encode a toy set of product concepts.", """
import numpy as np

items = {
    "car": np.array([0.95, 0.05, 0.0]),
    "automobile": np.array([0.90, 0.10, 0.0]),
    "truck": np.array([0.82, 0.18, 0.0]),
    "pasta recipe": np.array([0.0, 0.05, 0.95]),
}
"""),
        step("2. Compare with cosine similarity", "Cosine similarity compares direction and is commonly used for normalized embeddings.", """
def cosine_similarity(left, right):
    denominator = np.linalg.norm(left) * np.linalg.norm(right)
    if denominator == 0:
        raise ValueError("cosine similarity is undefined for a zero vector")
    return float(np.dot(left, right) / denominator)

query = items["automobile"]
scores = {name: cosine_similarity(query, vector) for name, vector in items.items()}
print(sorted(scores.items(), key=lambda pair: -pair[1]))
"""),
        step("3. Check vector contracts", "A production embedding index requires a consistent model, vector dimension, normalization convention, and version across queries and documents.", """
dimensions = {vector.shape for vector in items.values()}
print("vector shapes:", dimensions)
assert dimensions == {(3,)}
print("These hand-authored vectors are illustrative, not semantic model embeddings.")
"""),
    ],
    "full-text-search": [
        step("1. Build an inverted index", "An inverted index maps each normalized token to the documents containing it.", """
import re
from collections import defaultdict

documents = {
    "manual-1": "Reset the account password from account settings",
    "manual-2": "If error E1042 appears, restart the device",
    "manual-3": "Contact support to restore a locked account",
}
index = defaultdict(set)
for document_id, text in documents.items():
    for token in set(re.findall(r"[a-z0-9]+", text.lower())):
        index[token].add(document_id)
print("indexed terms:", len(index))
"""),
        step("2. Search with AND and OR semantics", "Intersect postings for AND; union postings for OR. Real search engines add stemming, ranking, syntax, and language processing.", """
def search(query, mode="AND"):
    terms = re.findall(r"[a-z0-9]+", query.lower())
    if not terms:
        return set()
    postings = [index.get(term, set()) for term in terms]
    if mode == "AND":
        return set.intersection(*postings)
    if mode == "OR":
        return set.union(*postings)
    raise ValueError("mode must be AND or OR")

print("AND:", search("account password"))
print("OR:", search("account E1042", mode="OR"))
"""),
        step("3. Rank matching documents", "A simple overlap score helps order results. Use BM25 or a production search engine when collection size and relevance requirements grow.", """
def ranked_search(query):
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    scores = {
        document_id: sum(document_id in index[term] for term in terms)
        for document_id in documents
    }
    return sorted(
        ((score, document_id) for document_id, score in scores.items() if score),
        reverse=True,
    )

print(ranked_search("account password"))
"""),
    ],
    "bm25": [
        step("1. Tokenize the corpus and calculate statistics", "BM25 combines query-term frequency, inverse document frequency, and document-length normalization.", """
import math
import re
from collections import Counter

documents = {
    "a": "reset password from account settings",
    "b": "account billing address update",
    "c": "reset password reset account password",
}
tokens = {key: re.findall(r"[a-z]+", text.lower()) for key, text in documents.items()}
average_length = sum(map(len, tokens.values())) / len(tokens)
document_frequency = Counter(
    term for words in tokens.values() for term in set(words)
)
print("average document length:", average_length)
"""),
        step("2. Implement BM25 scoring", "The usual IDF variant below stays positive for rare terms; `k1` controls term-frequency saturation and `b` controls length normalization.", """
def bm25(query, document_id, k1=1.5, b=0.75):
    query_terms = set(re.findall(r"[a-z]+", query.lower()))
    words = tokens[document_id]
    counts = Counter(words)
    score = 0.0
    for term in query_terms:
        frequency = counts[term]
        if not frequency:
            continue
        df = document_frequency[term]
        idf = math.log(1 + (len(documents) - df + 0.5) / (df + 0.5))
        norm = frequency + k1 * (1 - b + b * len(words) / average_length)
        score += idf * frequency * (k1 + 1) / norm
    return score
"""),
        step("3. Rank and inspect the results", "BM25 is lexical: exact terms and rare identifiers matter. Evaluate ranking quality on labeled queries rather than assuming a formula guarantees relevance.", """
query = "reset password"
ranking = sorted(
    ((bm25(query, document_id), document_id) for document_id in documents),
    reverse=True,
)
for score, document_id in ranking:
    print(f"{score:.3f} {document_id}: {documents[document_id]}")
"""),
    ],
    "semantic-search": [
        step("1. Build a small concept vector space", "Semantic retrieval relies on a trained embedding model. This offline toy encodes a known synonym relationship explicitly to demonstrate vector ranking.", """
import numpy as np

passages = {
    "car manual": np.array([0.95, 0.05, 0.0]),
    "truck manual": np.array([0.82, 0.18, 0.0]),
    "pasta recipe": np.array([0.0, 0.05, 0.95]),
}
query_text = "automobile instructions"
query_vector = np.array([0.92, 0.08, 0.0])
"""),
        step("2. Rank by vector similarity", "Compare each candidate by cosine similarity, not exact word overlap.", """
def cosine(left, right):
    return float(np.dot(left, right) / (np.linalg.norm(left) * np.linalg.norm(right)))

scores = {
    passage: cosine(query_vector, vector)
    for passage, vector in passages.items()
}
for passage, score in sorted(scores.items(), key=lambda pair: -pair[1]):
    print(f"{score:.3f}: {passage}")
"""),
        step("3. Understand evaluation and limitations", "The hand-assigned vectors make “automobile” close to “car”; actual embedding quality must be measured on relevant queries and judged results.", """
relevant = {"car manual", "truck manual"}
top_two = {name for name, _score in sorted(scores.items(), key=lambda pair: -pair[1])[:2]}
recall_at_2 = len(top_two & relevant) / len(relevant)
print(f"recall@2 on this toy query: {recall_at_2:.2f}")
print("Replace toy coordinates with embeddings from one fixed model in a real index.")
"""),
    ],
    "rrf": [
        step("1. Create independent ranked lists", "Lexical and vector systems produce ranks with incomparable score scales; RRF needs rank positions, not calibrated scores.", """
lexical_ranking = ["part-E1042", "charger-guide", "battery-care"]
vector_ranking = ["battery-care", "charger-guide", "warranty"]
"""),
        step("2. Implement reciprocal-rank fusion", "Each input list contributes 1/(k + rank). Deduplicate within each list so duplicate hits cannot inflate a result.", """
def reciprocal_rank_fusion(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, document_id in enumerate(dict.fromkeys(ranking), start=1):
            scores[document_id] = scores.get(document_id, 0.0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))

fused = reciprocal_rank_fusion([lexical_ranking, vector_ranking])
"""),
        step("3. Compare fused order", "A result ranked highly by multiple methods is often promoted. Tune candidate depth and evaluate RRF against each retrieval baseline.", """
for document_id, score in fused:
    print(f"{score:.4f} {document_id}")
assert fused[0][0] == "battery-care"
"""),
    ],
    "rag": [
        step("1. Build a source corpus", "RAG starts with evidence-bearing passages and source metadata, not a free-form answer.", """
documents = [
    {"id": "returns-v3#p2", "text": "Unused items can be returned within 30 days of delivery."},
    {"id": "shipping-v2#p1", "text": "Standard delivery usually takes 3 to 5 business days."},
    {"id": "warranty-v1#p4", "text": "The limited warranty lasts for one year."},
]
question = "How long is the return period?"
"""),
        step("2. Retrieve evidence before answering", "A simple lexical ranker keeps the lesson local and deterministic. Production retrieval should be tested for recall.", """
def retrieve(question, documents, k=2):
    terms = set(question.lower().split())
    ranked = []
    for document in documents:
        overlap = len(terms & set(document["text"].lower().replace(".", "").split()))
        ranked.append((overlap, document))
    return [document for score, document in sorted(ranked, key=lambda x: -x[0]) if score][:k]

evidence = retrieve(question, documents)
for passage in evidence:
    print(passage["id"], "->", passage["text"])
"""),
        step("3. Produce a grounded answer with citations", "This extractive answer does not call an LLM: it returns a relevant source sentence. Abstain when retrieval yields no evidence.", """
def grounded_answer(question, evidence):
    if not evidence:
        return {"answer": "I could not find supporting evidence.", "sources": []}
    return {
        "answer": evidence[0]["text"],
        "sources": [document["id"] for document in evidence],
    }

answer = grounded_answer(question, evidence)
print(answer)
assert answer["sources"]
"""),
    ],
    "knowledge-graphs": [
        step("1. Model facts as typed triples", "A knowledge graph stores subject–relation–object facts with explicit relation names.", """
triples = [
    ("Battery-B7", "installed_in", "Device-D1"),
    ("Device-D1", "uses_firmware", "Firmware-2.4"),
    ("Firmware-2.4", "affected_by", "Advisory-A9"),
    ("Battery-B7", "manufactured_by", "Maker-M3"),
]
"""),
        step("2. Query the graph", "A simple traversal illustrates graph queries; graph databases add indexes, query languages, and constraints.", """
def neighbors(entity, relation=None):
    return [
        (edge, target)
        for source, edge, target in triples
        if source == entity and (relation is None or edge == relation)
    ]

print("Device components:", neighbors("Battery-B7"))
device = neighbors("Battery-B7", "installed_in")[0][1]
firmware = neighbors(device, "uses_firmware")[0][1]
print("firmware advisories:", neighbors(firmware, "affected_by"))
"""),
        step("3. Answer a multi-hop question", "Relationships enable questions that require combining several facts; validate entity resolution and edge provenance in real graphs.", """
def advisories_for_component(component):
    devices = [target for relation, target in neighbors(component, "installed_in")]
    firmware = [
        fw for device_id in devices
        for relation, fw in neighbors(device_id, "uses_firmware")
    ]
    return [
        advisory
        for fw in firmware
        for relation, advisory in neighbors(fw, "affected_by")
    ]

print(advisories_for_component("Battery-B7"))
"""),
    ],
    "heuristic-search": [
        step("1. Define a weighted route-planning problem", "A* searches paths using cost so far plus a heuristic estimate to the goal.", """
import heapq

graph = {
    "A": {"B": 2, "C": 4},
    "B": {"C": 1, "D": 5},
    "C": {"D": 2},
    "D": {},
}
heuristic = {"A": 4, "B": 3, "C": 2, "D": 0}
"""),
        step("2. Implement A* with path reconstruction", "A priority queue expands the most promising node. The example heuristic never overestimates the remaining path cost.", """
def a_star(graph, start, goal, heuristic):
    frontier = [(heuristic[start], 0, start)]
    best_cost = {start: 0}
    parent = {}
    while frontier:
        _estimated_total, cost, node = heapq.heappop(frontier)
        if cost != best_cost[node]:
            continue
        if node == goal:
            path = [node]
            while node in parent:
                node = parent[node]
                path.append(node)
            return list(reversed(path)), cost
        for neighbor, edge_cost in graph[node].items():
            candidate = cost + edge_cost
            if candidate < best_cost.get(neighbor, float("inf")):
                best_cost[neighbor] = candidate
                parent[neighbor] = node
                heapq.heappush(
                    frontier, (candidate + heuristic[neighbor], candidate, neighbor)
                )
    return None, float("inf")
"""),
        step("3. Check the route and optimal cost", "With a nonnegative admissible heuristic, A* finds an optimal route. Changing the heuristic can change efficiency and correctness.", """
path, cost = a_star(graph, "A", "D", heuristic)
print("route:", path, "cost:", cost)
assert path == ["A", "B", "C", "D"] and cost == 5
"""),
    ],
    "graphrag": [
        step("1. Create source-linked entity facts", "GraphRAG represents entities and relationships extracted from source documents, retaining provenance for each edge.", """
edges = [
    {"source": "Team-R", "relation": "owns", "target": "Project-P", "doc": "plan-1"},
    {"source": "Project-P", "relation": "decided", "target": "Decision-7", "doc": "minutes-4"},
    {"source": "Decision-7", "relation": "caused", "target": "Incident-2", "doc": "review-2"},
    {"source": "Team-S", "relation": "supports", "target": "Project-Q", "doc": "plan-2"},
]
"""),
        step("2. Retrieve a relevant subgraph", "Start from a query-linked entity, expand a bounded number of hops, and carry source IDs along with facts.", """
def expand(seed, max_hops=2):
    frontier = {seed}
    seen = set(frontier)
    selected = []
    for _ in range(max_hops):
        next_frontier = set()
        for edge in edges:
            if edge["source"] in frontier:
                selected.append(edge)
                next_frontier.add(edge["target"])
        frontier = next_frontier - seen
        seen.update(frontier)
    return selected

subgraph = expand("Team-R", max_hops=3)
print("retrieved edges:", subgraph)
"""),
        step("3. Summarize with evidence", "A grounded response reports connected facts and source IDs. Graph completeness and extraction quality determine whether an answer can be trusted.", """
summary = [
    f"{edge['source']} {edge['relation']} {edge['target']} [source: {edge['doc']}]"
    for edge in subgraph
]
print("\\n".join(summary))
assert any(edge["target"] == "Incident-2" for edge in subgraph)
"""),
    ],
    "agents": [
        step("1. Define a goal and least-privilege tools", "An agent has a model or policy, task state, and explicitly permitted tools. Start with read-only operations.", """
from collections.abc import Callable
from dataclasses import dataclass

documents = {"returns": "Unused items may be returned within 30 days."}

def search_policy(topic: str) -> str:
    return documents.get(topic, "No matching policy found.")

def calculator(expression: str) -> float:
    allowed = {"2 + 2": 4.0, "10 * 3": 30.0}
    if expression not in allowed:
        raise ValueError("expression is not in this demo's allowlist")
    return allowed[expression]

tools: dict[str, Callable] = {
    "search_policy": search_policy,
    "calculator": calculator,
}
"""),
        step("2. Parse a plan and validate tool calls", "A real agent asks a model to select a tool. This offline plan demonstrates typed dispatch and rejects tools outside the allowlist.", """
@dataclass
class ToolCall:
    name: str
    arguments: dict[str, str]

def execute_tool(call: ToolCall):
    if call.name not in tools:
        raise PermissionError(f"tool is not permitted: {call.name}")
    return tools[call.name](**call.arguments)

planned_call = ToolCall("search_policy", {"topic": "returns"})
observation = execute_tool(planned_call)
print("observation:", observation)
"""),
        step("3. Produce a bounded, evidence-linked result", "The agent should report the tool result, not claim more than its evidence supports. Side effects require separate authorization.", """
answer = {
    "question": "What is the return window?",
    "evidence": observation,
    "answer": observation,
    "side_effects_performed": False,
}
print(answer)
"""),
    ],
    "agent-loop": [
        step("1. Define bounded state and tools", "An agent loop observes state, selects one permitted action, and stops on completion or a step budget.", """
state = {"goal": "find_return_window", "evidence": [], "status": "running"}
knowledge = {
    "returns": "Returns are accepted within 30 days.",
    "support": "Support is available on weekdays.",
}
tools = {"search": lambda key: knowledge.get(key, "No evidence found.")}
max_steps = 4
"""),
        step("2. Run observe–act–observe cycles", "This deterministic policy is executable without an LLM. A model can propose actions, but the application should still validate every action.", """
def choose_action(state):
    return "search:returns" if not state["evidence"] else "finish"

trace = []
for step_number in range(1, max_steps + 1):
    action = choose_action(state)
    trace.append({"step": step_number, "action": action})
    if action == "finish":
        state["status"] = "completed"
        break
    tool_name, argument = action.split(":", maxsplit=1)
    if tool_name not in tools:
        raise PermissionError(tool_name)
    result = tools[tool_name](argument)
    state["evidence"].append(result)
else:
    state["status"] = "limit_reached"
"""),
        step("3. Inspect the trace and stop condition", "A production loop needs timeouts, tool-call limits, input validation, and human approval before consequential actions.", """
print("trace:", trace)
print("final state:", state)
assert state["status"] == "completed"
"""),
    ],
    "multi-agent": [
        step("1. Give each role a narrow contract", "A multi-agent workflow can use specialist roles, but each role should have explicit inputs and outputs.", """
sources = [
    {"id": "policy-v3#p2", "text": "Unused items may be returned within 30 days."},
    {"id": "shipping-v2#p1", "text": "Standard delivery takes 3 to 5 business days."},
]

def researcher(question, source_documents):
    return [doc for doc in source_documents if "return" in doc["text"].lower()]
"""),
        step("2. Draft and independently verify", "Separate drafting from evidence checks to make unsupported claims easier to catch.", """
def writer(question, evidence):
    if not evidence:
        return {"answer": "I don't know.", "citations": []}
    return {"answer": evidence[0]["text"], "citations": [evidence[0]["id"]]}

def verifier(draft, source_documents):
    source_ids = {doc["id"] for doc in source_documents}
    valid_citations = all(source in source_ids for source in draft["citations"])
    return {
        "approved": valid_citations and bool(draft["citations"]),
        "citation_check": valid_citations,
    }

evidence = researcher("What is the return period?", sources)
draft = writer("What is the return period?", evidence)
review = verifier(draft, sources)
"""),
        step("3. Return a reviewed result", "The orchestrator owns the final stop/approval decision. Additional agents add cost and coordination overhead, not guaranteed correctness.", """
result = draft if review["approved"] else {
    "answer": "I could not verify an answer from the available sources.",
    "citations": [],
}
print({"result": result, "review": review})
"""),
    ],
    "langchain": [
        step("1. Define a composable chain contract", "A chain connects retrieval, prompt construction, model invocation, and output parsing. This offline implementation uses a deterministic model adapter.", """
documents = [
    {"id": "policy-1", "text": "Unused items may be returned within 30 days."},
    {"id": "policy-2", "text": "Support is open Monday through Friday."},
]

def retrieve(question):
    terms = set(question.lower().split())
    return [doc for doc in documents if terms & set(doc["text"].lower().replace(".", "").split())]

def format_prompt(question, evidence):
    return {"question": question, "context": [doc["text"] for doc in evidence]}
"""),
        step("2. Compose runnable stages", "Each stage accepts structured data and returns structured data; changing the model adapter does not require rewriting retrieval.", """
def offline_model(prompt):
    if not prompt["context"]:
        return "I don't know based on the provided evidence."
    return prompt["context"][0]

def parse_answer(text):
    return {"answer": text, "grounded": text != "I don't know based on the provided evidence."}

def run_chain(question):
    evidence = retrieve(question)
    prompt = format_prompt(question, evidence)
    return parse_answer(offline_model(prompt)), evidence
"""),
        step("3. Execute and inspect intermediate results", "The real LangChain version uses prompt templates and runnable composition; see `examples/integrations/langchain_example.py` for an optional provider-backed chain.", """
answer, evidence = run_chain("What is the return period?")
print("evidence:", evidence)
print("answer:", answer)
assert answer["grounded"]
"""),
        step("4. Optionally run the actual LangChain chain", "Install the `langchain` extra and set `OPENAI_API_KEY` before opting in. The deterministic chain above remains the default offline path.", """
RUN_LANGCHAIN = False
if RUN_LANGCHAIN:
    from examples.integrations.langchain_example import build_chain

    hosted_chain = build_chain()
    hosted_answer = hosted_chain.invoke({
        "question": "What is the return period?",
        "evidence": "Unused items may be returned within 30 days.",
    })
    print(hosted_answer)
else:
    print("Hosted LangChain call skipped; enable it only with credentials and reviewed data.")
"""),
    ],
    "langgraph": [
        step("1. Define explicit workflow state", "LangGraph models a workflow as nodes that transform shared state and edges that route execution.", """
from typing import TypedDict

class State(TypedDict):
    question: str
    evidence: list[str]
    approved: bool
    answer: str

initial_state: State = {
    "question": "What is the return window?",
    "evidence": ["Returns are accepted within 30 days."],
    "approved": False,
    "answer": "",
}
"""),
        step("2. Implement nodes and conditional transitions", "The small runner below makes nodes and transitions visible without requiring network access or framework setup.", """
def draft_node(state):
    if not state["evidence"]:
        return {**state, "answer": "I don't know."}
    return {**state, "answer": state["evidence"][0]}

def route_after_draft(state):
    return "finish" if state["approved"] else "human_review"

def run_graph(state):
    state = draft_node(state)
    route = route_after_draft(state)
    if route == "human_review":
        state = {**state, "answer": f"REVIEW REQUIRED: {state['answer']}"}
    return state, route
"""),
        step("3. Run the graph and inspect the branch", "For a real LangGraph workflow, add checkpointing and resume at the approval node; `examples/integrations/langgraph_example.py` demonstrates its optional framework API.", """
result, route = run_graph(initial_state)
print("route:", route)
print("state:", result)
assert route == "human_review"
"""),
        step("4. Optionally run a LangGraph implementation", "Install the `langgraph` extra to run the same approval branch with the framework's state graph.", """
RUN_LANGGRAPH = False
if RUN_LANGGRAPH:
    from examples.integrations.langgraph_example import build_workflow

    workflow_result = build_workflow().invoke({
        "approved": False, "action": "send_email", "status": "new"
    })
    print(workflow_result)
else:
    print("Framework call skipped; the local state graph above runs offline.")
"""),
    ],
    "langsmith": [
        step("1. Represent a run as a trace", "Tracing records inputs, outputs, timing, and errors for each component in an LLM application.", """
from dataclasses import dataclass, field
from time import perf_counter

@dataclass
class Trace:
    name: str
    inputs: dict
    outputs: dict = field(default_factory=dict)
    elapsed_ms: float = 0.0

def traced(name, function, **inputs):
    started = perf_counter()
    output = function(**inputs)
    return Trace(name, inputs, {"result": output}, (perf_counter() - started) * 1000)
"""),
        step("2. Trace retrieval and answer stages", "Separate spans identify whether a bad response started with retrieval or generation. This recorder is local; it does not send telemetry.", """
def search(query):
    return ["Returns are accepted within 30 days."] if "return" in query.lower() else []

def answer(context):
    return context[0] if context else "I don't know."

retrieval_trace = traced("retrieve", search, query="What is the return period?")
answer_trace = traced(
    "answer", answer, context=retrieval_trace.outputs["result"]
)
trace_tree = [retrieval_trace, answer_trace]
"""),
        step("3. Evaluate and inspect traces", "Dataset-based evaluation compares predictions with expected behavior; production monitoring should also capture latency and failure rates.", """
expected = "Returns are accepted within 30 days."
actual = answer_trace.outputs["result"]
evaluation = {"exact_match": actual == expected, "latency_ms": sum(t.elapsed_ms for t in trace_tree)}
for trace in trace_tree:
    print(trace.name, round(trace.elapsed_ms, 3), "ms", trace.outputs)
print("evaluation:", evaluation)
"""),
        step("4. Optionally send traces to LangSmith", "Install the `langsmith` extra and configure LangSmith tracing before opting in. Never send sensitive prompts or data without approval.", """
RUN_LANGSMITH = False
if RUN_LANGSMITH:
    from examples.integrations.langsmith_example import answer_from_evidence

    print(answer_from_evidence("return window", [expected]))
else:
    print("LangSmith tracing skipped; the trace above stayed local.")
"""),
    ],
    "llamaindex": [
        step("1. Split source documents into chunks", "LlamaIndex structures data for retrieval. This local example demonstrates chunk IDs and source metadata without an external model.", """
documents = [
    {"id": "policy-7", "text": "Unused products may be returned within 30 days. Keep the receipt."},
    {"id": "support-2", "text": "Support is open Monday through Friday."},
]

def chunk_text(text, size=7, overlap=2):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunks.append(" ".join(words[start:start + size]))
        start += size - overlap
    return chunks
"""),
        step("2. Build a simple metadata-aware index", "Keep the document ID attached to every chunk so retrieved evidence can be cited.", """
nodes = []
for document in documents:
    for index, chunk in enumerate(chunk_text(document["text"])):
        nodes.append({
            "node_id": f"{document['id']}#chunk-{index}",
            "document_id": document["id"],
            "text": chunk,
        })
print("indexed nodes:", nodes)
"""),
        step("3. Retrieve nodes and cite sources", "The actual LlamaIndex package can replace this simple overlap retriever; see `examples/integrations/llamaindex_example.py` for a credential-free framework demonstration.", """
def query_index(question, top_k=2):
    terms = set(question.lower().split())
    ranked = sorted(
        ((len(terms & set(node["text"].lower().split())), node) for node in nodes),
        key=lambda item: -item[0],
    )
    return [node for score, node in ranked[:top_k] if score > 0]

hits = query_index("return products 30 days")
print([{"source": hit["node_id"], "text": hit["text"]} for hit in hits])
"""),
        step("4. Optionally run the LlamaIndex framework", "Install the `llamaindex` extra to execute the framework version with mock embeddings and an offline mock language model.", """
RUN_LLAMAINDEX = False
if RUN_LLAMAINDEX:
    from examples.integrations.llamaindex_example import main as run_llamaindex

    run_llamaindex()
else:
    print("LlamaIndex framework call skipped; the local index above runs offline.")
"""),
    ],
    "fastapi": [
        step("1. Define a typed API over a service", "FastAPI turns typed Python functions into validated HTTP routes and an OpenAPI schema.", """
import asyncio

from fastapi import FastAPI, Query
from httpx import ASGITransport, AsyncClient

app = FastAPI(title="Offline Support Search Demo")
articles = [
    {"id": "a1", "title": "Password reset", "text": "Reset your password from account settings."},
    {"id": "a2", "title": "Returns", "text": "Unused products may be returned within 30 days."},
]
"""),
        step("2. Implement and validate an endpoint", "Bound query length and result count at the API boundary, then keep search logic in a small service function.", """
def search_articles(query):
    terms = set(query.lower().split())
    return [
        article for article in articles
        if terms & set((article["title"] + " " + article["text"]).lower().split())
    ]

@app.get("/search")
def search(q: str = Query(min_length=1, max_length=200), limit: int = Query(5, ge=1, le=20)):
    return {"query": q, "results": search_articles(q)[:limit]}
"""),
        step("3. Exercise HTTP success and validation paths", "An in-process ASGI client exercises request parsing without starting a server or opening a port.", """
async def exercise_api():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/search", params={"q": "password reset"})
        invalid_response = await client.get("/search", params={"q": ""})
    return response, invalid_response

response, invalid_response = asyncio.run(exercise_api())
print("success:", response.status_code, response.json())
print("invalid:", invalid_response.status_code)
assert response.status_code == 200 and invalid_response.status_code == 422
"""),
    ],
    "postgresql": [
        step("1. Design relational tables and constraints", "PostgreSQL transactions and constraints keep related application records consistent. This SQLite-backed exercise is runnable locally and uses compatible relational concepts.", """
import sqlite3

database = sqlite3.connect(":memory:")
database.execute("PRAGMA foreign_keys = ON")
database.executescript(\"\"\"
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 100),
    body TEXT NOT NULL
);
CREATE TABLE document_tags (
    document_id INTEGER NOT NULL REFERENCES documents(id),
    tag TEXT NOT NULL,
    PRIMARY KEY (document_id, tag)
);
\"\"\")
"""),
        step("2. Commit related writes atomically", "A transaction ensures a failed tag write cannot leave a partially saved document.", """
try:
    with database:
        cursor = database.execute(
            "INSERT INTO documents(title, body) VALUES (?, ?)",
            ("Password reset", "Reset from account settings."),
        )
        database.execute(
            "INSERT INTO document_tags(document_id, tag) VALUES (?, ?)",
            (cursor.lastrowid, "accounts"),
        )
except sqlite3.DatabaseError as error:
    raise RuntimeError("document transaction failed") from error

print(database.execute("SELECT id, title FROM documents").fetchall())
"""),
        step("3. Query and inspect the schema-backed result", "Use parameterized SQL for values. PostgreSQL adds production features such as `tsvector`, GIN indexes, JSONB, and concurrency controls.", """
rows = database.execute(
    \"\"\"
    SELECT documents.title, document_tags.tag
    FROM documents JOIN document_tags ON documents.id = document_tags.document_id
    WHERE document_tags.tag = ?
    \"\"\",
    ("accounts",),
).fetchall()
print(rows)
assert rows == [("Password reset", "accounts")]
"""),
    ],
    "qdrant": [
        step("1. Define a local in-memory vector collection", "Qdrant stores vectors with point IDs and payload metadata. The in-memory client is ephemeral and needs no server.", """
from qdrant_client import QdrantClient, models

client = QdrantClient(":memory:")
collection = "study_passages"
client.create_collection(
    collection_name=collection,
    vectors_config=models.VectorParams(size=3, distance=models.Distance.COSINE),
)
"""),
        step("2. Upsert vectors with source metadata", "Vector and payload are stored together; stable IDs make repeat upserts idempotent.", """
client.upsert(
    collection_name=collection,
    points=[
        models.PointStruct(id=1, vector=[0.9, 0.1, 0.0], payload={"text": "car repair guide", "access": "public"}),
        models.PointStruct(id=2, vector=[0.0, 0.1, 0.9], payload={"text": "pasta recipe", "access": "public"}),
        models.PointStruct(id=3, vector=[0.8, 0.2, 0.0], payload={"text": "truck service manual", "access": "staff"}),
    ],
    wait=True,
)
"""),
        step("3. Search with a payload filter", "A query vector must match the collection dimension. Apply metadata authorization filters during retrieval, not after returning data to a caller.", """
results = client.query_points(
    collection_name=collection,
    query=[0.95, 0.05, 0.0],
    query_filter=models.Filter(
        must=[models.FieldCondition(key="access", match=models.MatchValue(value="public"))]
    ),
    limit=3,
).points
print([(hit.id, round(hit.score, 3), hit.payload["text"]) for hit in results])
assert all(hit.payload["access"] == "public" for hit in results)
client.close()
"""),
    ],
    "transactional-outbox": [
        step("1. Create source and outbox tables", "The outbox stores the delivery request in the same database as application data.", """
import json
import sqlite3

database = sqlite3.connect(":memory:")
database.execute("PRAGMA foreign_keys = ON")
database.executescript(\"\"\"
CREATE TABLE documents(id TEXT PRIMARY KEY, body TEXT NOT NULL);
CREATE TABLE outbox(
    id INTEGER PRIMARY KEY,
    event_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0
);
\"\"\")
"""),
        step("2. Write the document and event in one transaction", "If either insert fails, the context manager rolls back both writes. Parameterized values prevent SQL injection.", """
document_id = "doc-1"
payload = {"document_id": document_id, "body": "Returns within 30 days"}
with database:
    database.execute(
        "INSERT INTO documents(id, body) VALUES (?, ?)",
        (document_id, payload["body"]),
    )
    database.execute(
        "INSERT INTO outbox(event_type, aggregate_id, payload) VALUES (?, ?, ?)",
        ("document.index", document_id, json.dumps(payload)),
    )
print("pending events:", database.execute("SELECT count(*) FROM outbox").fetchone()[0])
"""),
        step("3. Deliver idempotently and mark processed", "A worker may crash after delivery but before marking completion. A stable event/aggregate ID lets the destination upsert safely on retry.", """
indexed = {}
def process_event(event_id):
    row = database.execute(
        "SELECT aggregate_id, payload FROM outbox WHERE id=? AND status='pending'",
        (event_id,),
    ).fetchone()
    if row is None:
        return False
    aggregate_id, encoded = row
    event = json.loads(encoded)
    indexed[aggregate_id] = event["body"]  # idempotent upsert
    with database:
        database.execute(
            "UPDATE outbox SET status='processed', attempts=attempts+1 WHERE id=?",
            (event_id,),
        )
    return True

event_id = database.execute("SELECT id FROM outbox").fetchone()[0]
print("delivered:", process_event(event_id))
print("repeat is harmless:", process_event(event_id), "index:", indexed)
"""),
    ],
}

LESSONS.update(
    {
        "data-preparation": [
            step("1. Inspect raw records", "Check missing values and category variation before choosing transformations.", """
records = [
    {"temperature": 20.0, "status": "ok"},
    {"temperature": None, "status": "ok"},
    {"temperature": 24.0, "status": "warning"},
]
print("rows:", len(records))
print("missing temperatures:", sum(row["temperature"] is None for row in records))
print("statuses:", sorted({row["status"] for row in records}))
"""),
            step("2. Impute and encode deliberately", "Fit data-dependent transformations from the training records, and keep missingness as a potentially useful signal.", """
temperatures = [row["temperature"] for row in records]
observed = [value for value in temperatures if value is not None]
training_mean = sum(observed) / len(observed)
prepared = [
    {
        "temperature": value if value is not None else training_mean,
        "temperature_was_missing": value is None,
        "warning": row["status"] == "warning",
    }
    for row, value in zip(records, temperatures)
]
print(prepared)
"""),
            step("3. Separate features and target", "Keep targets out of inputs; for forecasting, split by time before deriving features or fitting imputers.", """
features = [
    [row["temperature"], float(row["temperature_was_missing"])]
    for row in prepared
]
target = [row["warning"] for row in prepared]
assert len(features) == len(target)
print("feature matrix:", features)
print("target:", target)
"""),
        ],
        "linear-algebra": [
            step("1. Represent data and parameters", "A feature vector describes one example; a weight vector represents a linear model.", """
import numpy as np

features = np.array([2.0, 3.0])
weights = np.array([0.4, -0.2])
bias = 0.1
print("feature shape:", features.shape, "weight shape:", weights.shape)
"""),
            step("2. Compute a dot product", "The dot product multiplies matching entries and sums their contributions to a score.", """
score = features @ weights + bias
manual_score = sum(value * weight for value, weight in zip(features, weights)) + bias
assert np.isclose(score, manual_score)
print("linear score:", score)
"""),
            step("3. Batch the same operation", "Rows of a matrix are examples; one matrix multiplication scores every row efficiently.", """
batch = np.array([[2.0, 3.0], [1.0, 4.0], [5.0, 1.0]])
scores = batch @ weights + bias
print("batch scores:", scores.round(2).tolist())
"""),
        ],
        "probability-statistics": [
            step("1. Summarize observations", "A sample mean and event rate summarize observed data but do not remove sampling uncertainty.", """
import numpy as np

readings = np.array([18.2, 19.1, 17.7, 20.0, 18.9])
print("mean:", round(float(readings.mean()), 2))
print("sample standard deviation:", round(float(readings.std(ddof=1)), 2))
"""),
            step("2. Estimate a probability", "An empirical probability is a frequency estimate; the estimate is less certain with few observations.", """
failures, trials = 3, 20
estimated_rate = failures / trials
print(f"estimated failure rate: {estimated_rate:.1%} from {trials} trials")
"""),
            step("3. Apply Bayes' rule", "Bayes' rule combines a prior event rate with evidence sensitivity and false-positive rate.", """
prior = 0.02
sensitivity = 0.90
false_positive_rate = 0.05
posterior = sensitivity * prior / (
    sensitivity * prior + false_positive_rate * (1 - prior)
)
print(f"probability of failure after a positive alert: {posterior:.1%}")
"""),
        ],
        "ml-evaluation": [
            step("1. Separate development from final testing", "Use validation data for choices and keep the test set untouched until the final assessment.", """
from sklearn.model_selection import train_test_split

X = [[value] for value in range(100)]
y = [int(value >= 70) for value in range(100)]
X_trainval, X_test, y_trainval, y_test = train_test_split(
    X, y, test_size=0.2, random_state=14, stratify=y
)
X_train, X_validation, y_train, y_validation = train_test_split(
    X_trainval, y_trainval, test_size=0.25, random_state=14, stratify=y_trainval
)
print("train:", len(X_train), "validation:", len(X_validation), "test:", len(X_test))
"""),
            step("2. Inspect class-sensitive metrics", "For rare failures, recall may matter more than overall accuracy; inspect the confusion matrix and precision-recall trade-off.", """
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score

baseline = DummyClassifier(strategy="most_frequent").fit(X_train, y_train)
validation_predictions = baseline.predict(X_validation)
print(confusion_matrix(y_validation, validation_predictions))
print(classification_report(y_validation, validation_predictions, zero_division=0))
cv_recall = cross_val_score(
    baseline, X_train, y_train, cv=3, scoring="recall"
)
print("training-only cross-validation recall:", cv_recall.round(2).tolist())
"""),
            step("3. Tune a threshold on validation data", "Pick a threshold to match operational costs using validation data, then report once on untouched test data.", """
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

model = make_pipeline(StandardScaler(), LogisticRegression()).fit(X_train, y_train)
validation_probabilities = model.predict_proba(X_validation)[:, 1]
threshold = 0.4
thresholded_validation = (validation_probabilities >= threshold).astype(int)
final_model = make_pipeline(StandardScaler(), LogisticRegression()).fit(X_trainval, y_trainval)
test_predictions = (final_model.predict_proba(X_test)[:, 1] >= threshold).astype(int)
print("validation positives:", int(thresholded_validation.sum()))
print("final test confusion matrix:")
print(confusion_matrix(y_test, test_predictions))
"""),
        ],
        "supervised-learning": [
            step("1. Prepare labeled examples", "Inputs are features and targets are known labels or values; keep examples independent and representative.", """
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

X, y = make_classification(
    n_samples=300, n_features=5, n_informative=3, n_redundant=0, random_state=4
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=4
)
print("training examples:", len(X_train))
"""),
            step("2. Train a classifier", "Classification predicts a category; preprocessing must be fitted only on training examples.", """
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

classifier = make_pipeline(StandardScaler(), LogisticRegression())
classifier.fit(X_train, y_train)
predictions = classifier.predict(X_test)
print("first predictions:", predictions[:8].tolist())
"""),
            step("3. Train a regression model", "Regression predicts a numeric quantity; use a metric such as mean absolute error in the target's units.", """
from sklearn.datasets import make_regression
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error

X_reg, y_reg = make_regression(n_samples=100, n_features=3, noise=10, random_state=4)
regressor = Ridge().fit(X_reg[:80], y_reg[:80])
print("held-out MAE:", round(mean_absolute_error(y_reg[80:], regressor.predict(X_reg[80:])), 2))
"""),
        ],
        "classical-models": [
            step("1. Create a reproducible dataset", "Keep the data split identical so model comparisons reflect modeling choices rather than different examples.", """
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split

X, y = make_moons(n_samples=300, noise=0.2, random_state=12)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=12
)
"""),
            step("2. Compare a linear model and a tree", "A linear decision boundary is simple; a tree can model nonlinear partitions but may overfit.", """
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

models = {
    "logistic": LogisticRegression(),
    "shallow_tree": DecisionTreeClassifier(max_depth=3, random_state=12),
}
for model in models.values():
    model.fit(X_train, y_train)
"""),
            step("3. Measure on held-out data", "Compare accuracy and complexity, and then inspect errors and robustness before choosing a model.", """
for name, model in models.items():
    print(name, "accuracy:", round(model.score(X_test, y_test), 3))
"""),
        ],
        "unsupervised-learning": [
            step("1. Create unlabeled data", "No target labels are supplied. Standardization can matter because distance-based methods are scale-sensitive.", """
import numpy as np
from sklearn.datasets import make_blobs
from sklearn.preprocessing import StandardScaler

X, hidden_groups = make_blobs(
    n_samples=120, centers=3, cluster_std=1.1, random_state=5
)
X_scaled = StandardScaler().fit_transform(X)
print("observed feature shape:", X_scaled.shape)
"""),
            step("2. Discover groups", "K-means assigns points to nearby centroids; the chosen number of clusters is an assumption, not discovered truth.", """
from sklearn.cluster import KMeans

clusterer = KMeans(n_clusters=3, n_init=10, random_state=5).fit(X_scaled)
cluster_ids = clusterer.labels_
print("cluster sizes:", np.bincount(cluster_ids).tolist())
"""),
            step("3. Inspect and qualify the result", "Compare clusters with domain knowledge and stability checks; do not treat synthetic hidden labels as available in real unsupervised work.", """
for cluster_id in range(3):
    center = X[cluster_ids == cluster_id].mean(axis=0)
    print(cluster_id, "original-unit center:", center.round(2).tolist())
"""),
            step("4. Reduce dimensionality with PCA", "Principal component analysis projects data onto directions that preserve variance; it is useful for compression and visualization, not automatically for better predictions.", """
from sklearn.decomposition import PCA

pca = PCA(n_components=2).fit(X_scaled)
coordinates = pca.transform(X_scaled)
print("explained variance:", pca.explained_variance_ratio_.round(3).tolist())
print("projected shape:", coordinates.shape)
"""),
        ],
        "semi-supervised-learning": [
            step("1. Separate labeled and unlabeled examples", "The unlabeled examples have features but no target. The `-1` marker is the scikit-learn convention for unknown labels.", """
import numpy as np

X = np.array([[0.0], [0.2], [0.4], [4.8], [5.0], [5.2]])
y = np.array([0, -1, -1, -1, -1, 1])
print("labeled:", int((y >= 0).sum()), "unlabeled:", int((y < 0).sum()))
"""),
            step("2. Propagate labels from nearby points", "Label propagation assumes nearby examples tend to share labels. Wrong labels can spread, so the assumption needs testing.", """
from sklearn.semi_supervised import LabelSpreading

model = LabelSpreading(kernel="knn", n_neighbors=2).fit(X, y)
print("inferred labels:", model.transduction_.tolist())
"""),
            step("3. Keep uncertainty visible", "Only use high-confidence pseudo-labels for a downstream task; route uncertain cases for annotation.", """
confidence = model.label_distributions_.max(axis=1)
for index, (label, score) in enumerate(zip(model.transduction_, confidence)):
    status = "pseudo-labeled" if score >= 0.8 else "needs review"
    print(index, int(label), round(float(score), 2), status)
"""),
        ],
        "reinforcement-learning": [
            step("1. Define states, actions, and rewards", "An agent observes a state, takes an action, receives a reward, and transitions to another state.", """
import random

random.seed(3)
states, actions = range(5), (0, 1)
goal_state = 4
q_values = [[0.0 for _ in actions] for _ in states]
print("states:", list(states), "actions: 0=left, 1=right")
"""),
            step("2. Learn a tabular Q policy", "Q-learning updates an action value from immediate reward and the best estimated future value.", """
learning_rate, discount = 0.2, 0.9
for _episode in range(300):
    state = 0
    for _step in range(20):
        action = random.randrange(2) if random.random() < 0.15 else max(
            actions, key=lambda candidate: q_values[state][candidate]
        )
        next_state = max(0, min(goal_state, state + (1 if action else -1)))
        reward = 1.0 if next_state == goal_state else -0.02
        future = 0 if next_state == goal_state else max(q_values[next_state])
        q_values[state][action] += learning_rate * (
            reward + discount * future - q_values[state][action]
        )
        state = next_state
        if state == goal_state:
            break
"""),
            step("3. Inspect the learned policy", "A toy tabular policy is not safe for a real environment; inspect reward design, exploration, and behavior over many states.", """
policy = [max(actions, key=lambda action: q_values[state][action]) for state in states]
print("policy (0=left, 1=right):", policy)
assert policy[0] == 1
"""),
        ],
        "recommendation-systems": [
            step("1. Build an interaction matrix", "Rows are users, columns are items, and missing values mean no observed interaction—not necessarily dislike.", """
import numpy as np

users = ["A", "B", "C", "D"]
items = ["book-1", "book-2", "book-3", "book-4"]
ratings = np.array([
    [5, 4, 0, 0], [5, 0, 4, 0], [0, 5, 4, 0], [0, 0, 1, 5]
], dtype=float)
print("user-item matrix shape:", ratings.shape)
"""),
            step("2. Score items by similar users", "A simple neighborhood score uses similarity-weighted interactions and excludes already-seen items.", """
target_user = 0
similarities = ratings @ ratings[target_user] / (
    np.linalg.norm(ratings, axis=1) * np.linalg.norm(ratings[target_user]) + 1e-9
)
candidate_scores = similarities @ ratings / (np.abs(similarities).sum() + 1e-9)
candidate_scores[ratings[target_user] > 0] = -np.inf
print("candidate scores:", candidate_scores.round(2).tolist())
"""),
            step("3. Rank recommendations and state limitations", "Offline metrics should use a time-based holdout; consider cold-start users, popularity bias, privacy, and catalog coverage.", """
recommendations = sorted(
    zip(items, candidate_scores), key=lambda pair: pair[1], reverse=True
)
print("top recommendations:", recommendations[:2])
"""),
        ],
        "feature-engineering": [
            step("1. Identify numeric and categorical fields", "Transformations should be defined from the task and available at prediction time, not from future outcomes.", """
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

numeric = Pipeline([("impute", SimpleImputer()), ("scale", StandardScaler())])
categorical = Pipeline([
    ("impute", SimpleImputer(strategy="most_frequent")),
    ("encode", OneHotEncoder(handle_unknown="ignore")),
])
"""),
            step("2. Fit transformations within the model pipeline", "The pipeline ensures imputers, scalers, and category vocabularies are fitted on training data only.", """
from sklearn.linear_model import LogisticRegression

preprocess = ColumnTransformer([
    ("number", numeric, [0, 1]),
    ("category", categorical, [2]),
])
pipeline = Pipeline([("features", preprocess), ("model", LogisticRegression())])
X = np.array([[20.0, 0.1, "north"], [25.0, 0.3, "south"], [None, 0.2, "north"], [24.0, 0.4, "south"]], dtype=object)
y = [0, 1, 0, 1]
pipeline.fit(X, y)
"""),
            step("3. Handle unseen categories safely", "A production pipeline must accept expected missing values and unseen categories while preserving a stable feature contract.", """
prediction = pipeline.predict(np.array([[22.0, 0.2, "west"]], dtype=object))
print("prediction for unseen category:", prediction.tolist())
"""),
        ],
        "neural-networks": [
            step("1. Create a tiny feed-forward network", "A layer applies a weighted sum and a nonlinear activation to its inputs.", """
import numpy as np

sigmoid = lambda value: 1 / (1 + np.exp(-value))
x = np.array([0.6, 0.2])
W1 = np.array([[0.5, -0.4], [0.3, 0.8]])
b1 = np.array([0.0, 0.1])
W2 = np.array([[0.7], [-0.2]])
b2 = np.array([0.0])
"""),
            step("2. Forward-propagate through layers", "The hidden representation is transformed into an output probability; training adjusts weights to reduce a loss.", """
hidden = np.tanh(x @ W1 + b1)
probability = sigmoid(hidden @ W2 + b2)
print("hidden:", hidden.round(3), "probability:", probability.round(3))
"""),
            step("3. Check how a parameter affects the output", "A small perturbation illustrates sensitivity; backpropagation computes these derivatives efficiently for all parameters.", """
perturbed_W2 = W2.copy()
perturbed_W2[0, 0] += 0.01
perturbed_probability = sigmoid(hidden @ perturbed_W2 + b2)
print("output change:", round(float((perturbed_probability - probability).item()), 6))
"""),
        ],
        "backpropagation": [
            step("1. Define a differentiable prediction and loss", "For a one-weight linear model, squared-error loss has a simple derivative that can be derived by the chain rule.", """
x, target, weight, bias = 2.0, 5.0, 0.5, 0.0
prediction = weight * x + bias
loss = (prediction - target) ** 2
print({"prediction": prediction, "loss": loss})
"""),
            step("2. Compute gradients", "The derivative of squared error with respect to the weight includes the input factor from the prediction equation.", """
error = prediction - target
gradient_weight = 2 * error * x
gradient_bias = 2 * error
print({"d_loss_d_weight": gradient_weight, "d_loss_d_bias": gradient_bias})
"""),
            step("3. Update parameters and measure loss again", "Gradient descent moves parameters opposite the gradient; a learning rate that is too large can make loss diverge.", """
learning_rate = 0.1
weight -= learning_rate * gradient_weight
bias -= learning_rate * gradient_bias
new_loss = (weight * x + bias - target) ** 2
print({"updated_parameters": (weight, bias), "loss_after_update": new_loss})
assert new_loss < loss
"""),
        ],
        "deep-learning": [
            step("1. Prepare a nonlinear classification task", "A multilayer perceptron is a small example of a deep model; its hidden layers learn intermediate representations.", """
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split

X, y = make_moons(n_samples=240, noise=0.18, random_state=8)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=8, stratify=y
)
"""),
            step("2. Train a multilayer network", "Deep models are not automatically better; compare against simpler baselines and tune on validation data.", """
from sklearn.neural_network import MLPClassifier

network = MLPClassifier(
    hidden_layer_sizes=(16, 8), max_iter=500, random_state=8, early_stopping=True
).fit(X_train, y_train)
"""),
            step("3. Evaluate the held-out set", "Report held-out performance and resource use; this small CPU example is not evidence that a deep model is needed.", """
print("held-out accuracy:", round(network.score(X_test, y_test), 3))
print("training iterations:", network.n_iter_)
"""),
        ],
        "generative-models": [
            step("1. Compare model families", "VAEs learn a probabilistic latent representation, GANs train a generator against a discriminator, and diffusion models learn denoising steps.", """
model_families = {
    "VAE": "encode to a regularized latent distribution, then decode",
    "GAN": "train a generator and discriminator in competition",
    "diffusion": "learn to reverse a gradual noising process",
}
for family, idea in model_families.items():
    print(f"{family}: {idea}")
"""),
            step("2. Simulate a diffusion forward process", "A forward process progressively adds noise; training learns a denoiser for reversing this process.", """
import numpy as np

rng = np.random.default_rng(7)
clean = np.array([0.2, 0.8, 0.4, 0.6])
noise = rng.normal(size=clean.shape)
alpha = 0.7
noisy = np.sqrt(alpha) * clean + np.sqrt(1 - alpha) * noise
print("noisy sample:", noisy.round(3))
"""),
            step("3. Inspect a known-noise reconstruction", "This oracle reconstruction knows the injected noise exactly; a real generative model must estimate it from data and never gets this shortcut.", """
reconstructed = (noisy - np.sqrt(1 - alpha) * noise) / np.sqrt(alpha)
print("reconstruction:", reconstructed.round(3))
assert np.allclose(reconstructed, clean)
"""),
        ],
        "text-preprocessing": [
            step("1. Inspect raw text before normalization", "Raw text can contain negation, identifiers, punctuation, and casing that affect the task.", """
import re

text = "Can't reset device E-1042!"
print("raw:", text)
"""),
            step("2. Tokenize with explicit rules", "This simple tokenizer retains contractions and alphanumeric product IDs; production tokenizers are language- and model-specific.", """
normalized = text.lower()
tokens = re.findall(r"[a-z]+-\\d+|[a-z]+(?:'[a-z]+)?|\\d+|[^\\w\\s]", normalized)
print("tokens:", tokens)
"""),
            step("3. Avoid harmful normalization", "Removing punctuation, negation, or identifiers can change meaning; compare preprocessing choices on a held-out task set.", """
assert "can't" in tokens
assert "e-1042" in tokens
print("important distinctions preserved")
"""),
        ],
        "bag-of-words": [
            step("1. Build a vocabulary", "A fixed vocabulary maps each token to a stable column in the document-term matrix.", """
from collections import Counter

documents = ["reset password", "password reset failed", "billing question"]
tokenized = [document.lower().split() for document in documents]
vocabulary = sorted({token for document in tokenized for token in document})
term_index = {term: index for index, term in enumerate(vocabulary)}
print(term_index)
"""),
            step("2. Count terms per document", "Bag of words stores counts and deliberately ignores token order.", """
import numpy as np

matrix = np.zeros((len(documents), len(vocabulary)), dtype=int)
for row, tokens in enumerate(tokenized):
    counts = Counter(tokens)
    for term, count in counts.items():
        matrix[row, term_index[term]] = count
print("columns:", vocabulary)
print(matrix)
"""),
            step("3. Inspect what order was lost", "Documents with the same word counts have the same bag-of-words representation even if their word order differs.", """
first, second = "dog bites person", "person bites dog"
def counts(text):
    return Counter(text.split())
print("same counts:", counts(first) == counts(second))
"""),
        ],
        "word2vec": [
            step("1. Build skip-gram training pairs", "Word2Vec skip-gram learns to predict nearby context tokens from a center word; this tiny corpus keeps training inspectable.", """
import numpy as np

corpus = [
    "battery", "lasts", "long", "battery", "charges",
    "quickly", "charger", "powers", "battery",
]
vocabulary = sorted(set(corpus))
word_id = {word: index for index, word in enumerate(vocabulary)}
pairs = []
for position, word in enumerate(corpus):
    for neighbor in range(max(0, position - 2), min(len(corpus), position + 3)):
        if neighbor != position:
            pairs.append((word_id[word], word_id[corpus[neighbor]]))
print("vocabulary:", vocabulary, "training pairs:", len(pairs))
"""),
            step("2. Train a small negative-sampling model", "The logistic objective raises scores for observed center-context pairs and lowers scores for sampled noise pairs.", """
rng = np.random.default_rng(11)
dimension = 8
input_vectors = rng.normal(0, 0.1, (len(vocabulary), dimension))
context_vectors = rng.normal(0, 0.1, (len(vocabulary), dimension))

def update(center, context, label, rate=0.04):
    source = input_vectors[center].copy()
    target_vector = context_vectors[context].copy()
    score = float(source @ target_vector)
    probability = 1 / (1 + np.exp(-np.clip(score, -20, 20)))
    gradient = rate * (label - probability)
    input_vectors[center] += gradient * target_vector
    context_vectors[context] += gradient * source

for _epoch in range(80):
    for center, context in pairs:
        update(center, context, 1)
        for _ in range(2):
            negative = int(rng.integers(len(vocabulary)))
            if negative != context:
                update(center, negative, 0)
"""),
            step("3. Inspect nearest vector neighbors", "These vectors are trained on a tiny corpus and are unstable; real Word2Vec needs a larger, representative corpus and evaluation.", """
word = "battery"
vector = input_vectors[word_id[word]]
neighbors = []
for candidate in vocabulary:
    if candidate == word:
        continue
    other = input_vectors[word_id[candidate]]
    similarity = float(vector @ other / (np.linalg.norm(vector) * np.linalg.norm(other) + 1e-9))
    neighbors.append((candidate, similarity))
print(sorted(neighbors, key=lambda pair: -pair[1])[:3])
"""),
        ],
        "attention": [
            step("1. Represent queries, keys, and values", "A query is compared with keys; the resulting weights mix value vectors.", """
import numpy as np

query = np.array([1.0, 0.0])
keys = np.array([[1.0, 0.0], [0.0, 1.0]])
values = np.array([[3.0, 0.0], [0.0, 6.0]])
"""),
            step("2. Compute scaled attention weights", "Scaling dot products by the square root of the key dimension helps control score magnitude.", """
scores = query @ keys.T / np.sqrt(keys.shape[1])
weights = np.exp(scores - scores.max())
weights /= weights.sum()
print("scores:", scores.round(3), "weights:", weights.round(3))
"""),
            step("3. Combine values", "The output is a weighted sum of values; multi-head attention repeats this operation with learned projections.", """
attended = weights @ values
print("attended representation:", attended.round(3))
"""),
        ],
        "prompt-engineering": [
            step("1. Specify task and boundaries", "A useful prompt makes the task, permitted evidence, audience, and constraints explicit.", """
question = "Can I return an item after 20 days?"
policy = "Returns are accepted within 30 days with a receipt."
instruction = "Answer using only the supplied policy; say when the evidence is insufficient."
"""),
            step("2. Request a structured response", "A requested schema makes downstream validation easier, but the application must still validate the model response.", """
prompt = (
    f"{instruction}\\nPolicy: {policy}\\nQuestion: {question}\\n"
    "Return JSON with keys answer and supporting_quote."
)
print(prompt)
"""),
            step("3. Test prompt behavior with examples", "A prompt should be evaluated on representative, ambiguous, and adversarial questions rather than one hand-picked success.", """
test_questions = [
    "Can I return this after 20 days?",
    "Can I return it after 50 days?",
    "Can I return it without a receipt?",
]
print("evaluation cases:", len(test_questions))
"""),
        ],
        "llm-inference": [
            step("1. Convert logits to probabilities", "Temperature rescales logits before softmax; lower values sharpen the distribution and higher values flatten it.", """
import numpy as np

logits = np.array([2.0, 1.0, 0.1])
"""),
            step("2. Compare temperatures", "Sampling settings affect variety and repeatability; they do not repair an incorrect or unsupported answer.", """
def softmax(values):
    shifted = values - values.max()
    probabilities = np.exp(shifted)
    return probabilities / probabilities.sum()

for temperature in (0.5, 1.0, 1.8):
    print(temperature, softmax(logits / temperature).round(3).tolist())
"""),
            step("3. Sample reproducibly", "A fixed random seed makes this demonstration repeatable; production generation also needs token and time limits.", """
rng = np.random.default_rng(2)
probabilities = softmax(logits / 0.8)
tokens = ["A", "B", "C"]
print([tokens[index] for index in rng.choice(len(tokens), size=5, p=probabilities)])
"""),
        ],
        "fine-tuning": [
            step("1. Compare adaptation strategies", "Prompting, retrieval, and fine-tuning solve different needs; fine-tuning is not a substitute for up-to-date factual retrieval.", """
strategies = {
    "prompting": "change instructions and examples",
    "retrieval": "supply current external evidence at inference",
    "fine_tuning": "update model behavior from curated training examples",
}
print(strategies)
"""),
            step("2. Estimate a low-rank adapter size", "A rank-r adapter for a matrix uses approximately r times the sum of input and output dimensions instead of the full matrix.", """
input_dim, output_dim, rank = 4096, 4096, 8
full_parameters = input_dim * output_dim
adapter_parameters = rank * (input_dim + output_dim)
print("parameter reduction:", round(1 - adapter_parameters / full_parameters, 3))
"""),
            step("3. Plan a safe fine-tuning experiment", "Deduplicate and permission-check data, split by source or time, compare with a baseline, and keep a rollbackable model artifact.", """
experiment_checklist = {
    "training_data_reviewed": True,
    "held_out_evaluation_defined": True,
    "baseline_available": True,
    "rollback_artifact_required": True,
}
assert all(experiment_checklist.values())
print(experiment_checklist)
"""),
        ],
        "multimodal-ai": [
            step("1. Model typed input parts", "Multimodal requests can combine text and media, but each part needs explicit type and provenance.", """
request = {
    "parts": [
        {"type": "text", "text": "Describe visible damage."},
        {"type": "image", "media_type": "image/jpeg", "source": "approved-image-001"},
    ]
}
print([part["type"] for part in request["parts"]])
"""),
            step("2. Validate modality-specific requirements", "Validate media type, size, consent, and reference access before sending content to a model.", """
allowed_types = {"text", "image", "audio", "video"}
assert all(part["type"] in allowed_types for part in request["parts"])
image_parts = [part for part in request["parts"] if part["type"] == "image"]
assert all(part["media_type"].startswith("image/") for part in image_parts)
"""),
            step("3. Evaluate each modality", "Measure transcription, visual grounding, and cross-modal reasoning separately; an aggregate score can hide failures.", """
evaluation_dimensions = {
    "text": ["factuality", "format"],
    "image": ["visible-evidence grounding", "omission"],
    "audio": ["word error rate", "speaker handling"],
}
print(evaluation_dimensions)
"""),
        ],
        "llm-evaluation": [
            step("1. Create a small versioned evaluation set", "Representative examples should cover normal, ambiguous, and unsupported requests with expected evidence.", """
cases = [
    {"question": "return after 20 days", "evidence": "Returns within 30 days", "expected": "answer"},
    {"question": "return after 90 days", "evidence": "Returns within 30 days", "expected": "decline"},
    {"question": "free lifetime return", "evidence": "Returns within 30 days", "expected": "decline"},
]
print("test cases:", len(cases))
"""),
            step("2. Score a groundedness check", "This lexical overlap check is only a toy signal; real evaluation needs human-reviewed rubrics and semantic evidence checks.", """
def lexical_support(answer, evidence):
    answer_terms = set(answer.lower().split())
    evidence_terms = set(evidence.lower().split())
    return len(answer_terms & evidence_terms) / max(1, len(answer_terms))

answer = "Returns are accepted within 30 days."
print("lexical support:", round(lexical_support(answer, cases[0]["evidence"]), 2))
"""),
            step("3. Record failure categories", "Track unsupported claims, retrieval misses, refusal errors, latency, and cost for each change to models or prompts.", """
run_record = {
    "model": "record-the-exact-model-version",
    "prompt_version": "support-v3",
    "case_count": len(cases),
    "failure_categories": ["unsupported_claim", "missed_evidence", "incorrect_refusal"],
}
print(run_record)
"""),
        ],
        "responsible-ai": [
            step("1. Describe impact and data boundaries", "Identify affected people, sensitive inputs, intended use, prohibited use, and a route to appeal or human review.", """
system_card = {
    "intended_use": "prioritize support requests",
    "sensitive_data": "exclude unnecessary personal details",
    "human_review": "required for high-impact or uncertain cases",
    "appeal_path": "available to affected users",
}
print(system_card)
"""),
            step("2. Measure subgroup error rates", "Aggregate metrics can conceal unequal errors; compare adequately sized groups and report uncertainty and limitations.", """
groups = {
    "group-A": {"actual": [1, 1, 0, 0], "predicted": [1, 0, 0, 0]},
    "group-B": {"actual": [1, 1, 0, 0], "predicted": [1, 1, 1, 0]},
}
for name, data in groups.items():
    positives = sum(data["actual"])
    true_positives = sum(a == p == 1 for a, p in zip(data["actual"], data["predicted"]))
    print(name, "recall:", true_positives / positives)
"""),
            step("3. Define a safe failure path", "A model score is not a policy: add a conservative fallback, monitor outcomes, and route uncertain cases for qualified review.", """
def decide(probability, threshold=0.8):
    return "automatic" if probability >= threshold else "human_review"

print([decide(score) for score in (0.95, 0.62, 0.21)])
"""),
        ],
        "tool-calling": [
            step("1. Define a narrow tool contract", "Tools should expose the smallest capability needed, with typed arguments and bounded effects.", """
ALLOWED_TOOLS = {"lookup_order"}
orders = {"ORD-1042": {"status": "shipped"}}
"""),
            step("2. Validate and authorize before dispatch", "Never execute arbitrary model-generated code or trust arguments without validation and authorization.", """
def dispatch_tool(name, arguments):
    if name not in ALLOWED_TOOLS:
        raise ValueError(f"tool not allowed: {name}")
    order_id = arguments.get("order_id")
    if not isinstance(order_id, str) or order_id not in orders:
        raise ValueError("unknown or invalid order_id")
    return orders[order_id]

print(dispatch_tool("lookup_order", {"order_id": "ORD-1042"}))
"""),
            step("3. Require approval for side effects", "Read-only tools can often be automatic; sending messages, changing records, or spending money needs explicit policy and often human confirmation.", """
def approve_action(action, approved):
    if action in {"send_email", "issue_refund"} and not approved:
        return "awaiting_human_approval"
    return "ready_to_execute"

print(approve_action("issue_refund", approved=False))
"""),
        ],
        "mlops": [
            step("1. Record a reproducible model artifact", "Store model, data, code, and configuration versions together so a deployed prediction can be traced.", """
deployment = {
    "model_version": "ticket-risk-v1",
    "training_data_version": "tickets-2025-01",
    "feature_schema_version": "features-v2",
    "code_revision": "replace-with-commit-id",
}
print(deployment)
"""),
            step("2. Monitor input drift", "A change in feature distribution may indicate a new operating regime or a broken data pipeline; it is not itself proof of lower quality.", """
training = [10, 11, 9, 10, 10]
serving = [18, 19, 17, 18, 20]
mean_shift = sum(serving) / len(serving) - sum(training) / len(training)
print("mean shift:", mean_shift)
"""),
            step("3. Define alert and rollback behavior", "Monitoring needs an owner and an action; retain the previous known-good artifact and verify rollback procedures.", """
alert = abs(mean_shift) > 3
action = "investigate and consider rollback" if alert else "continue monitoring"
print({"alert": alert, "action": action, "rollback_version": "ticket-risk-v0"})
"""),
        ],
    }
)

# Provider/runtime lessons explain the production boundary and demonstrate a
# guarded call. These calls do not execute unless explicitly opted in.
PROVIDER_LESSONS: dict[str, tuple[str, str]] = {
    "ollama": (
        "OLLAMA_MODEL",
        "OLLAMA_MODEL",
    ),
    "openai": (
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
    ),
    "gemini": (
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
    ),
    "anthropic": (
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL",
    ),
    "docker-model-runner": (
        "DOCKER_MODEL_RUNNER_URL",
        "DOCKER_MODEL_RUNNER_MODEL",
    ),
    "amazon-sagemaker": (
        "AWS_DEFAULT_REGION",
        "SAGEMAKER_ENDPOINT_NAME",
    ),
    "amazon-bedrock": (
        "AWS_DEFAULT_REGION",
        "BEDROCK_MODEL_ID",
    ),
}


def provider_lesson(slug: str) -> list[LessonStep]:
    required_setting, model_setting = PROVIDER_LESSONS[slug]
    title = slug.replace("-", " ").title()
    endpoint = {
        "ollama": "http://localhost:11434/api/chat",
        "openai": "OpenAI Responses API",
        "gemini": "Google GenAI generate_content",
        "anthropic": "Anthropic Messages API",
        "docker-model-runner": "OpenAI-compatible Docker Model Runner API",
        "amazon-sagemaker": "SageMaker Runtime InvokeEndpoint",
        "amazon-bedrock": "Bedrock Runtime Converse API",
    }[slug]
    code = f'''import os

RUN_PROVIDER_CALL = False
print("{title} integration: {endpoint}")
print("Required setting present:", bool(os.getenv("{required_setting}")))
print("Set RUN_PROVIDER_CALL=True in this cell only when credentials, model access,")
print("data handling, and any provider charges have been reviewed.")
'''
    integration_function = {
        "ollama": "ask_ollama",
        "openai": "ask_openai",
        "gemini": "ask_gemini",
        "anthropic": "ask_anthropic",
        "docker-model-runner": "ask_docker_model_runner",
        "amazon-sagemaker": "invoke_sagemaker",
        "amazon-bedrock": "ask_bedrock",
    }[slug]
    invocation = f"response = {integration_function}(prompt)"
    invoke_code = f'''import os

from examples.integrations.model_providers import {integration_function}

if not RUN_PROVIDER_CALL:
    print("Provider call skipped. Set RUN_PROVIDER_CALL=True to opt in.")
elif not os.getenv("{required_setting}"):
    raise RuntimeError("Missing required setting: {required_setting}")
else:
    print("Selected model or endpoint:", os.getenv("{model_setting}", "not set"))
    prompt = "In one sentence, explain what this model integration can do."
    {invocation}
    print(response)
'''
    return [
        step(
            "1. Understand the integration boundary",
            f"This lesson connects the application contract to {title}. The default path is offline, makes no request, and creates no cloud resources.",
            code,
        ),
        step(
            "2. Keep credentials and billing opt-in",
            f"The SDK call in `examples/integrations/model_providers.py` uses {endpoint}. Enable provider calls only after configuring credentials, permissions, model access, and spending limits.",
            invoke_code,
        ),
        step(
            "3. Validate output before using it",
            "Treat provider output as untrusted text. Validate structure and evidence, handle timeouts/rate limits explicitly, and record the selected model/version.",
            """
def validate_summary(text, maximum_characters=2_000):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("provider returned an empty or non-text result")
    if len(text) > maximum_characters:
        raise ValueError("provider response exceeds the application limit")
    return text.strip()

sample = validate_summary("Example response; no provider call was made.")
print(sample)
""",
        ),
    ]


for _slug in LESSONS:
    if _slug in PROVIDER_LESSONS:
        raise ValueError(f"{_slug} cannot be both a local and provider lesson")
