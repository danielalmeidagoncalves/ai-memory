from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoringConfig:
    decay_rate: float = 0.05
    archive_threshold: float = 0.1
    reinforcement_boost: float = 0.2
    connection_bonus_factor: float = 0.05
    max_score: float = 1.0
    min_score: float = 0.0
