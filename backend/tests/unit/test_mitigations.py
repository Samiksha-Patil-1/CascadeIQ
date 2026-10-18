"""Unit tests for Phase 5: Mitigations and compare (T5.1 - T5.5)."""

from app.domain.enums import EdgeKind, MitigationType, NodeType
from app.domain.models import Edge, FailureInjection, Graph, MitigationItem, Node, Scenario
from app.engine.metrics import summarize
from app.engine.mitigations import apply, get_mitigation_catalog
from app.engine.propagation import simulate


def test_mitigation_catalog_has_all_archetypes() -> None:
    catalog = get_mitigation_catalog()
    assert len(catalog) >= 7
    types = {item["type"] for item in catalog}
    assert "circuit_breaker" in types
    assert "fallback_cache" in types
    assert "bulkhead" in types
    assert "async_decouple" in types
    assert "add_replica_failover" in types


def test_apply_immutability_rule() -> None:
    """Domain Rule 6: Engine never mutates its input graph. Mitigations return a new graph."""
    node = Node(id="srv", name="Srv", type=NodeType.SERVICE, tier=0, failover_quality=0.0, replicas=1)
    graph = Graph(id="imm-test", name="Immutable Test", nodes=[node], edges=[])

    item = MitigationItem(
        id="mit-1",
        type=MitigationType.ADD_REPLICA_FAILOVER,
        target={"node": "srv"},
        cost=5.0,
    )
    mit_graph = apply(graph, [item])

    # Original graph must remain completely untouched
    assert graph.nodes[0].replicas == 1
    assert graph.nodes[0].failover_quality == 0.0

    # New graph has updated values
    assert mit_graph.nodes[0].replicas == 2
    assert mit_graph.nodes[0].failover_quality > 0.0
    assert mit_graph.id == "imm-test-mitigated"


def test_property_mitigation_never_increases_outage_cost() -> None:
    """Property test T5.4: Adding a mitigation never increases outage cost."""
    nodes = [
        Node(id="app", name="App", type=NodeType.SERVICE, tier=0, user_facing=True, revenue_per_min=100.0),
        Node(id="db", name="DB", type=NodeType.DATABASE, tier=1),
    ]
    edges = [
        Edge(source="app", target="db", kind=EdgeKind.SYNC, strength=1.0),
    ]
    graph = Graph(id="prop-test", name="Property Test", nodes=nodes, edges=edges)

    scenario = Scenario(
        failures=[FailureInjection(node_id="db", severity=1.0, start_s=0.0)],
        outage_minutes=30.0,
        seed=42,
    )

    base_sim = simulate(graph, scenario)
    base_cost = summarize(base_sim, graph, scenario)["outage_cost"]

    # Add circuit breaker
    cb_item = MitigationItem(
        id="mit-cb",
        type=MitigationType.CIRCUIT_BREAKER,
        target={"edge": ["app", "db"]},
        cost=3.0,
    )
    mit_graph = apply(graph, [cb_item])
    mit_sim = simulate(mit_graph, scenario)
    mit_cost = summarize(mit_sim, mit_graph, scenario)["outage_cost"]

    assert mit_cost <= base_cost, f"Mitigation increased loss from {base_cost} to {mit_cost}!"


def test_break_cycle_mitigation() -> None:
    nodes = [
        Node(id="srv-1", name="S1", type=NodeType.SERVICE, tier=1),
        Node(id="srv-2", name="S2", type=NodeType.SERVICE, tier=1),
    ]
    edges = [
        Edge(source="srv-1", target="srv-2", kind=EdgeKind.SYNC),
        Edge(source="srv-2", target="srv-1", kind=EdgeKind.SYNC),
    ]
    graph = Graph(id="cycle-break-test", name="Cycle Break Test", nodes=nodes, edges=edges)

    item = MitigationItem(
        id="break-1",
        type=MitigationType.BREAK_CYCLE,
        target={"edge": ["srv-2", "srv-1"]},
        cost=5.0,
    )
    new_graph = apply(graph, [item])
    assert len(new_graph.edges) == 1
    assert new_graph.edges[0].source == "srv-1"
    assert new_graph.edges[0].target == "srv-2"
