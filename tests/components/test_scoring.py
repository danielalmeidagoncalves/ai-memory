
from memoria.graph.edge import Edge
from memoria.graph.graph import MemoryGraph
from memoria.graph.node import Node
from memoria.scoring.config import ScoringConfig
from memoria.scoring.scorer import Scorer


class TestScoringConfig:
    def test_defaults(self):
        config = ScoringConfig()
        assert config.decay_rate == 0.05
        assert config.archive_threshold == 0.1
        assert config.reinforcement_boost == 0.2


class TestScorer:
    def test_decay_reduces_score(self):
        scorer = Scorer()
        new_score = scorer.decay(1.0, 10.0)
        assert new_score < 1.0
        assert new_score > 0.0

    def test_decay_zero_days(self):
        scorer = Scorer()
        new_score = scorer.decay(0.8, 0.0)
        assert abs(new_score - 0.8) < 0.001

    def test_reinforce_caps_at_max(self):
        scorer = Scorer()
        boosted = scorer.reinforce(0.95)
        assert boosted == 1.0

    def test_connection_boost_no_neighbors(self):
        scorer = Scorer()
        g = MemoryGraph()
        g.add_node(Node(id="lonely", label="L", content="c"))
        boost = scorer.connection_boost(g, "lonely")
        assert boost == 0.0

    def test_connection_boost_with_neighbors(self):
        scorer = Scorer()
        g = MemoryGraph()
        g.add_node(Node(id="a", label="A", content="c", activation_score=0.8))
        g.add_node(Node(id="b", label="B", content="c", activation_score=0.6))
        g.add_edge(Edge(source_id="a", target_id="b"))
        boost = scorer.connection_boost(g, "a")
        assert boost > 0.0

    def test_score_all(self):
        scorer = Scorer(ScoringConfig(decay_rate=0.0))
        g = MemoryGraph()
        g.add_node(Node(id="n1", label="N1", content="c", activation_score=0.5))
        scores = scorer.score_all(g)
        assert "n1" in scores
        assert scores["n1"] >= 0.0

    def test_below_threshold(self):
        config = ScoringConfig(archive_threshold=0.5, decay_rate=0.0)
        scorer = Scorer(config)
        g = MemoryGraph()
        g.add_node(Node(id="high", label="H", content="c", activation_score=0.9))
        g.add_node(Node(id="low", label="L", content="c", activation_score=0.1))
        below = scorer.below_threshold(g)
        assert "low" in below
        assert "high" not in below
