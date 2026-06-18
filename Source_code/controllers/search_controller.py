"""
Search controller - handles search operations
"""

from typing import List, Dict, Any, Optional
from Source_code.services.elasticsearch_service import ElasticsearchService
from Source_code.utils.logger import logger


class SearchController:
    """Controller for search operations"""

    def __init__(self):
        self.es_service = ElasticsearchService()

    def search(self, query: str, fields: List[str] = None, size: int = 20) -> Dict[str, Any]:
        """Search emails"""
        if not query or not query.strip():
            return {'results': [], 'total': 0, 'query': query}

        results = self.es_service.search(query.strip(), fields, size)

        return {
            'query': query,
            'total': len(results),
            'results': results
        }

    def search_exact_ignore_space(self, query: str, field: str = None, size: int = 20) -> Dict[str, Any]:
        """Search exact normalized text while ignoring spaces."""
        if not query or not query.strip():
            return {'results': [], 'total': 0, 'query': query}

        results = self.es_service.search_exact_ignore_space(query.strip(), field=field, size=size)
        return {'query': query, 'field': field, 'total': len(results), 'results': results}

    def search_words(self, query: str, fields: List[str] = None, ordered: bool = False, size: int = 20) -> Dict[str, Any]:
        """Search all words either in exact order or any order."""
        if not query or not query.strip():
            return {'results': [], 'total': 0, 'query': query}

        results = self.es_service.search_words(query.strip(), fields=fields, ordered=ordered, size=size)
        return {'query': query, 'ordered': ordered, 'total': len(results), 'results': results}

    def search_field(self, query: str, field: str, size: int = 20) -> Dict[str, Any]:
        """Search inside one specific field such as subject, body, from, to, or cc."""
        if not query or not query.strip():
            return {'results': [], 'total': 0, 'query': query}

        results = self.es_service.search_field(query.strip(), field=field, size=size)
        return {'query': query, 'field': field, 'total': len(results), 'results': results}

    def search_ngram(self, query: str, fields: List[str] = None, size: int = 20) -> Dict[str, Any]:
        """Search partial Persian words using ngram fields."""
        if not query or not query.strip():
            return {'results': [], 'total': 0, 'query': query}

        results = self.es_service.search_ngram(query.strip(), fields=fields, size=size)
        return {'query': query, 'total': len(results), 'results': results}

    def semantic_search(self, query_vector: List[float], size: int = 20) -> Dict[str, Any]:
        """Search by embedding vector. Query text must be embedded before calling this."""
        results = self.es_service.semantic_search(query_vector=query_vector, size=size)
        return {'total': len(results), 'results': results}

    def search_advanced(self,
                        text: str = None,
                        from_email: str = None,
                        date_from: str = None,
                        date_to: str = None,
                        has_attachment: bool = None,
                        folder: str = None,
                        size: int = 20) -> Dict[str, Any]:
        """
        Advanced search with filters
        CUSTOMIZE these filters based on your team's fields
        """
        # Build Elasticsearch query with filters
        # This is a template - customize based on your needs
        logger.info(f"Advanced search: text={text}, from={from_email}")

        if from_email:
            return self.search_field(from_email, field="from", size=size)
        if text:
            return self.search(text, size=size)

        return {'results': [], 'total': 0}

    def suggest(self, partial_word: str, field: str = "body") -> List[str]:
        """Get search suggestions"""
        # Implement autocomplete/suggestions
        logger.debug(f"Suggestions for: {partial_word}")
        return []
