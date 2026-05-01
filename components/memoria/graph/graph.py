from __future__ import annotations

from typing import Optional

from memoria.graph.edge import Edge
from memoria.graph.node import Node


class MemoryGraph:
    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []

    @property
    def nodes(self) -> dict[str, Node]:
        return dict(self._nodes)

    @property
    def edges(self) -> list[Edge]:
        return list(self._edges)

    def add_node(self, node: Node) -> Node:
        self._nodes[node.id] = node
        return node

    def get_node(self, node_id: str) -> Optional[Node]:
        node = self._nodes.get(node_id)
        if node is not None:
            node.touch()
        return node

    def remove_node(self, node_id: str) -> Optional[Node]:
        node = self._nodes.pop(node_id, None)
        if node is not None:
            self._edges = [
                e
                for e in self._edges
                if e.source_id != node_id and e.target_id != node_id
            ]
        return node

    def add_edge(self, edge: Edge) -> Optional[Edge]:
        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            return None
        for existing in self._edges:
            if (
                existing.source_id == edge.source_id
                and existing.target_id == edge.target_id
            ):
                return existing
        self._edges.append(edge)
        return edge

    def get_neighbors(self, node_id: str) -> list[Node]:
        neighbor_ids: set[str] = set()
        for edge in self._edges:
            if edge.source_id == node_id:
                neighbor_ids.add(edge.target_id)
            elif edge.target_id == node_id:
                neighbor_ids.add(edge.source_id)
        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def get_edges_for(self, node_id: str) -> list[Edge]:
        return [
            e
            for e in self._edges
            if e.source_id == node_id or e.target_id == node_id
        ]

    def get_subgraph(self, node_ids: list[str]) -> MemoryGraph:
        sub = MemoryGraph()
        for nid in node_ids:
            node = self._nodes.get(nid)
            if node:
                sub.add_node(Node(**node.__dict__))
        for edge in self._edges:
            if edge.source_id in sub._nodes and edge.target_id in sub._nodes:
                sub.add_edge(Edge(**edge.__dict__))
        return sub

    def has_node(self, node_id: str) -> bool:
        return node_id in self._nodes

    def has_edge(self, source_id: str, target_id: str) -> bool:
        return any(
            e.source_id == source_id and e.target_id == target_id
            for e in self._edges
        )

    def merge(self, other: MemoryGraph) -> None:
        for nid, node in other._nodes.items():
            if nid not in self._nodes:
                self._nodes[nid] = node
        for edge in other._edges:
            self.add_edge(edge)

    def node_count(self) -> int:
        return len(self._nodes)

    def edge_count(self) -> int:
        return len(self._edges)

    def all_node_ids(self) -> list[str]:
        return list(self._nodes.keys())

    def is_orphan(self, node_id: str) -> bool:
        return all(
            e.source_id != node_id and e.target_id != node_id for e in self._edges
        )
