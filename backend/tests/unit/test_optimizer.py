"""Unit tests for Phase 6: Optimizer (T6.1 - T6.8)."""

from app.domain.enums import EdgeKind, NodeType
from app.domain.models import Edge, FailureInjection, Graph, Node, Scenario
from app.engine.optimizer import find_knee_point, generate_candidate_mitigations, optimize


def _build_optimizer_graph() -> Graph:
    nodes = [
        Node(id="api", name="API", type=NodeType.GATEWAY, tier=0, user_facing=True, revenue_per_min=50.0),
        Node(id="orders", name="Orders", type=NodeType.SERVICE, tier=0, user_facing=True, revenue_per_min=100.0),
        Node(id="payment", name="Payment", type=NodeType.SERVICE, tier=0, user_facing=True, revenue_per_min=150.0),
        Node(id="db", name="DB", type=NodeType.DATABASE, tier=1),
    ]
    edges = [
        Edge(source="api", target="orders", kind=EdgeKind.SYNC, strength=0.9),
        Edge(source="orders", target="payment", kind=EdgeKind.SYNC, strength=0.9),
        Edge(source="payment", target="db", kind=EdgeKind.DATA, strength=1.0),
    ]
    return Graph(id="opt-graph", name="Optimizer Graph", nodes=nodes, edges=edges)


def test_candidate_generation_relevance_filter() -> None:
    graph = _build_optimizer_graph()
    scenarios = [
        (
            Scenario(
                failures=[FailureInjection(node_id="db", severity=1.0, start_s=0.0)],
                outage_minutes=30.0,
                seed=42,
            ),
            1.0,
        )
    ]
    candidates = generate_candidate_mitigations(graph, scenarios)
    assert len(candidates) > 0
    # Candidates should touch affected nodes
    cand_nodes = {c.target.get("node") for c in candidates if "node" in c.target}
    assert "db" in cand_nodes


def test_find_knee_point_arithmetic() -> None:
    curve = [
        {"cost": 0.0, "expected_loss": 1000.0},
        {"cost": 5.0, "expected_loss": 200.0},   # Sharp drop (knee)
        {"cost": 10.0, "expected_loss": 150.0},  # Diminishing returns
        {"cost": 15.0, "expected_loss": 140.0},
    ]
    knee_idx = find_knee_point(curve)
    assert knee_idx == 1


def test_optimize_greedy_under_budget() -> None:
    graph = _build_optimizer_graph()
    scenarios = [
        (
            Scenario(
                failures=[FailureInjection(node_id="db", severity=1.0, start_s=0.0)],
                outage_minutes=30.0,
                seed=42,
            ),
            1.0,
        )
    ]
    budget = 10.0
    result = optimize(graph=graph, scenarios=scenarios, budget=budget, algorithm="greedy")

    assert "plan" in result
    assert "curve" in result
    assert "knee_index" in result
    assert result["final_loss"] <= result["baseline_loss"]

    # Plan total cost must strictly adhere to budget
    total_cost = sum(p["item"]["cost"] for p in result["plan"])
    assert total_cost <= budget
