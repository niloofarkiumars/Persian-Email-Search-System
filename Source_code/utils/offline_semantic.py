"""
Offline semantic vector generation for Persian text.

This is a deterministic local embedding fallback. It does not call any online
service and does not require a downloaded model.
"""

import hashlib
import math
import os
from functools import lru_cache
from typing import Any, List, Optional

from Source_code.config import config
from Source_code.utils.persian_normalizer import normalize_persian_text, tokenize_persian_words


def _normalize_vector(vector: List[float]) -> List[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def _fit_vector_dims(vector: List[float], dims: int) -> List[float]:
    if len(vector) == dims:
        return vector
    if len(vector) > dims:
        return vector[:dims]
    return vector + [0.0] * (dims - len(vector))


@lru_cache(maxsize=1)
def _load_sentence_transformer() -> Optional[object]:
    """
    Load a local sentence-transformers model without network access.

    SEMANTIC_MODEL_PATH must point to an existing local model directory. A model
    name is intentionally not enough because that may trigger a download.
    """
    model_path = config.SEMANTIC_MODEL_PATH
    if config.SEMANTIC_BACKEND != "sentence_transformer" or not model_path:
        return None
    if not os.path.isdir(model_path):
        return None

    try:
        from sentence_transformers import SentenceTransformer

        try:
            return SentenceTransformer(model_path, local_files_only=True)
        except TypeError:
            return SentenceTransformer(model_path)
    except Exception:
        return None


def _sentence_transformer_vector(value: Any, dims: int) -> Optional[List[float]]:
    model = _load_sentence_transformer()
    if not model:
        return None

    text = normalize_persian_text(value)
    if not text:
        return [0.0] * dims

    try:
        embedding = model.encode(text, normalize_embeddings=True)
    except Exception:
        return None

    vector = [float(value) for value in embedding]
    return _normalize_vector(_fit_vector_dims(vector, dims))


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
    Generate a local dense vector for Persian semantic search.

    When SEMANTIC_BACKEND=sentence_transformer and SEMANTIC_MODEL_PATH points to
    a local sentence-transformers model, that model is used offline. Otherwise,
    this falls back to a deterministic lexical vectorizer that mixes normalized
    words, optional Parsivar stems, word bigrams, and character ngrams.
    """
    vector_dims = dims or config.SEMANTIC_VECTOR_DIMS
    transformer_vector = _sentence_transformer_vector(value, vector_dims)
    if transformer_vector is not None:
        return transformer_vector

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

    return _normalize_vector(vector)
