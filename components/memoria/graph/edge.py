from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Edge:
    source_id: str
    target_id: str
    relation: str = "connects"

    def to_attrs(self) -> dict[str, str]:
        return {"relation": self.relation}

    @classmethod
    def from_attrs(
        cls, source_id: str, target_id: str, attrs: dict[str, str]
    ) -> Edge:
        return cls(
            source_id=source_id,
            target_id=target_id,
            relation=attrs.get("relation", "connects"),
        )
