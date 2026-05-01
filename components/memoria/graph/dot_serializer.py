from __future__ import annotations

import re

import graphviz as gv
from memoria.graph.edge import Edge
from memoria.graph.graph import MemoryGraph
from memoria.graph.node import Node


def _sanitize_dot_value(value: str) -> str:
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace('"', '\\"')
    escaped = escaped.replace("\n", "\\n")
    return escaped


def _unsanitize_dot_value(value: str) -> str:
    unescaped = value.replace("\\n", "\n")
    unescaped = unescaped.replace('\\"', '"')
    unescaped = unescaped.replace("\\\\", "\\")
    return unescaped


def _attrs_to_dot_str(attrs: dict[str, str]) -> str:
    parts = []
    for key, val in attrs.items():
        parts.append(f'{key}="{_sanitize_dot_value(val)}"')
    return " [" + ", ".join(parts) + "]"


def _parse_attrs(attr_str: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    pattern = r'(\w+)="((?:[^"\\]|\\.)*)"'
    for match in re.finditer(pattern, attr_str):
        attrs[match.group(1)] = _unsanitize_dot_value(match.group(2))
    return attrs


def serialize(graph: MemoryGraph) -> str:
    lines = ["digraph memory {"]
    for nid, node in graph.nodes.items():
        attr_str = _attrs_to_dot_str(node.to_attrs())
        lines.append(f"    {nid}{attr_str}")
    for edge in graph.edges:
        attr_str = _attrs_to_dot_str(edge.to_attrs())
        lines.append(f"    {edge.source_id} -> {edge.target_id}{attr_str}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def deserialize(dot_content: str) -> MemoryGraph:
    graph = MemoryGraph()
    in_graph = False
    for line in dot_content.splitlines():
        stripped = line.strip()
        if stripped == "digraph memory {":
            in_graph = True
            continue
        if stripped == "}":
            break
        if not in_graph or not stripped:
            continue

        if "->" in stripped:
            parts = stripped.split("->", 1)
            source_id = parts[0].strip()
            rest = parts[1].strip()
            bracket_idx = rest.find("[")
            if bracket_idx >= 0:
                target_id = rest[:bracket_idx].strip()
                attr_str = rest[bracket_idx:]
                attrs = _parse_attrs(attr_str)
                graph.add_edge(Edge.from_attrs(source_id, target_id, attrs))
            else:
                target_id = rest.strip().rstrip(";")
                graph.add_edge(Edge(source_id=source_id, target_id=target_id))
        else:
            bracket_idx = stripped.find("[")
            if bracket_idx >= 0:
                node_id = stripped[:bracket_idx].strip()
                attr_str = stripped[bracket_idx:]
                attrs = _parse_attrs(attr_str)
                graph.add_node(Node.from_attrs(node_id, attrs))

    return graph


def to_graphviz(graph: MemoryGraph) -> gv.Digraph:
    dot = gv.Digraph(name="memory")
    for nid, node in graph.nodes.items():
        dot.node(nid, label=node.label, **{"tooltip": node.content})
    for edge in graph.edges:
        dot.edge(edge.source_id, edge.target_id, label=edge.relation)
    return dot
