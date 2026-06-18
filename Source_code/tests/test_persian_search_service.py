"""
Offline tests for Persian search behavior.

These tests do not connect to Elasticsearch. They verify document preparation
and the query bodies sent to ElasticsearchService._execute_search.
"""

import sys
import types

from Source_code.config import config
from Source_code.utils.offline_semantic import generate_offline_semantic_vector


elasticsearch_stub = types.ModuleType("elasticsearch")
elasticsearch_stub.Elasticsearch = object
sys.modules.setdefault("elasticsearch", elasticsearch_stub)

from Source_code.services.elasticsearch_service import ElasticsearchService


def make_service():
    service = ElasticsearchService.__new__(ElasticsearchService)
    service.index_name = "test_index"
    service.es = None
    return service


def capture_query(service):
    captured = {}

    def fake_execute_search(query_body):
        captured["query_body"] = query_body
        return [{"id": "1", "score": 1.0}]

    service._execute_search = fake_execute_search
    return captured


def test_prepare_document_normalizes_text_and_exact_fields():
    service = make_service()

    document = service._prepare_document({
        "subject": "كاربرد يكي",
        "body": "می‌روم",
        "from": "عَلِی@example.com",
        "to": ["کاربر ۱۲۳"],
        "cc": ""
    })

    assert document["subject"] == "کاربرد یکی"
    assert document["body"] == "می روم"
    assert document["from"] == "علی@example.com"
    assert document["to"] == "کاربر 123"
    assert document["bodyExact"] == "میروم"
    assert document["toExact"] == "کاربر123"
    assert len(document["semanticVector"]) == 384


def test_exact_ignore_space_uses_exact_fields_and_normalized_query():
    service = make_service()
    captured = capture_query(service)

    service.search_exact_ignore_space("می روم", field="body")

    wildcard = captured["query_body"]["query"]["bool"]["should"][0]["wildcard"]
    assert wildcard == {"bodyExact": {"value": "*میروم*"}}


def test_ordered_word_search_uses_phrase_query():
    service = make_service()
    captured = capture_query(service)

    service.search_words("گزارش پروژه", ordered=True)

    multi_match = captured["query_body"]["query"]["multi_match"]
    assert multi_match["type"] == "phrase"
    assert multi_match["slop"] == 0


def test_unordered_word_search_requires_all_words():
    service = make_service()
    captured = capture_query(service)

    service.search_words("گزارش پروژه", ordered=False)

    multi_match = captured["query_body"]["query"]["multi_match"]
    assert multi_match["type"] == "best_fields"
    assert multi_match["operator"] == "and"


def test_field_search_limits_to_specific_field():
    service = make_service()
    captured = capture_query(service)

    service.search_field("مدیریت", field="subject")

    fields = captured["query_body"]["query"]["multi_match"]["fields"]
    assert fields == ["subject"]


def test_ngram_search_uses_ngram_subfields():
    service = make_service()
    captured = capture_query(service)

    service.search_ngram("گزار", fields=["subject", "body"])

    fields = captured["query_body"]["query"]["multi_match"]["fields"]
    assert fields == ["subject.ngram", "body.ngram"]


def test_semantic_search_text_generates_query_vector():
    service = make_service()
    captured = capture_query(service)

    service.semantic_search_text("گزارش ماهیانه")

    params = captured["query_body"]["query"]["script_score"]["script"]["params"]
    assert len(params["query_vector"]) == 384
    assert any(value != 0 for value in params["query_vector"])


def test_sentence_transformer_backend_requires_local_model_path(monkeypatch):
    monkeypatch.setattr(config, "SEMANTIC_BACKEND", "sentence_transformer")
    monkeypatch.setattr(config, "SEMANTIC_MODEL_PATH", "HooshvareLab/sentence-transformer-fa")

    vector = generate_offline_semantic_vector("گزارش ماهیانه", dims=32)

    assert len(vector) == 32
    assert any(value != 0 for value in vector)


def test_hash_semantic_vector_keeps_requested_dimensions(monkeypatch):
    monkeypatch.setattr(config, "SEMANTIC_BACKEND", "hash")

    vector = generate_offline_semantic_vector("گزارش ماهیانه", dims=64)

    assert len(vector) == 64
    assert any(value != 0 for value in vector)
