from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


def _generate_id() -> str:
    return uuid.uuid4().hex[:8]


@dataclass
class Node:
    id: str
    label: str
    content: str
    activation_score: float = 1.0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())

    def touch(self) -> None:
        self.last_accessed = datetime.now().isoformat()

    def to_attrs(self) -> dict[str, str]:
        return {
            "label": self.label,
            "content": self.content,
            "score": str(self.activation_score),
            "created": self.created_at,
            "accessed": self.last_accessed,
        }

    @classmethod
    def from_attrs(cls, node_id: str, attrs: dict[str, str]) -> Node:
        return cls(
            id=node_id,
            label=attrs.get("label", node_id),
            content=attrs.get("content", ""),
            activation_score=float(attrs.get("score", "1.0")),
            created_at=attrs.get("created", datetime.now().isoformat()),
            last_accessed=attrs.get("accessed", datetime.now().isoformat()),
        )
