"""
Offline tests for sync startup behavior.
"""

from Source_code.controllers.sync_controller import SyncController


class FakeElasticsearchService:
    def __init__(self, has_mapping):
        self.has_mapping = has_mapping

    def has_semantic_vector_mapping(self):
        return self.has_mapping


class TestableSyncController(SyncController):
    def __init__(self, has_mapping):
        self.es_service = FakeElasticsearchService(has_mapping)
        self.force_values = []

    def sync_all(self, force_recreate_index=False):
        self.force_values.append(force_recreate_index)
        return {"synced": 1, "total": 1, "failed": 0}


def test_semantic_vector_sync_recreates_index_when_mapping_missing():
    controller = TestableSyncController(has_mapping=False)

    result = controller.sync_semantic_vectors()

    assert result == {"synced": 1, "total": 1, "failed": 0}
    assert controller.force_values == [True]


def test_semantic_vector_sync_refreshes_documents_when_mapping_exists():
    controller = TestableSyncController(has_mapping=True)

    result = controller.sync_semantic_vectors()

    assert result == {"synced": 1, "total": 1, "failed": 0}
    assert controller.force_values == [False]
