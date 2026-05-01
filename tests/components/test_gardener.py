import tempfile

from memoria.gardener.gardener import Gardener
from memoria.graph.edge import Edge
from memoria.graph.node import Node
from memoria.scoring.config import ScoringConfig
from memoria.storage.file_store import FileStore


class TestGardener:
    def _make_graph(self, store: FileStore, nodes: list[dict]) -> None:
        from memoria.graph.graph import MemoryGraph

        g = MemoryGraph()
        for n in nodes:
            g.add_node(
                Node(
                    id=n["id"],
                    label=n.get("label", n["id"]),
                    content=n.get("content", "c"),
                    activation_score=n.get("score", 1.0),
                )
            )
        for n in nodes:
            for target in n.get("connects_to", []):
                g.add_edge(Edge(source_id=n["id"], target_id=target))
        store.save_active(g)

    def test_garden_removes_low_orphans(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ScoringConfig(
                archive_threshold=0.5, decay_rate=0.0, connection_bonus_factor=0.0
            )
            store = FileStore(tmp)
            self._make_graph(
                store,
                [
                    {"id": "keep", "score": 0.9, "connects_to": []},
                    {"id": "orphan_low", "score": 0.1},
                    {"id": "orphan_high", "score": 0.9},
                ],
            )
            gardener = Gardener(store, config=config)
            result = gardener.run()
            assert result.has_node("keep")
            assert not result.has_node("orphan_low")
            assert result.has_node("orphan_high")

    def test_garden_keeps_low_connected(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = ScoringConfig(
                archive_threshold=0.5, decay_rate=0.0, connection_bonus_factor=0.0
            )
            store = FileStore(tmp)
            self._make_graph(
                store,
                [
                    {"id": "a", "score": 0.9, "connects_to": ["b"]},
                    {"id": "b", "score": 0.1},
                ],
            )
            gardener = Gardener(store, config=config)
            result = gardener.run()
            assert result.has_node("a")
            assert result.has_node("b")

    def test_get_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp)
            self._make_graph(
                store,
                [{"id": "a", "score": 0.9}, {"id": "b", "score": 0.9}],
            )
            gardener = Gardener(store)
            stats = gardener.get_stats()
            assert stats["active_nodes"] == 2
            assert stats["daily_files"] == 1
