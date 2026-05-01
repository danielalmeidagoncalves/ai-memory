from __future__ import annotations

from datetime import datetime
from pathlib import Path

from memoria.graph.dot_serializer import deserialize, serialize
from memoria.graph.graph import MemoryGraph
from memoria.storage.paths import archived_dir, daily_dir


class FileStore:
    def __init__(self, storage_path: str | None = None) -> None:
        from memoria.storage.paths import resolve_storage_path

        self._root = resolve_storage_path(storage_path)
        self._daily = daily_dir(self._root)
        self._archived = archived_dir(self._root)

    @property
    def root(self) -> Path:
        return self._root

    def _today_filename(self) -> str:
        return f"{datetime.now().strftime('%Y-%m-%d')}.dot"

    def _month_filename(self) -> str:
        return f"{datetime.now().strftime('%Y-%m')}.dot"

    def load_active(self) -> MemoryGraph:
        graph = MemoryGraph()
        dot_files = sorted(self._daily.glob("*.dot"))
        for dot_file in dot_files:
            content = dot_file.read_text(encoding="utf-8")
            if content.strip():
                daily_graph = deserialize(content)
                graph.merge(daily_graph)
        return graph

    def save_active(self, graph: MemoryGraph) -> None:
        today_file = self._daily / self._today_filename()
        dot_content = serialize(graph)
        today_file.write_text(dot_content, encoding="utf-8")

    def archive_nodes(self, node_ids: list[str], active_graph: MemoryGraph) -> None:
        if not node_ids:
            return

        month_file = self._archived / self._month_filename()
        if month_file.exists():
            archived_graph = deserialize(
                month_file.read_text(encoding="utf-8")
            )
        else:
            archived_graph = MemoryGraph()

        for nid in node_ids:
            node = active_graph.get_node(nid)
            if node:
                archived_graph.add_node(node)
                for edge in active_graph.get_edges_for(nid):
                    if edge.source_id in node_ids and edge.target_id in node_ids:
                        archived_graph.add_edge(edge)

        month_file.parent.mkdir(parents=True, exist_ok=True)
        month_file.write_text(serialize(archived_graph), encoding="utf-8")

        for nid in node_ids:
            active_graph.remove_node(nid)

        self.save_active(active_graph)

    def load_archived(self, month: str | None = None) -> MemoryGraph:
        if month:
            month_file = self._archived / f"{month}.dot"
            if month_file.exists():
                return deserialize(month_file.read_text(encoding="utf-8"))
            return MemoryGraph()

        graph = MemoryGraph()
        for dot_file in sorted(self._archived.glob("*.dot")):
            content = dot_file.read_text(encoding="utf-8")
            if content.strip():
                graph.merge(deserialize(content))
        return graph

    def list_daily_files(self) -> list[str]:
        return sorted(f.name for f in self._daily.glob("*.dot"))

    def list_archived_files(self) -> list[str]:
        return sorted(f.name for f in self._archived.glob("*.dot"))
