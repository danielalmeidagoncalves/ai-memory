from __future__ import annotations

from dataclasses import dataclass

from memoria.graph.graph import MemoryGraph
from memoria.graph.node import Node


@dataclass
class RetrievalResult:
    node: Node
    neighbors: list[Node]
    relevance_score: float


class Retriever:
    def retrieve(
        self,
        graph: MemoryGraph,
        query: str,
        top_k: int = 10,
    ) -> list[RetrievalResult]:
        if not query.strip():
            return []

        query_tokens = set(query.lower().split())
        scored: list[tuple[str, float]] = []

        for nid, node in graph.nodes.items():
            match_score = self._match_score(node, query_tokens)
            combined = match_score * node.activation_score
            if combined > 0:
                scored.append((nid, combined))

        scored.sort(key=lambda x: x[1], reverse=True)
        top_ids = scored[:top_k]

        results: list[RetrievalResult] = []
        for nid, score in top_ids:
            node = graph.get_node(nid)
            if node:
                neighbors = graph.get_neighbors(nid)
                results.append(
                    RetrievalResult(
                        node=node,
                        neighbors=neighbors,
                        relevance_score=score,
                    )
                )

        return results

    def _match_score(self, node: Node, query_tokens: set[str]) -> float:
        content_tokens = set(node.content.lower().split())
        label_tokens = set(node.label.lower().split())
        id_tokens = set(node.id.lower().split("_"))

        all_tokens = content_tokens | label_tokens | id_tokens
        if not all_tokens:
            return 0.0

        matches = query_tokens & all_tokens
        return len(matches) / len(query_tokens) if query_tokens else 0.0

    def retrieve_context(
        self,
        graph: MemoryGraph,
        query: str,
        top_k: int = 10,
    ) -> list[dict]:
        results = self.retrieve(graph, query, top_k)
        context: list[dict] = []
        for r in results:
            entry = {
                "id": r.node.id,
                "label": r.node.label,
                "content": r.node.content,
                "score": r.relevance_score,
                "related": [
                    {"id": n.id, "label": n.label, "content": n.content}
                    for n in r.neighbors
                ],
            }
            context.append(entry)
        return context
