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
        (
            "3",
            Email(
                message_id="3",
                subject="گزارش ماهیانه فروش",
                body="این ایمیل شامل گزارش ماهیانه فروش و وضعیت مالی است.",
                from_address="حسابداری@example.com",
                to_addresses=["مدیریت@example.com"],
            ).to_elasticsearch(),
        ),
        (
            "4",
            Email(
                message_id="4",
                subject="پرداخت حقوق کارکنان",
                body="فایل واریز دستمزد و حقوق این ماه برای همه کارکنان آماده شد.",
                from_address="payroll@example.com",
                to_addresses=["منابع-انسانی@example.com"],
            ).to_elasticsearch(),
        ),
        (
            "5",
            Email(
                message_id="5",
                subject="گزارش بلند پروژه",
                body=(
                    "این پیام شامل توضیحات طولانی درباره وضعیت پروژه، برنامه زمان‌بندی، "
                    "ریسک‌ها، تصمیم‌های مدیریتی و جمع‌بندی نهایی گزارش پروژه است. "
                    * 20
                ),
                from_address="pm@example.com",
                to_addresses=["team@example.com"],
            ).to_elasticsearch(),
        ),
        (
            "6",
            Email(
                message_id="6",
                subject="Meeting درباره Project Phoenix",
                body="جلسه فردا درباره project phoenix و گزارش فنی API برگزار می‌شود.",
                from_address="tech@example.com",
                to_addresses=["engineering@example.com"],
            ).to_elasticsearch(),
        ),
        (
            "7",
            Email(
                message_id="7",
                subject="دعوت به ناهار",
                body="برای ناهار فردا رستوران رزرو شده است.",
                from_address="office@example.com",
                to_addresses=["all@example.com"],
            ).to_elasticsearch(),
        ),
    ]
    assert service.bulk_index(documents) == len(documents)
    service.es.indices.refresh(index=service.index_name)

    yield service

    service.delete_index()


def ids(results):
    return {result["id"] for result in results}


def ordered_ids(results):
    return [result["id"] for result in results]


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


def test_monthly_report_search_allows_reversed_word_order(es_service):
    forward_results = es_service.search_words("گزارش ماهیانه", ordered=False, fields=["subject", "body"])
    reversed_results = es_service.search_words("ماهیانه گزارش", ordered=False, fields=["subject", "body"])

    assert "3" in ids(forward_results)
    assert "3" in ids(reversed_results)


def test_field_specific_search(es_service):
    subject_results = es_service.search_field("مدیریت", field="subject")
    body_results = es_service.search_field("مدیریت", field="body")

    assert "2" in ids(subject_results)
    assert "2" not in ids(body_results)


def test_ngram_partial_word_search(es_service):
    results = es_service.search_ngram("گزا", fields=["subject", "body"])
    assert {"1", "2"}.intersection(ids(results))


def test_offline_semantic_text_search(es_service):
    results = es_service.semantic_search_text("گزارش ماهیانه")
    assert "3" in ids(results)


def test_semantic_search_finds_monthly_report_for_broad_monthly_query(es_service):
    results = es_service.semantic_search_text("خلاصه عملکرد این ماه", size=5)
    assert "3" in ordered_ids(results)


def test_semantic_search_finds_salary_for_wage_query(es_service):
    results = es_service.semantic_search_text("واریز دستمزد", size=5)
    assert ordered_ids(results)[0] == "4"


def test_semantic_search_handles_persian_typo_like_query(es_service):
    results = es_service.semantic_search_text("گزارش پروزه", size=5)
    assert ordered_ids(results)[0] in {"2", "5"}


def test_semantic_search_handles_long_email_content(es_service):
    results = es_service.semantic_search_text("ریسک های برنامه زمان بندی پروژه", size=5)
    assert ordered_ids(results)[0] == "5"


def test_semantic_search_handles_mixed_persian_english_query(es_service):
    results = es_service.semantic_search_text("phoenix API جلسه", size=5)
    assert ordered_ids(results)[0] == "6"
