"""
Urgency Classifier — TF-IDF + Logistic Regression

This module trains a simple text classifier on first call and caches the model.
HIGH urgency keywords: injured, bleeding, attack, dying, emergency, critical, severe, accident, hit, trapped, unconscious
LOW urgency: stray, lost, hungry, wandering, thin, homeless
"""
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import numpy as np

_TRAINING_DATA = [
    # HIGH urgency examples
    ("dog hit by car bleeding badly needs immediate help", "HIGH"),
    ("cat severely injured attack by another animal", "HIGH"),
    ("animal unconscious road accident emergency", "HIGH"),
    ("bird with broken wing cannot fly dying", "HIGH"),
    ("dog trapped under debris critical condition", "HIGH"),
    ("injured stray cat bleeding from head", "HIGH"),
    ("puppy hit by motorcycle lying on road", "HIGH"),
    ("animal in severe pain cannot move emergency", "HIGH"),
    ("dog attacked by larger dog deep wounds bleeding", "HIGH"),
    ("cat fell from building looks critically injured", "HIGH"),
    ("horse hit by vehicle lying on road dying", "HIGH"),
    ("dog has seizures convulsions emergency help needed", "HIGH"),
    ("animal poisoning eating toxic substance urgent", "HIGH"),
    ("cat trapped in drain injured", "HIGH"),
    ("dog crushed by heavy object bones broken critical", "HIGH"),
    ("rabbit severely injured predator attack bleeding", "HIGH"),
    ("stray dog badly beaten up injuries all over body", "HIGH"),
    ("animal electrocuted lying still emergency", "HIGH"),
    ("dog choking cannot breathe critical", "HIGH"),
    ("cat with deep wounds needs immediate veterinary care", "HIGH"),
    # LOW urgency examples
    ("stray dog wandering neighborhood looking for food", "LOW"),
    ("lost cat near park friendly", "LOW"),
    ("thin hungry dog needs feeding", "LOW"),
    ("stray kitten meowing outside shelter needed", "LOW"),
    ("homeless dog sleeping near building", "LOW"),
    ("cat seems lost sitting near road", "LOW"),
    ("dog wandering without collar needs home", "LOW"),
    ("stray puppy very friendly needs adoption", "LOW"),
    ("old cat abandoned needs foster home", "LOW"),
    ("dog looking hungry thin ribs showing", "LOW"),
    ("bird with ruffled feathers not flying much", "LOW"),
    ("rabbit loose in garden appears healthy", "LOW"),
    ("dog sleeping on footpath not moving much", "LOW"),
    ("stray cat with kittens needs rescue", "LOW"),
    ("dog roaming streets no collar healthy", "LOW"),
    ("cat sitting outside door looking for food", "LOW"),
    ("parrot escaped from cage found in tree", "LOW"),
    ("turtle found in middle of road needs relocation", "LOW"),
    ("dog whimpering tied to pole owner absent", "LOW"),
    ("stray dogs forming pack near school", "LOW"),
]

_vectorizer = None
_model = None


def _train():
    global _vectorizer, _model
    texts = [t for t, _ in _TRAINING_DATA]
    labels = [l for _, l in _TRAINING_DATA]
    _vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=500, stop_words="english")
    X = _vectorizer.fit_transform(texts)
    _model = LogisticRegression(max_iter=1000, random_state=42)
    _model.fit(X, labels)


def classify_urgency(text: str) -> str:
    """Return 'HIGH' or 'LOW' urgency classification for the given text."""
    global _vectorizer, _model
    if _vectorizer is None or _model is None:
        _train()

    # Quick keyword override for obvious cases
    text_lower = text.lower()
    high_keywords = {
        "bleeding", "injured", "injury", "dying", "emergency", "critical",
        "unconscious", "accident", "trapped", "attack", "attacked", "severe",
        "poisoned", "seizure", "choking", "electrocuted", "broken", "crushed",
        "hit by", "run over", "urgent"
    }
    for kw in high_keywords:
        if kw in text_lower:
            return "HIGH"

    cleaned = re.sub(r"[^a-zA-Z0-9 ]", " ", text)
    X = _vectorizer.transform([cleaned])
    prediction = _model.predict(X)[0]
    return prediction
