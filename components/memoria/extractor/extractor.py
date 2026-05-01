from __future__ import annotations

import json
from typing import Callable

from memoria.extractor.prompts import EXTRACTION_PROMPT
from memoria.extractor.slug import generate_id
from memoria.graph.edge import Edge
from memoria.graph.graph import MemoryGraph
from memoria.graph.node import Node


class ExtractionResult:
    def __init__(self) -> None:
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []

    def __repr__(self) -> str:
        return (
            f"ExtractionResult(nodes={len(self.nodes)}, edges={len(self.edges)})"
        )


class Extractor:
    def __init__(self, llm_callable: Callable[[str], str]) -> None:
        self._llm = llm_callable

    def extract(
        self, conversation_text: str, existing_graph: MemoryGraph
    ) -> ExtractionResult:
        result = ExtractionResult()

        existing_ids = set(existing_graph.all_node_ids())
        prompt = EXTRACTION_PROMPT.format(
            existing_ids="\n".join(f"- {nid}" for nid in sorted(existing_ids)),
            text=conversation_text,
        )

        response = self._llm(prompt)
        items = self._parse_response(response)

        for item in items:
            content = item.get("content", "").strip()
            label = item.get("label", "").strip()
            connects_to = item.get("connects_to", [])

            if not content:
                continue

            node_id = generate_id(content, existing_ids)
            existing_ids.add(node_id)

            node = Node(
                id=node_id,
                label=label or node_id,
                content=content,
            )
            result.nodes.append(node)

            for target_id in connects_to:
                if target_id in existing_ids or existing_graph.has_node(target_id):
                    result.edges.append(
                        Edge(source_id=node_id, target_id=target_id)
                    )

        return result

    def _parse_response(self, response: str) -> list[dict]:
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            start = 1
            end = len(lines) - 1
            for i, line in enumerate(lines):
                if i > 0 and line.strip().startswith("```"):
                    end = i
                    break
            response = "\n".join(lines[start:end])

        try:
            parsed = json.loads(response)
            if isinstance(parsed, list):
                return parsed
            return []
        except json.JSONDecodeError:
            return []
