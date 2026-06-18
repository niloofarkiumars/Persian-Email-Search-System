"""
Offline semantic vector generation for Persian text.

This is a deterministic local embedding fallback. It does not call any online
service and does not require a downloaded model.
"""

import hashlib
import math
from typing import Any, List

from Source_code.config import config
from Source_code.utils.persian_normalizer import normalize_persian_text, tokenize_persian_words


def _hash_index(feature: str, dims: int) -> int:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dims


def _hash_sign(feature: str) -> float:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=1).digest()
    return 1.0 if digest[0] % 2 == 0 else -1.0


def _character_ngrams(text: str, min_n: int = 3, max_n: int = 5) -> List[str]:
    compact = "".join(text.split())
    grams = []
    for size in range(min_n, max_n + 1):
        grams.extend(compact[index:index + size] for index in range(0, max(len(compact) - size + 1, 0)))
    return grams


def generate_offline_semantic_vector(value: Any, dims: int = None) -> List[float]:
    """
    Generate a deterministic dense vector from Persian lexical features.

    The vector mixes normalized words, optional Parsivar stems, word bigrams,
    and character ngrams. It is not a transformer model, but gives local
    semantic-like similarity without network calls or external model files.
    """
    vector_dims = dims or config.SEMANTIC_VECTOR_DIMS
    vector = [0.0] * vector_dims
    text = normalize_persian_text(value)
    tokens = tokenize_persian_words(text, stem=True)

    features = []
    features.extend(f"w:{token}" for token in tokens)
    features.extend(f"b:{tokens[index]}_{tokens[index + 1]}" for index in range(len(tokens) - 1))
    features.extend(f"c:{gram}" for gram in _character_ngrams(text))

    if not features:
        return vector

    for feature in features:
        index = _hash_index(feature, vector_dims)
        vector[index] += _hash_sign(feature)

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]
