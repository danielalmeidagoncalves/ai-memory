
from memoria.graph.dot_serializer import deserialize, serialize
from memoria.graph.edge import Edge
from memoria.graph.graph import MemoryGraph
from memoria.graph.node import Node


class TestNode:
    def test_create_node_defaults(self):
        node = Node(id="test", label="Test", content="hello world")
        assert node.id == "test"
        assert node.activation_score == 1.0
        assert node.created_at is not None
        assert node.last_accessed is not None

    def test_touch_updates_accessed(self):
        node = Node(id="test", label="Test", content="hello")
        old_accessed = node.last_accessed
        node.touch()
        assert node.last_accessed >= old_accessed

    def test_to_attrs_roundtrip(self):
        node = Node(id="test", label="Test", content="hello", activation_score=0.75)
        attrs = node.to_attrs()
        restored = Node.from_attrs("test", attrs)
        assert restored.id == node.id
        assert restored.label == node.label
        assert restored.content == node.content
        assert abs(restored.activation_score - 0.75) < 0.001


class TestEdge:
    def test_create_edge(self):
        edge = Edge(source_id="a", target_id="b")
        assert edge.source_id == "a"
        assert edge.target_id == "b"
        assert edge.relation == "connects"

    def test_edge_attrs_roundtrip(self):
        edge = Edge(source_id="a", target_id="b", relation="relates_to")
        attrs = edge.to_attrs()
        restored = Edge.from_attrs("a", "b", attrs)
        assert restored.relation == "relates_to"


class TestMemoryGraph:
    def test_add_and_get_node(self):
        g = MemoryGraph()
        node = Node(id="n1", label="N1", content="content")
        g.add_node(node)
        assert g.get_node("n1") is not None
        assert g.node_count() == 1

    def test_remove_node(self):
        g = MemoryGraph()
        g.add_node(Node(id="n1", label="N1", content="c"))
        g.add_node(Node(id="n2", label="N2", content="c"))
        g.add_edge(Edge(source_id="n1", target_id="n2"))
        g.remove_node("n1")
        assert g.get_node("n1") is None
        assert g.edge_count() == 0

    def test_add_edge(self):
        g = MemoryGraph()
        g.add_node(Node(id="a", label="A", content="c"))
        g.add_node(Node(id="b", label="B", content="c"))
        edge = g.add_edge(Edge(source_id="a", target_id="b"))
        assert edge is not None
        assert g.edge_count() == 1

    def test_add_edge_missing_node(self):
        g = MemoryGraph()
        g.add_node(Node(id="a", label="A", content="c"))
        result = g.add_edge(Edge(source_id="a", target_id="missing"))
        assert result is None

    def test_no_duplicate_edges(self):
        g = MemoryGraph()
        g.add_node(Node(id="a", label="A", content="c"))
        g.add_node(Node(id="b", label="B", content="c"))
        g.add_edge(Edge(source_id="a", target_id="b"))
        g.add_edge(Edge(source_id="a", target_id="b"))
        assert g.edge_count() == 1

    def test_get_neighbors(self):
        g = MemoryGraph()
        g.add_node(Node(id="a", label="A", content="c"))
        g.add_node(Node(id="b", label="B", content="c"))
        g.add_node(Node(id="c", label="C", content="c"))
        g.add_edge(Edge(source_id="a", target_id="b"))
        g.add_edge(Edge(source_id="c", target_id="a"))
        neighbors = g.get_neighbors("a")
        neighbor_ids = [n.id for n in neighbors]
        assert "b" in neighbor_ids
        assert "c" in neighbor_ids

    def test_get_subgraph(self):
        g = MemoryGraph()
        g.add_node(Node(id="a", label="A", content="c"))
        g.add_node(Node(id="b", label="B", content="c"))
        g.add_node(Node(id="c", label="C", content="c"))
        g.add_edge(Edge(source_id="a", target_id="b"))
        g.add_edge(Edge(source_id="b", target_id="c"))
        sub = g.get_subgraph(["a", "b"])
        assert sub.node_count() == 2
        assert sub.edge_count() == 1

    def test_merge(self):
        g1 = MemoryGraph()
        g1.add_node(Node(id="a", label="A", content="c"))
        g2 = MemoryGraph()
        g2.add_node(Node(id="b", label="B", content="c"))
        g1.merge(g2)
        assert g1.node_count() == 2

    def test_is_orphan(self):
        g = MemoryGraph()
        g.add_node(Node(id="a", label="A", content="c"))
        g.add_node(Node(id="b", label="B", content="c"))
        g.add_edge(Edge(source_id="a", target_id="b"))
        assert g.is_orphan("a") is False
        g.add_node(Node(id="lonely", label="L", content="c"))
        assert g.is_orphan("lonely") is True


class TestDotSerializer:
    def test_roundtrip(self):
        g = MemoryGraph()
        g.add_node(
            Node(id="python_decorators", label="Decorators", content="wrap functions")
        )
        g.add_node(
            Node(
                id="python_functions",
                label="Functions",
                content="first class",
            )
        )
        g.add_edge(Edge(source_id="python_decorators", target_id="python_functions"))
        dot = serialize(g)
        assert "digraph memory" in dot
        assert "python_decorators" in dot

        restored = deserialize(dot)
        assert restored.node_count() == 2
        assert restored.edge_count() == 1
        node = restored.get_node("python_decorators")
        assert node is not None
        assert node.content == "wrap functions"

    def test_empty_graph(self):
        g = MemoryGraph()
        dot = serialize(g)
        restored = deserialize(dot)
        assert restored.node_count() == 0

    def test_special_characters_in_content(self):
        g = MemoryGraph()
        g.add_node(
            Node(
                id="test",
                label="Test",
                content='He said "hello" and left\\nwith a newline',
            )
        )
        dot = serialize(g)
        restored = deserialize(dot)
        node = restored.get_node("test")
        assert node is not None
        assert '"hello"' in node.content
