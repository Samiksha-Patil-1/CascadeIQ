"""Unit tests for Phase 3: Deterministic propagation (T3.1 - T3.6)."""

import pytest

from app.domain.enums import EdgeKind, MitigationType, NodeState, NodeType
from app.domain.models import Edge, FailureInjection, Graph, Node, Scenario
from app.engine.graph_io import IndexedGraph
from app.engine.propagation import compute_edge_tau, simulate


def test_compute_edge_tau_with_mitigations() -> None:
    # edge with strength 0.8, sync (kappa=1.0)
    # circuit_breaker (0.35) and fallback_cache (0.60)
    # m = 1 - (1 - 0.35) * (1 - 0.60) = 1 - 0.65 * 0.40 = 0.74
    # tau = 0.8 * 1.0 * (1 - 0.74) = 0.208
    node_a = Node(id="node-a", name="A", type=NodeType.SERVICE, tier=0)
    node_b = Node(id="node-b", name="B", type=NodeType.SERVICE, tier=1)
    edge = Edge(
        source="node-a",
        target="node-b",
        kind=EdgeKind.SYNC,
        strength=0.8,
        mitigations=[MitigationType.CIRCUIT_BREAKER.value, MitigationType.FALLBACK_CACHE.value],
    )
    graph = Graph(id="tau-test", name="Tau Test", nodes=[node_a, node_b], edges=[edge])
    indexed = IndexedGraph(graph)
    indexed_edge = indexed.provider_edges(indexed.to_index("node-a"))[0]

    tau = compute_edge_tau(indexed_edge)
    assert pytest.approx(tau, 1e-4) == 0.208


def test_propagation_monotonicity_and_cycle_safety() -> None:
    """Invariant 3: Damage never decreases. Cycle graph must terminate safely within MAX_EVENTS."""
    nodes = [
        Node(id="loop-a", name="Loop A", type=NodeType.SERVICE, tier=1),
        Node(id="loop-b", name="Loop B", type=NodeType.SERVICE, tier=1),
    ]
    edges = [
        Edge(source="loop-a", target="loop-b", kind=EdgeKind.SYNC, strength=0.9, delay_s=1.0),
        Edge(source="loop-b", target="loop-a", kind=EdgeKind.SYNC, strength=0.9, delay_s=1.0),
    ]
    graph = Graph(id="loop-test", name="Loop Test", nodes=nodes, edges=edges)
    scenario = Scenario(
        failures=[FailureInjection(node_id="loop-a", severity=1.0, start_s=0.0)],
        outage_minutes=30.0,
        seed=42,
    )
    result = simulate(graph, scenario)

    # Simulation must terminate
    assert result.run_id.startswith("run-")
    assert result.nodes["loop-a"].damage <= 1.0
    assert result.nodes["loop-b"].damage <= 1.0

    # Check timeline monotonicity per node
    node_damages: dict[str, float] = {}
    for ev in result.timeline:
        prev = node_damages.get(ev.node_id, 0.0)
        assert ev.damage >= prev - 1e-6, "Damage decreased during propagation!"
        node_damages[ev.node_id] = ev.damage


def test_alternative_provider_groups_redundancy() -> None:
    """When two providers share a group, failure of ONE provider should NOT degrade the caller."""
    nodes = [
        Node(id="client", name="Client", type=NodeType.SERVICE, tier=0),
        Node(id="replica-1", name="Replica 1", type=NodeType.DATABASE, tier=1),
        Node(id="replica-2", name="Replica 2", type=NodeType.DATABASE, tier=1),
    ]
    edges = [
        Edge(source="client", target="replica-1", kind=EdgeKind.DATA, strength=1.0, group="db-pool"),
        Edge(source="client", target="replica-2", kind=EdgeKind.DATA, strength=1.0, group="db-pool"),
    ]
    graph = Graph(id="redundancy-test", name="Redundancy Test", nodes=nodes, edges=edges)

    # Fail ONLY replica-1
    scenario = Scenario(
        failures=[FailureInjection(node_id="replica-1", severity=1.0, start_s=0.0)],
        outage_minutes=30.0,
        seed=42,
    )
    result = simulate(graph, scenario)

    assert result.nodes["replica-1"].state == NodeState.FAILED
    assert result.nodes["replica-2"].state == NodeState.HEALTHY
    # Client should stay healthy because replica-2 is still active in the group!
    assert result.nodes["client"].state == NodeState.HEALTHY
    assert result.nodes["client"].damage == 0.0
