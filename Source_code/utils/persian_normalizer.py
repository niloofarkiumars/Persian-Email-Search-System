"""
Persian/Farsi text normalization helpers.
"""

import re
from functools import lru_cache
from typing import Any, Iterable, List


ARABIC_TO_PERSIAN_TRANSLATION = str.maketrans({
    "ي": "ی",
    "ى": "ی",
    "ئ": "ی",
    "ك": "ک",
    "ۀ": "ه",
    "ة": "ه",
    "ؤ": "و",
    "إ": "ا",
    "أ": "ا",
    "ٱ": "ا",
    "آ": "آ",
    "‌": " ",
    "ـ": "",
})

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ASCII_DIGITS = "0123456789"

DIGIT_TRANSLATION = str.maketrans({
    **dict(zip(PERSIAN_DIGITS, ASCII_DIGITS)),
    **dict(zip(ARABIC_DIGITS, ASCII_DIGITS)),
})

DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670]")
WHITESPACE_RE = re.compile(r"\s+")
TOKEN_RE = re.compile(r"[\w\u0600-\u06FF]+", re.UNICODE)


@lru_cache(maxsize=1)
def _parsivar_tools():
    """Load Parsivar tools when installed; otherwise use local fallbacks."""
    try:
        from parsivar import FindStems, Normalizer, Tokenizer

        return {
            "normalizer": Normalizer(),
            "tokenizer": Tokenizer(),
            "stemmer": FindStems(),
        }
    except Exception:
        return None


def stringify(value: Any) -> str:
    """Convert common document values to searchable text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Iterable) and not isinstance(value, (dict, bytes)):
        return " ".join(stringify(item) for item in value)
    return str(value)


def normalize_persian_text(value: Any) -> str:
    """
    Normalize Persian text before indexing and searching.

    This keeps word boundaries, so it is suitable for regular full-text search.
    """
    text = stringify(value)
    tools = _parsivar_tools()
    if tools:
        try:
            text = tools["normalizer"].normalize(text)
        except Exception:
            pass

    text = text.translate(ARABIC_TO_PERSIAN_TRANSLATION)
    text = text.translate(DIGIT_TRANSLATION)
    text = DIACRITICS_RE.sub("", text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def normalize_persian_no_space(value: Any) -> str:
    """Normalize Persian text for exact matching while ignoring whitespace."""
    text = normalize_persian_text(value)
    return WHITESPACE_RE.sub("", text)


def tokenize_persian_words(value: Any, stem: bool = False) -> List[str]:
    """Tokenize normalized Persian text, optionally using Parsivar stems."""
    text = normalize_persian_text(value)
    tools = _parsivar_tools()

    if tools:
        try:
            tokens = tools["tokenizer"].tokenize_words(text)
        except Exception:
            tokens = TOKEN_RE.findall(text)
    else:
        tokens = TOKEN_RE.findall(text)

    cleaned = [token for token in tokens if token.strip()]
    if not stem or not tools:
        return cleaned

    stemmed = []
    for token in cleaned:
        try:
            stemmed.append(tools["stemmer"].convert_to_stem(token))
        except Exception:
            stemmed.append(token)
    return stemmed
