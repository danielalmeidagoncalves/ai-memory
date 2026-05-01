from __future__ import annotations

from memoria.graph.graph import MemoryGraph
from memoria.scoring.config import ScoringConfig
from memoria.scoring.scorer import Scorer
from memoria.storage.file_store import FileStore


class Gardener:
    def __init__(
        self,
        store: FileStore,
        scorer: Scorer | None = None,
        config: ScoringConfig | None = None,
    ) -> None:
        self._store = store
        self._config = config or ScoringConfig()
        self._scorer = scorer or Scorer(self._config)

    def run(self) -> MemoryGraph:
        graph = self._store.load_active()
        below = self._scorer.below_threshold(graph)

        to_archive: list[str] = []
        for nid in below:
            if graph.is_orphan(nid):
                to_archive.append(nid)

        if to_archive:
            self._store.archive_nodes(to_archive, graph)
            graph = self._store.load_active()

        return graph

    def get_stats(self) -> dict[str, int]:
        graph = self._store.load_active()
        return {
            "active_nodes": graph.node_count(),
            "active_edges": graph.edge_count(),
            "daily_files": len(self._store.list_daily_files()),
            "archived_files": len(self._store.list_archived_files()),
        }
