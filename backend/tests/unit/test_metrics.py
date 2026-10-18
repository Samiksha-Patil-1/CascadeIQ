"""Unit tests for Phase 4: Metrics and risk ranking (T4.1 - T4.4)."""

import pytest

from app.domain.enums import EdgeKind, NodeType
from app.domain.models import Edge, FailureInjection, Graph, Node, Scenario
from app.engine.metrics import summarize
from app.engine.propagation import simulate
from app.engine.risk import rank_risk


def test_summarize_metrics_hand_computed() -> None:
    # 1 capability node with revenue_per_min = 100.0, users_per_min = 50.0
    # 1 backend database
    nodes = [
        Node(
            id="checkout",
            name="Checkout",
            type=NodeType.SERVICE,
            tier=0,
            user_facing=True,
            revenue_per_min=100.0,
            users_per_min=50.0,
            slo_floor=0.99,
            degrade_threshold=0.2,
            fail_threshold=0.6,
        ),
        Node(
            id="db",
            name="DB",
            type=NodeType.DATABASE,
            tier=1,
            user_facing=False,
            degrade_threshold=0.2,
            fail_threshold=0.6,
        ),
    ]
    edges = [
        Edge(source="checkout", target="db", kind=EdgeKind.SYNC, strength=1.0, delay_s=0.0),
    ]
    graph = Graph(id="metrics-test", name="Metrics Test", nodes=nodes, edges=edges)

    # Inject DB at severity 1.0 for 30 minutes
    scenario = Scenario(
        failures=[FailureInjection(node_id="db", severity=1.0, start_s=0.0)],
        outage_minutes=30.0,
        seed=42,
    )
    sim = simulate(graph, scenario)
    summary = summarize(sim, graph, scenario)

    # Hand arithmetic:
    # - DB damage = 1.0 -> Failed
    # - Checkout damage = 1.0 -> Failed
    # - affected: 2
    # - failed: 2
    # - users_impacted: 50.0 * 1.0 = 50.0
    # - money_per_hour: 60 * (100.0 * 1.0) = $6,000.00
    # - outage_cost: 100.0 * 30 min * 1.0 = $3,000.00
    # - slo_breaches: 2
    assert summary["affected"] == 2
    assert summary["failed"] == 2
    assert pytest.approx(summary["users_impacted"], 0.1) == 50.0
    assert pytest.approx(summary["money_per_hour"], 0.1) == 6000.0
    assert pytest.approx(summary["outage_cost"], 0.1) == 3000.0
    assert summary["slo_breaches"] == 2


def test_rank_risk_order() -> None:
    # DB failure costs $3,000 per incident; leaf cache failure costs nothing
    nodes = [
        Node(
            id="storefront",
            name="Storefront",
            type=NodeType.SERVICE,
            tier=0,
            revenue_per_min=200.0,
            mtbf_hours=1000.0,
            mttr_minutes=60.0,
        ),
        Node(
            id="core-db",
            name="Core DB",
            type=NodeType.DATABASE,
            tier=1,
            mtbf_hours=500.0,
            mttr_minutes=30.0,
        ),
    ]
    edges = [
        Edge(source="storefront", target="core-db", kind=EdgeKind.DATA, strength=1.0),
    ]
    graph = Graph(id="risk-test", name="Risk Test", nodes=nodes, edges=edges)

    rankings = rank_risk(graph)
    assert len(rankings) == 2
    # Both storefront and core-db are ranked
    assert rankings[0]["rank"] == 1
    assert rankings[1]["rank"] == 2
    # The AEL must be positive
    assert rankings[0]["ael"] > 0
