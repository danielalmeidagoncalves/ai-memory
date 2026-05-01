from __future__ import annotations

from typing import Callable

from memoria.extractor.extractor import ExtractionResult, Extractor
from memoria.gardener.gardener import Gardener
from memoria.gardener.scheduler import MemoryScheduler
from memoria.graph.dot_serializer import serialize
from memoria.graph.edge import Edge
from memoria.graph.graph import MemoryGraph
from memoria.graph.node import Node
from memoria.retrieval.retriever import Retriever
from memoria.scoring.config import ScoringConfig
from memoria.scoring.scorer import Scorer
from memoria.storage.file_store import FileStore


class MemoryAPI:
    def __init__(
        self,
        storage_path: str | None = None,
        llm_callable: Callable[[str], str] | None = None,
        scoring_config: ScoringConfig | None = None,
    ) -> None:
        self._store = FileStore(storage_path)
        self._config = scoring_config or ScoringConfig()
        self._scorer = Scorer(self._config)
        self._gardener = Gardener(self._store, self._scorer, self._config)
        self._scheduler: MemoryScheduler | None = None
        self._retriever = Retriever()
        self._extractor: Extractor | None = None
        if llm_callable is not None:
            self._extractor = Extractor(llm_callable)

    def store(
        self,
        id: str,
        content: str,
        label: str | None = None,
        connects_to: list[str] | None = None,
    ) -> Node:
        graph = self._store.load_active()
        existing_ids = set(graph.all_node_ids())
        from memoria.extractor.slug import deduplicate_slug

        final_id = deduplicate_slug(id, existing_ids)

        node = Node(id=final_id, label=label or final_id, content=content)
        graph.add_node(node)

        if connects_to:
            for target_id in connects_to:
                if graph.has_node(target_id) or final_id != target_id:
                    graph.add_edge(Edge(source_id=final_id, target_id=target_id))

        self._store.save_active(graph)
        return node

    def extract(self, conversation_text: str) -> ExtractionResult:
        if self._extractor is None:
            raise ValueError(
                "Cannot extract without an llm_callable. "
                "Provide one in the MemoryAPI constructor."
            )
        graph = self._store.load_active()
        result = self._extractor.extract(conversation_text, graph)

        for node in result.nodes:
            graph.add_node(node)
        for edge in result.edges:
            graph.add_edge(edge)

        self._store.save_active(graph)
        return result

    def retrieve(
        self, query: str, top_k: int = 10
    ) -> list[dict]:
        graph = self._store.load_active()
        return self._retriever.retrieve_context(graph, query, top_k)

    def garden(self) -> dict[str, int]:
        self._gardener.run()
        return self._gardener.get_stats()

    def start_scheduler(self, interval_seconds: int = 3600) -> None:
        if self._scheduler is not None:
            self.stop_scheduler()
        self._scheduler = MemoryScheduler(self._gardener)
        self._scheduler.start(interval_seconds)

    def stop_scheduler(self) -> None:
        if self._scheduler is not None:
            self._scheduler.stop()
            self._scheduler = None

    @property
    def scheduler_running(self) -> bool:
        return self._scheduler is not None and self._scheduler.is_running

    def export_dot(self) -> str:
        graph = self._store.load_active()
        return serialize(graph)

    def get_node(self, id: str) -> Node | None:
        graph = self._store.load_active()
        return graph.get_node(id)

    def connect(self, source_id: str, target_id: str) -> Edge | None:
        graph = self._store.load_active()
        edge = graph.add_edge(Edge(source_id=source_id, target_id=target_id))
        if edge is not None:
            self._store.save_active(graph)
        return edge

    def get_graph(self) -> MemoryGraph:
        return self._store.load_active()

    def remove_node(self, node_id: str) -> Node | None:
        graph = self._store.load_active()
        node = graph.remove_node(node_id)
        if node is not None:
            self._store.save_active(graph)
        return node

    def list_nodes(self) -> list[dict]:
        graph = self._store.load_active()
        return [
            {
                "id": n.id,
                "label": n.label,
                "score": n.activation_score,
            }
            for n in graph.nodes.values()
        ]
