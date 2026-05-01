import json
import tempfile

import pytest
from memoria.memory_api import MemoryAPI


class TestMemoryAPI:
    def test_store_and_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            node = mem.store("test_node", "some content", label="Test Node")
            assert node.id == "test_node"
            retrieved = mem.get_node("test_node")
            assert retrieved is not None
            assert retrieved.content == "some content"

    def test_store_with_connections(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            mem.store("a", "content a")
            mem.store("b", "content b", connects_to=["a"])
            graph = mem.get_graph()
            assert graph.has_edge("b", "a")

    def test_store_deduplicates_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            n1 = mem.store("test", "first")
            n2 = mem.store("test", "second")
            assert n1.id == "test"
            assert n2.id == "test_2"

    def test_extract_with_llm(self):
        with tempfile.TemporaryDirectory() as tmp:
            def llm(prompt: str) -> str:
                return json.dumps([
                    {
                        "content": "Metaclasses control class creation",
                        "label": "Metaclasses",
                        "connects_to": [],
                    }
                ])

            mem = MemoryAPI(storage_path=tmp, llm_callable=llm)
            result = mem.extract("user asked about metaclasses")
            assert len(result.nodes) == 1

    def test_extract_without_llm_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            with pytest.raises(ValueError, match="llm_callable"):
                mem.extract("test")

    def test_retrieve(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            mem.store("python_decorators", "Decorators wrap functions")
            mem.store("python_functions", "Functions are first-class")
            results = mem.retrieve("decorators")
            assert len(results) >= 1

    def test_export_dot(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            mem.store("node_a", "content a")
            dot = mem.export_dot()
            assert "digraph memory" in dot
            assert "node_a" in dot

    def test_garden(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            mem.store("keep", "important stuff")
            stats = mem.garden()
            assert "active_nodes" in stats
            assert stats["active_nodes"] == 1

    def test_connect(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            mem.store("a", "c")
            mem.store("b", "c")
            edge = mem.connect("a", "b")
            assert edge is not None
            graph = mem.get_graph()
            assert graph.has_edge("a", "b")

    def test_remove_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            mem.store("target", "to be removed")
            removed = mem.remove_node("target")
            assert removed is not None
            assert mem.get_node("target") is None

    def test_list_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            mem.store("a", "c", label="Alpha")
            mem.store("b", "c", label="Beta")
            nodes = mem.list_nodes()
            assert len(nodes) == 2
            ids = [n["id"] for n in nodes]
            assert "a" in ids
            assert "b" in ids

    def test_scheduler_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = MemoryAPI(storage_path=tmp)
            assert not mem.scheduler_running
            mem.start_scheduler(interval_seconds=3600)
            assert mem.scheduler_running
            mem.stop_scheduler()
            assert not mem.scheduler_running
