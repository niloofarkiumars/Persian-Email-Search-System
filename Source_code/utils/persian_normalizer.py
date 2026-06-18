"""
Persian/Farsi text normalization helpers.
"""

import re
from typing import Any, Iterable


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
    text = text.translate(ARABIC_TO_PERSIAN_TRANSLATION)
    text = text.translate(DIGIT_TRANSLATION)
    text = DIACRITICS_RE.sub("", text)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def normalize_persian_no_space(value: Any) -> str:
    """Normalize Persian text for exact matching while ignoring whitespace."""
    text = normalize_persian_text(value)
    return WHITESPACE_RE.sub("", text)
