
from memoria.graph.edge import Edge
from memoria.graph.graph import MemoryGraph
from memoria.graph.node import Node
from memoria.retrieval.retriever import Retriever


def _build_graph() -> MemoryGraph:
    g = MemoryGraph()
    g.add_node(
        Node(
            id="python_decorators",
            label="Decorators",
            content="Decorators wrap functions",
        )
    )
    g.add_node(
        Node(
            id="python_functions",
            label="Functions",
            content="Functions are first-class objects",
        )
    )
    g.add_node(
        Node(
            id="python_closures",
            label="Closures",
            content="Closures capture variables from scope",
        )
    )
    g.add_edge(Edge(source_id="python_decorators", target_id="python_functions"))
    g.add_edge(Edge(source_id="python_closures", target_id="python_functions"))
    return g


class TestRetriever:
    def test_retrieve_basic(self):
        retriever = Retriever()
        results = retriever.retrieve(_build_graph(), "decorators")
        assert len(results) >= 1
        assert results[0].node.id == "python_decorators"

    def test_retrieve_returns_neighbors(self):
        retriever = Retriever()
        results = retriever.retrieve(_build_graph(), "decorators")
        assert len(results[0].neighbors) >= 1

    def test_retrieve_top_k(self):
        retriever = Retriever()
        results = retriever.retrieve(_build_graph(), "python", top_k=1)
        assert len(results) <= 1

    def test_retrieve_empty_query(self):
        retriever = Retriever()
        results = retriever.retrieve(_build_graph(), "")
        assert len(results) == 0

    def test_retrieve_no_match(self):
        retriever = Retriever()
        results = retriever.retrieve(
            _build_graph(), "javascript promises async"
        )
        assert len(results) == 0

    def test_retrieve_context_dict(self):
        retriever = Retriever()
        context = retriever.retrieve_context(
            _build_graph(), "functions", top_k=5
        )
        assert isinstance(context, list)
        assert len(context) >= 1
        assert "id" in context[0]
        assert "related" in context[0]

    def test_retrieve_scores_by_activation(self):
        g = _build_graph()
        for nid, node in g.nodes.items():
            if nid == "python_decorators":
                node.activation_score = 0.1
        retriever = Retriever()
        results = retriever.retrieve(g, "python", top_k=5)
        if len(results) >= 2:
            assert results[0].node.id != "python_decorators"
