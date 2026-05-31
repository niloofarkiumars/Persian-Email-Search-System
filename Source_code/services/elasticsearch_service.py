"""
Elasticsearch service layer
"""

from elasticsearch import Elasticsearch, exceptions
from typing import List, Dict, Any, Optional
from Source_code.utils.logger import logger
from Source_code.config import config
import warnings
warnings.filterwarnings('ignore')


class ElasticsearchService:
    """Service for Elasticsearch operations"""

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

            # Index settings with Persian analyzer
            settings = {
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "persian_analyzer": {
                                "type": "standard"  # or "persian" if available
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "messageId": {"type": "keyword"},
                        "subject": {"type": "text", "analyzer": "standard"},
                        "body": {"type": "text", "analyzer": "standard"},
                        "from": {"type": "text", "analyzer": "standard"},
                        "to": {"type": "text", "analyzer": "standard"},
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
                "_source": doc
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

    def search(self, query: str, fields: List[str] = None, size: int = 20) -> List[Dict]:
        """Search for emails"""
        if fields is None:
            fields = ["subject^3", "body", "from", "to"]

        try:
            response = self.es.search(
                index=self.index_name,
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": fields,
                            "fuzziness": "AUTO",
                            "operator": "or"
                        }
                    },
                    "highlight": {
                        "fields": {
                            "body": {"fragment_size": 150, "number_of_fragments": 2},
                            "subject": {}
                        }
                    },
                    "size": size
                }
            )

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

            logger.info(f"Search for '{query}' returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

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