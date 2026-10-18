"""Unit tests for Phase 7: Vectorized Monte Carlo simulation (T7.1 - T7.3)."""

from app.domain.enums import EdgeKind, NodeType
from app.domain.models import Edge, FailureInjection, Graph, Node, Scenario
from app.engine.montecarlo import simulate_mc


def test_simulate_monte_carlo_crn_reproducibility() -> None:
    nodes = [
        Node(id="api", name="API", type=NodeType.GATEWAY, tier=0),
        Node(id="auth", name="Auth", type=NodeType.SERVICE, tier=1),
        Node(id="db", name="DB", type=NodeType.DATABASE, tier=2),
    ]
    edges = [
        Edge(source="api", target="auth", kind=EdgeKind.SYNC, strength=0.8),
        Edge(source="auth", target="db", kind=EdgeKind.DATA, strength=0.9),
    ]
    graph = Graph(id="mc-test", name="MC Test", nodes=nodes, edges=edges)
    scenario = Scenario(
        failures=[FailureInjection(node_id="db", severity=1.0, start_s=0.0)],
        outage_minutes=30.0,
        seed=123,
    )

    res1 = simulate_mc(graph, scenario, trials=500, seed=123)
    res2 = simulate_mc(graph, scenario, trials=500, seed=123)

    # Identical seed and CRN must produce identical probabilities
    assert res1["p_fail"] == res2["p_fail"]
    assert res1["mean_affected"] == res2["mean_affected"]

    # Injected root db must fail with probability ~1.0
    assert res1["p_fail"]["db"] >= 0.95

    # Check 95% Confidence Intervals bounds
    for nid, (ci_low, ci_high) in res1["ci95"].items():
        assert 0.0 <= ci_low <= 1.0
        assert 0.0 <= ci_high <= 1.0
        assert ci_low <= ci_high
        p = res1["p_fail"][nid]
        assert ci_low <= p <= ci_high
