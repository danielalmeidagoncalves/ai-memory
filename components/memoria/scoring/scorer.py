from __future__ import annotations

from datetime import datetime

from memoria.graph.graph import MemoryGraph
from memoria.scoring.config import ScoringConfig


class Scorer:
    def __init__(self, config: ScoringConfig | None = None) -> None:
        self._config = config or ScoringConfig()

    @property
    def config(self) -> ScoringConfig:
        return self._config

    def decay(self, current_score: float, days_elapsed: float) -> float:
        exponent = -self._config.decay_rate * days_elapsed
        new_score = current_score * pow(2.71828, exponent)
        return max(self._config.min_score, new_score)

    def reinforce(self, current_score: float) -> float:
        boosted = current_score + self._config.reinforcement_boost
        return min(self._config.max_score, boosted)

    def connection_boost(self, graph: MemoryGraph, node_id: str) -> float:
        neighbors = graph.get_neighbors(node_id)
        if not neighbors:
            return 0.0
        avg_neighbor_score = sum(n.activation_score for n in neighbors) / len(neighbors)
        return avg_neighbor_score * self._config.connection_bonus_factor

    def _days_since(self, iso_timestamp: str) -> float:
        try:
            accessed = datetime.fromisoformat(iso_timestamp)
            delta = datetime.now() - accessed
            return delta.total_seconds() / 86400.0
        except (ValueError, TypeError):
            return 0.0

    def score_all(self, graph: MemoryGraph) -> dict[str, float]:
        new_scores: dict[str, float] = {}
        for nid, node in graph.nodes.items():
            days = self._days_since(node.last_accessed)
            decayed = self.decay(node.activation_score, days)
            boost = self.connection_boost(graph, nid)
            new_scores[nid] = min(self._config.max_score, decayed + boost)
        return new_scores

    def apply_scores(self, graph: MemoryGraph) -> None:
        scores = self.score_all(graph)
        for nid, score in scores.items():
            node = graph.get_node(nid)
            if node:
                node.activation_score = round(score, 6)

    def below_threshold(self, graph: MemoryGraph) -> list[str]:
        self.apply_scores(graph)
        return [
            nid
            for nid, node in graph.nodes.items()
            if node.activation_score < self._config.archive_threshold
        ]
