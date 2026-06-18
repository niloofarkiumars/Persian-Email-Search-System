"""
Elasticsearch service layer
"""

from elasticsearch import Elasticsearch
from typing import List, Dict, Any, Optional
from Source_code.utils.logger import logger
from Source_code.config import config
from Source_code.utils.persian_normalizer import normalize_persian_no_space, normalize_persian_text
import warnings
warnings.filterwarnings('ignore')


class ElasticsearchService:
    """Service for Elasticsearch operations"""

    TEXT_FIELDS = ["subject", "body", "from", "to", "cc"]
    EXACT_FIELDS = ["subjectExact", "bodyExact", "fromExact", "toExact", "ccExact"]
    DEFAULT_SEARCH_FIELDS = ["subject^4", "subject.ngram^2", "body", "body.ngram", "from^2", "to", "cc"]
    FIELD_ALIASES = {
        "subject": "subject",
        "body": "body",
        "from": "from",
        "from_address": "from",
        "sender": "from",
        "to": "to",
        "to_addresses": "to",
        "cc": "cc",
    }

    def __init__(self):
        self.es = None
        self.index_name = config.INDEX_NAME
        self._connect()

    def _connect(self):
        """Establish connection to Elasticsearch"""
        try:
            self.es = Elasticsearch(
                config.ES_HOST,
                basic_auth=(config.ES_USERNAME, config.ES_PASSWORD),
                verify_certs=False,
                request_timeout=30
            )
            # Test connection
            info = self.es.info()
            logger.info(f"Connected to Elasticsearch version: {info['version']['number']}")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            raise

    def create_index(self, force: bool = False) -> bool:
        """Create index with Persian support"""
        try:
            if self.es.indices.exists(index=self.index_name):
                if force:
                    self.es.indices.delete(index=self.index_name)
                    logger.info(f"Deleted existing index: {self.index_name}")
                else:
                    logger.info(f"Index {self.index_name} already exists")
                    return True

            # Index settings with Persian normalization. This handles common
            # Arabic/Persian variants, diacritics, Persian digits, and ZWNJ.
            settings = {
                "settings": {
                    "index": {
                        "max_ngram_diff": 18
                    },
                    "analysis": {
                        "char_filter": {
                            "persian_char_normalizer": {
                                "type": "mapping",
                                "mappings": [
                                    "\u064A => \u06CC",  # Arabic Yeh -> Persian Yeh
                                    "\u0649 => \u06CC",  # Alef Maksura -> Persian Yeh
                                    "\u0643 => \u06A9",  # Arabic Kaf -> Persian Kaf
                                    "\u06C0 => \u0647",  # Heh with Yeh above -> Heh
                                    "\u200C => "         # ZWNJ / half-space -> regular separator
                                ]
                            },
                            "persian_diacritic_remover": {
                                "type": "pattern_replace",
                                "pattern": "[\\u064B-\\u065F\\u0670]",
                                "replacement": ""
                            }
                        },
                        "filter": {
                            "persian_stop": {
                                "type": "stop",
                                "stopwords": "_persian_"
                            },
                            "persian_ngram_filter": {
                                "type": "ngram",
                                "min_gram": 2,
                                "max_gram": 20
                            }
                        },
                        "analyzer": {
                            "persian_text": {
                                "type": "custom",
                                "char_filter": [
                                    "persian_char_normalizer",
                                    "persian_diacritic_remover"
                                ],
                                "tokenizer": "standard",
                                "filter": [
                                    "lowercase",
                                    "decimal_digit",
                                    "arabic_normalization",
                                    "persian_normalization",
                                    "persian_stop"
                                ]
                            },
                            "persian_search": {
                                "type": "custom",
                                "char_filter": [
                                    "persian_char_normalizer",
                                    "persian_diacritic_remover"
                                ],
                                "tokenizer": "standard",
                                "filter": [
                                    "lowercase",
                                    "decimal_digit",
                                    "arabic_normalization",
                                    "persian_normalization"
                                ]
                            },
                            "persian_ngram": {
                                "type": "custom",
                                "char_filter": [
                                    "persian_char_normalizer",
                                    "persian_diacritic_remover"
                                ],
                                "tokenizer": "standard",
                                "filter": [
                                    "lowercase",
                                    "decimal_digit",
                                    "arabic_normalization",
                                    "persian_normalization",
                                    "persian_ngram_filter"
                                ]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "messageId": {"type": "keyword"},
                        "subject": {
                            "type": "text",
                            "analyzer": "persian_text",
                            "search_analyzer": "persian_search",
                            "fields": {
                                "raw": {"type": "keyword", "ignore_above": 256},
                                "ngram": {"type": "text", "analyzer": "persian_ngram", "search_analyzer": "persian_search"}
                            }
                        },
                        "body": {
                            "type": "text",
                            "analyzer": "persian_text",
                            "search_analyzer": "persian_search",
                            "fields": {
                                "ngram": {"type": "text", "analyzer": "persian_ngram", "search_analyzer": "persian_search"}
                            }
                        },
                        "from": {
                            "type": "text",
                            "analyzer": "persian_text",
                            "search_analyzer": "persian_search",
                            "fields": {
                                "raw": {"type": "keyword", "ignore_above": 256},
                                "ngram": {"type": "text", "analyzer": "persian_ngram", "search_analyzer": "persian_search"}
                            }
                        },
                        "to": {
                            "type": "text",
                            "analyzer": "persian_text",
                            "search_analyzer": "persian_search",
                            "fields": {
                                "raw": {"type": "keyword", "ignore_above": 512},
                                "ngram": {"type": "text", "analyzer": "persian_ngram", "search_analyzer": "persian_search"}
                            }
                        },
                        "cc": {
                            "type": "text",
                            "analyzer": "persian_text",
                            "search_analyzer": "persian_search",
                            "fields": {
                                "ngram": {"type": "text", "analyzer": "persian_ngram", "search_analyzer": "persian_search"}
                            }
                        },
                        "subjectExact": {"type": "keyword", "ignore_above": 32766},
                        "bodyExact": {"type": "keyword", "ignore_above": 32766},
                        "fromExact": {"type": "keyword", "ignore_above": 32766},
                        "toExact": {"type": "keyword", "ignore_above": 32766},
                        "ccExact": {"type": "keyword", "ignore_above": 32766},
                        "semanticVector": {
                            "type": "dense_vector",
                            "dims": config.SEMANTIC_VECTOR_DIMS,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "date": {"type": "date"},
                        "hasAttachment": {"type": "boolean"},
                        "priority": {"type": "keyword"},
                        "folder": {"type": "keyword"},
                        "isRead": {"type": "boolean"}
                    }
                }
            }

            self.es.indices.create(index=self.index_name, body=settings)
            logger.info(f"Created index: {self.index_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False

    def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """Index a single document"""
        try:
            document = self._prepare_document(document)
            response = self.es.index(
                index=self.index_name,
                id=doc_id,
                document=document
            )
            logger.debug(f"Indexed document {doc_id}: {response['result']}")
            return True
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            return False

    def bulk_index(self, documents: List[tuple]) -> int:
        """
        Bulk index documents
        documents: list of (doc_id, document) tuples
        """
        from elasticsearch.helpers import bulk

        actions = [
            {
                "_index": self.index_name,
                "_id": doc_id,
                "_source": self._prepare_document(doc)
            }
            for doc_id, doc in documents
        ]

        try:
            success, failed = bulk(self.es, actions, stats_only=True)
            logger.info(f"Bulk indexed: {success} successful, {failed} failed")
            return success
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return 0

    def _prepare_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Persian text fields and maintain no-space exact fields."""
        prepared = dict(document)
        exact_field_by_text_field = {
            "subject": "subjectExact",
            "body": "bodyExact",
            "from": "fromExact",
            "to": "toExact",
            "cc": "ccExact",
        }

        for text_field, exact_field in exact_field_by_text_field.items():
            normalized_value = normalize_persian_text(prepared.get(text_field, ""))
            prepared[text_field] = normalized_value
            prepared[exact_field] = normalize_persian_no_space(normalized_value)

        return prepared

    def _execute_search(self, query_body: Dict[str, Any]) -> List[Dict]:
        """Execute an Elasticsearch query and format hits consistently."""
        try:
            response = self.es.search(index=self.index_name, body=query_body)
            results = []
            for hit in response['hits']['hits']:
                result = {
                    'id': hit['_id'],
                    'score': hit['_score'],
                    **hit['_source']
                }
                if 'highlight' in hit:
                    result['highlights'] = hit['highlight']
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _highlight_fields(self) -> Dict[str, Any]:
        return {
            "body": {"fragment_size": 150, "number_of_fragments": 2},
            "subject": {},
            "from": {},
            "to": {},
            "cc": {}
        }

    def _resolve_text_field(self, field: str) -> Optional[str]:
        if not field:
            return None
        return self.FIELD_ALIASES.get(field)

    def _resolve_text_fields(self, fields: List[str] = None, include_ngram: bool = False) -> List[str]:
        if not fields:
            return self.DEFAULT_SEARCH_FIELDS if include_ngram else ["subject^4", "body", "from^2", "to", "cc"]

        resolved = []
        for field in fields:
            boost = ""
            field_name = field
            if "^" in field:
                field_name, boost = field.split("^", 1)
                boost = f"^{boost}"

            resolved_field = self._resolve_text_field(field_name)
            if resolved_field:
                resolved.append(f"{resolved_field}{boost}")

        return resolved or self.DEFAULT_SEARCH_FIELDS

    def _exact_fields_for(self, field: str = None) -> List[str]:
        resolved = self._resolve_text_field(field)
        if not resolved:
            return self.EXACT_FIELDS
        return [f"{resolved}Exact"]

    def search(self, query: str, fields: List[str] = None, size: int = 20) -> List[Dict]:
        """Search for emails"""
        normalized_query = normalize_persian_text(query)
        search_fields = self._resolve_text_fields(fields, include_ngram=True)

        results = self._execute_search({
            "query": {
                "multi_match": {
                    "query": normalized_query,
                    "fields": search_fields,
                    "fuzziness": "AUTO",
                    "prefix_length": 1,
                    "operator": "or"
                }
            },
            "highlight": {"fields": self._highlight_fields()},
            "size": size
        })

        logger.info(f"Search for '{query}' returned {len(results)} results")
        return results

    def search_exact_ignore_space(self, query: str, field: str = None, size: int = 20) -> List[Dict]:
        """Exact substring search after Persian normalization and whitespace removal."""
        normalized_query = normalize_persian_no_space(query)
        exact_fields = self._exact_fields_for(field)

        should_queries = [
            {"wildcard": {exact_field: {"value": f"*{normalized_query}*"}}}
            for exact_field in exact_fields
        ]

        return self._execute_search({
            "query": {
                "bool": {
                    "should": should_queries,
                    "minimum_should_match": 1
                }
            },
            "highlight": {"fields": self._highlight_fields()},
            "size": size
        })

    def search_words(self, query: str, fields: List[str] = None, ordered: bool = False, size: int = 20) -> List[Dict]:
        """Search words in exact order as a phrase or in any order with all words required."""
        normalized_query = normalize_persian_text(query)
        search_fields = self._resolve_text_fields(fields)
        query_type = "phrase" if ordered else "best_fields"

        multi_match = {
            "query": normalized_query,
            "fields": search_fields,
            "type": query_type
        }
        if ordered:
            multi_match["slop"] = 0
        else:
            multi_match["operator"] = "and"

        return self._execute_search({
            "query": {"multi_match": multi_match},
            "highlight": {"fields": self._highlight_fields()},
            "size": size
        })

    def search_field(self, query: str, field: str, size: int = 20) -> List[Dict]:
        """Search inside one specific searchable field."""
        resolved_field = self._resolve_text_field(field)
        if not resolved_field:
            logger.warning(f"Unsupported search field: {field}")
            return []

        return self.search(query=query, fields=[resolved_field], size=size)

    def search_ngram(self, query: str, fields: List[str] = None, size: int = 20) -> List[Dict]:
        """Search partial Persian words using ngram subfields."""
        normalized_query = normalize_persian_text(query)
        base_fields = self._resolve_text_fields(fields)
        ngram_fields = []
        for field in base_fields:
            field_name = field.split("^", 1)[0]
            if field_name in self.TEXT_FIELDS:
                ngram_fields.append(f"{field_name}.ngram")

        return self._execute_search({
            "query": {
                "multi_match": {
                    "query": normalized_query,
                    "fields": ngram_fields or ["subject.ngram", "body.ngram", "from.ngram", "to.ngram", "cc.ngram"],
                    "operator": "and"
                }
            },
            "highlight": {"fields": self._highlight_fields()},
            "size": size
        })

    def semantic_search(self, query_vector: List[float], size: int = 20) -> List[Dict]:
        """
        Vector semantic search.

        Documents must include a semanticVector generated by the same embedding
        model used for query_vector.
        """
        if not query_vector:
            logger.warning("Semantic search requires a query embedding vector")
            return []
        if len(query_vector) != config.SEMANTIC_VECTOR_DIMS:
            logger.warning(
                f"Semantic vector length {len(query_vector)} does not match "
                f"SEMANTIC_VECTOR_DIMS={config.SEMANTIC_VECTOR_DIMS}"
            )
            return []

        return self._execute_search({
            "query": {
                "script_score": {
                    "query": {"exists": {"field": "semanticVector"}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'semanticVector') + 1.0",
                        "params": {"query_vector": query_vector}
                    }
                }
            },
            "size": size
        })

    def delete_index(self) -> bool:
        """Delete the index"""
        try:
            if self.es.indices.exists(index=self.index_name):
                self.es.indices.delete(index=self.index_name)
                logger.info(f"Deleted index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        try:
            stats = self.es.indices.stats(index=self.index_name)
            count = self.es.count(index=self.index_name)
            return {
                'document_count': count['count'],
                'size_bytes': stats['indices'][self.index_name]['total']['store']['size_in_bytes'],
                'size_mb': round(stats['indices'][self.index_name]['total']['store']['size_in_bytes'] / 1024 / 1024, 2)
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
