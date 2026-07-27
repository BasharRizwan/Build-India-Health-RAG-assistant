import hashlib
import math
import re
from typing import Iterable, List


TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "have", "in", "is", "it", "of", "on", "or", "that", "the", "their",
    "this", "to", "was", "were", "with", "under", "through", "over",
}


class HashingEmbeddingModel:
    """Small local embedding model based on feature hashing.

    It keeps the project runnable without model downloads. If a hosted embedding
    API is added later, the search layer only needs another object with embed().
    """

    def __init__(self, dimensions: int = 768) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> List[float]:
        tokens = [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]
        vector = [0.0] * self.dimensions

        self._add_features(vector, tokens, weight=1.0)
        bigrams = [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
        self._add_features(vector, bigrams, weight=1.35)
        acronyms = [t for t in tokens if len(t) <= 8 and any(ch.isdigit() for ch in t)]
        self._add_features(vector, acronyms, weight=1.6)

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_many(self, texts: Iterable[str]) -> List[List[float]]:
        return [self.embed(text) for text in texts]

    def _add_features(self, vector: List[float], features: Iterable[str], weight: float) -> None:
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            raw = int.from_bytes(digest, "big")
            index = raw % self.dimensions
            sign = 1.0 if raw & 1 else -1.0
            vector[index] += sign * weight


def cosine_similarity(left: List[float], right: List[float]) -> float:
    return sum(a * b for a, b in zip(left, right))

