"""
Integration tests for Persian Elasticsearch behavior.

These tests require a running Elasticsearch instance. They are skipped when
Elasticsearch is not available.
"""

import uuid

import pytest

from Source_code.models.email_model import Email
from Source_code.services.elasticsearch_service import ElasticsearchService


@pytest.fixture
def es_service():
    try:
        service = ElasticsearchService()
    except Exception as exc:
        pytest.skip(f"Elasticsearch is not available: {exc}")

    service.index_name = f"persian_search_test_{uuid.uuid4().hex}"
    assert service.create_index(force=True)

    documents = [
        (
            "1",
            Email(
                message_id="1",
                subject="گزارش پروژه مالی",
                body="امروز درباره كاربرد جستجوی فارسی و می‌روم صحبت شد.",
                from_address="علی@example.com",
                to_addresses=["کاربر ۱۲۳@example.com"],
            ).to_elasticsearch(),
        ),
        (
            "2",
            Email(
                message_id="2",
                subject="جلسه مدیریت",
                body="پروژه مالی گزارش نهایی را آماده کرد.",
                from_address="سارا@example.com",
                to_addresses=["team@example.com"],
            ).to_elasticsearch(),
        ),
    ]
    assert service.bulk_index(documents) == len(documents)
    service.es.indices.refresh(index=service.index_name)

    yield service

    service.delete_index()


def ids(results):
    return {result["id"] for result in results}


def test_exact_match_ignores_spaces_and_half_spaces(es_service):
    results = es_service.search_exact_ignore_space("می روم", field="body")
    assert "1" in ids(results)


def test_arabic_and_persian_letter_variants_match(es_service):
    results = es_service.search("کاربرد")
    assert "1" in ids(results)


def test_ordered_word_search_requires_phrase_order(es_service):
    ordered_results = es_service.search_words("گزارش پروژه مالی", ordered=True, fields=["subject"])
    reversed_results = es_service.search_words("مالی پروژه گزارش", ordered=True, fields=["subject"])

    assert "1" in ids(ordered_results)
    assert "1" not in ids(reversed_results)


def test_unordered_word_search_allows_any_order(es_service):
    results = es_service.search_words("مالی گزارش پروژه", ordered=False, fields=["subject", "body"])
    assert {"1", "2"}.issubset(ids(results))


def test_field_specific_search(es_service):
    subject_results = es_service.search_field("مدیریت", field="subject")
    body_results = es_service.search_field("مدیریت", field="body")

    assert "2" in ids(subject_results)
    assert "2" not in ids(body_results)


def test_ngram_partial_word_search(es_service):
    results = es_service.search_ngram("گزا", fields=["subject", "body"])
    assert {"1", "2"}.intersection(ids(results))
