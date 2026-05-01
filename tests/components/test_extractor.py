import json

from memoria.extractor.extractor import Extractor
from memoria.extractor.slug import deduplicate_slug, generate_id, generate_slug
from memoria.graph.graph import MemoryGraph
from memoria.graph.node import Node


class TestSlug:
    def test_generate_slug_from_content(self):
        slug = generate_slug("Python decorators are a powerful feature")
        assert "python" in slug
        assert "decorators" in slug
        assert " " not in slug

    def test_generate_slug_short_content(self):
        slug = generate_slug("ab")
        assert len(slug) >= 2
        result = generate_id("ab", set())
        assert len(result) >= 8

    def test_deduplicate_no_conflict(self):
        result = deduplicate_slug("test", set())
        assert result == "test"

    def test_deduplicate_with_conflict(self):
        result = deduplicate_slug("test", {"test"})
        assert result == "test_2"

    def test_deduplicate_multiple_conflicts(self):
        result = deduplicate_slug("test", {"test", "test_2", "test_3"})
        assert result == "test_4"

    def test_generate_id_deduplicates(self):
        existing = {"python_decorators"}
        result = generate_id("python decorators are great", existing)
        assert result != "python_decorators"


class TestExtractor:
    def _mock_llm(self, response_items: list[dict]):
        def llm(prompt: str) -> str:
            return json.dumps(response_items)
        return llm

    def test_extract_basic(self):
        items = [
            {
                "content": "Python metaclasses control class creation",
                "label": "Metaclasses",
                "connects_to": [],
            }
        ]
        extractor = Extractor(self._mock_llm(items))
        result = extractor.extract("user asked about metaclasses", MemoryGraph())
        assert len(result.nodes) == 1
        assert result.nodes[0].label == "Metaclasses"

    def test_extract_with_connections(self):
        items = [
            {
                "content": "Closures capture enclosing scope",
                "label": "Closures",
                "connects_to": ["python_functions"],
            }
        ]
        extractor = Extractor(self._mock_llm(items))
        graph = MemoryGraph()
        graph.add_node(
            Node(id="python_functions", label="Functions", content="c")
        )
        result = extractor.extract("tell me about closures", graph)
        assert len(result.nodes) == 1
        assert len(result.edges) == 1

    def test_extract_empty_response(self):
        def llm(prompt: str) -> str:
            return "[]"
        extractor = Extractor(llm)
        result = extractor.extract("hello", MemoryGraph())
        assert len(result.nodes) == 0

    def test_extract_handles_markdown_json(self):
        def llm(prompt: str) -> str:
            inner = json.dumps(
                [{"content": "test concept", "label": "Test", "connects_to": []}]
            )
            return f"```json\n{inner}\n```"
        extractor = Extractor(llm)
        result = extractor.extract("test", MemoryGraph())
        assert len(result.nodes) == 1

    def test_extract_skips_empty_content(self):
        items = [
            {"content": "", "label": "Empty", "connects_to": []},
            {"content": "Real content", "label": "Real", "connects_to": []},
        ]
        extractor = Extractor(self._mock_llm(items))
        result = extractor.extract("test", MemoryGraph())
        assert len(result.nodes) == 1
