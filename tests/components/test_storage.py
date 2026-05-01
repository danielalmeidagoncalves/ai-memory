import tempfile

from memoria.graph.edge import Edge
from memoria.graph.graph import MemoryGraph
from memoria.graph.node import Node
from memoria.storage.file_store import FileStore


class TestFileStore:
    def test_save_and_load_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp)
            graph = MemoryGraph()
            graph.add_node(Node(id="n1", label="N1", content="test content"))
            graph.add_node(Node(id="n2", label="N2", content="other content"))
            graph.add_edge(Edge(source_id="n1", target_id="n2"))
            store.save_active(graph)

            loaded = store.load_active()
            assert loaded.node_count() == 2
            assert loaded.edge_count() == 1

    def test_archive_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp)
            graph = MemoryGraph()
            graph.add_node(Node(id="keep", label="Keep", content="important"))
            graph.add_node(Node(id="drop", label="Drop", content="irrelevant"))
            graph.add_edge(Edge(source_id="keep", target_id="drop"))
            store.save_active(graph)

            store.archive_nodes(["drop"], graph)

            active = store.load_active()
            assert active.node_count() == 1
            assert active.has_node("keep")
            assert not active.has_node("drop")

            archived = store.load_archived()
            assert archived.has_node("drop")

    def test_archive_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp)
            graph = MemoryGraph()
            graph.add_node(Node(id="n1", label="N1", content="c"))
            store.save_active(graph)
            store.archive_nodes([], graph)
            assert graph.node_count() == 1

    def test_list_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp)
            graph = MemoryGraph()
            graph.add_node(Node(id="n1", label="N1", content="c"))
            store.save_active(graph)
            daily = store.list_daily_files()
            assert len(daily) == 1
            assert daily[0].endswith(".dot")

    def test_merge_multiple_daily_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            from datetime import datetime, timedelta

            store = FileStore(tmp)
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            g1 = MemoryGraph()
            g1.add_node(Node(id="old", label="Old", content="yesterday"))
            from pathlib import Path

            (Path(tmp) / "daily" / f"{yesterday}.dot").write_text(
                "digraph memory {\n    old [label=\"Old\", content=\"yesterday\", "
                "score=\"1.0\", created=\"2026-05-01T00:00:00\", "
                "accessed=\"2026-05-01T00:00:00\"]\n}\n"
            )

            g2 = MemoryGraph()
            g2.add_node(Node(id="new", label="New", content="today"))
            store.save_active(g2)

            merged = store.load_active()
            assert merged.node_count() == 2
            assert merged.has_node("old")
            assert merged.has_node("new")
