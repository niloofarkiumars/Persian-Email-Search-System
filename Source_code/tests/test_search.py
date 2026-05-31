"""
Unit tests for search functionality
"""

import pytest
from Source_code.controllers.search_controller import SearchController
from Source_code.services.elasticsearch_service import ElasticsearchService
from Source_code.utils.logger import logger


class TestSearch:
    """Test search functionality"""

    @pytest.fixture
    def search_controller(self):
        """Create search controller for testing"""
        return SearchController()

    def test_basic_search(self, search_controller):
        """Test basic search functionality"""
        result = search_controller.search("پروژه")
        assert 'results' in result
        assert 'total' in result
        assert 'query' in result
        logger.info(f"Basic search test passed: {result['total']} results")

    def test_empty_search(self, search_controller):
        """Test empty search query"""
        result = search_controller.search("")
        assert result['total'] == 0

    def test_search_with_special_chars(self, search_controller):
        """Test search with special characters"""
        result = search_controller.search("جستجو!@#$")
        assert 'results' in result

    def test_search_performance(self, search_controller):
        """Test search performance"""
        import time

        start = time.time()
        result = search_controller.search("گزارش")
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should complete within 1 second
        logger.info(f"Search completed in {elapsed:.3f} seconds")


class TestElasticsearchConnection:
    """Test Elasticsearch connectivity"""

    def test_connection(self):
        """Test Elasticsearch connection"""
        es_service = ElasticsearchService()
        assert es_service.es is not None

        info = es_service.es.info()
        assert 'version' in info
        logger.info(f"Elasticsearch version: {info['version']['number']}")