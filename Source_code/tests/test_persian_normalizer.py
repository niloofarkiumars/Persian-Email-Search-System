"""
Tests for Persian text normalization that do not require Elasticsearch.
"""

from Source_code.utils.persian_normalizer import normalize_persian_no_space, normalize_persian_text


def test_normalizes_arabic_letters_to_persian():
    assert normalize_persian_text("كاربرد يكي") == "کاربرد یکی"


def test_removes_diacritics():
    assert normalize_persian_text("عَلِی") == "علی"


def test_normalizes_digits():
    assert normalize_persian_text("۱۲۳ ٤٥٦") == "123 456"


def test_exact_match_form_ignores_spaces_and_zwnj():
    assert normalize_persian_no_space("می‌روم") == normalize_persian_no_space("می روم")
