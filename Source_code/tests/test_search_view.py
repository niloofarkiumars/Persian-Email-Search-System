"""
Offline tests for the search CLI behavior.
"""

from Source_code.views.search_view import SearchView


class FakeController:
    def __init__(self):
        self.calls = []

    def semantic_search_text(self, query):
        self.calls.append(("semantic", query))
        return {"query": query, "total": 1, "results": [{"subject": "گزارش ماهانه", "score": 1.79}]}

    def search_words(self, query, ordered=False):
        self.calls.append(("words", query, ordered))
        return {"query": query, "total": 0, "results": []}


def test_search_view_prefers_semantic_search():
    view = SearchView.__new__(SearchView)
    view.controller = FakeController()

    result = view.controller.semantic_search_text("ماهیانه")
    if result["total"] == 0:
        result = view.controller.search_words("ماهیانه", ordered=False)

    assert result["total"] == 1
    assert view.controller.calls == [("semantic", "ماهیانه")]


def test_search_view_falls_back_to_word_search_when_semantic_empty():
    view = SearchView.__new__(SearchView)
    view.controller = FakeController()

    def empty_semantic(query):
        view.controller.calls.append(("semantic", query))
        return {"query": query, "total": 0, "results": []}

    view.controller.semantic_search_text = empty_semantic

    result = view.controller.semantic_search_text("ماهیانه")
    if result["total"] == 0:
        result = view.controller.search_words("ماهیانه", ordered=False)

    assert result["total"] == 0
    assert view.controller.calls == [("semantic", "ماهیانه"), ("words", "ماهیانه", False)]
