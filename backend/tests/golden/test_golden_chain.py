"""The Golden Chain Test (Section 2.8, page 14 of Build Pack).

Chain: A depends on B (0.8, sync), B depends on C (1.0, sync). Inject C at severity 1.0.
- Baseline: d_C = 1.0, d_B = 1.0, d_A = 0.8 -> A is FAILED.
- circuit_breaker (0.35) + fallback_cache (0.6) on A to B:
  m = 1 - 0.65 * 0.40 = 0.74, tau = 0.8 * 0.26 = 0.208 -> d_A = 0.208 (DEGRADED).
- Add bulkhead (0.25):
  m = 1 - 0.65 * 0.40 * 0.75 = 0.805, tau = 0.156 -> d_A = 0.156 (HEALTHY).
"""

import pytest

from app.domain.enums import EdgeKind, MitigationType, NodeState, NodeType
from app.domain.models import Edge, FailureInjection, Graph, Node, Scenario
from app.engine.propagation import simulate


def _build_golden_graph(mitigations_ab: list[str]) -> Graph:
    nodes = [
        Node(id="node-a", name="Service A", type=NodeType.SERVICE, tier=0),
        Node(id="node-b", name="Service B", type=NodeType.SERVICE, tier=0),
        Node(id="node-c", name="Service C", type=NodeType.SERVICE, tier=0),
    ]
    edges = [
        Edge(
            source="node-a",
            target="node-b",
            kind=EdgeKind.SYNC,
            strength=0.8,
            delay_s=2.0,
            mitigations=mitigations_ab,
        ),
        Edge(
            source="node-b",
            target="node-c",
            kind=EdgeKind.SYNC,
            strength=1.0,
            delay_s=2.0,
            mitigations=[],
        ),
    ]
    return Graph(id="golden-chain", name="Golden Chain", nodes=nodes, edges=edges)


def test_golden_chain_baseline() -> None:
    graph = _build_golden_graph([])
    scenario = Scenario(
        failures=[FailureInjection(node_id="node-c", severity=1.0, start_s=0.0)],
        outage_minutes=30.0,
        seed=42,
    )
    result = simulate(graph, scenario)

    assert pytest.approx(result.nodes["node-c"].damage, 1e-4) == 1.0
    assert result.nodes["node-c"].state == NodeState.FAILED

    assert pytest.approx(result.nodes["node-b"].damage, 1e-4) == 1.0
    assert result.nodes["node-b"].state == NodeState.FAILED

    assert pytest.approx(result.nodes["node-a"].damage, 1e-4) == 0.8
    assert result.nodes["node-a"].state == NodeState.FAILED


def test_golden_chain_two_mitigations() -> None:
    # circuit_breaker (0.35) + fallback_cache (0.6) on A to B
    # Arithmetic:
    # m_e = 1 - (1 - 0.35) * (1 - 0.60) = 1 - 0.65 * 0.40 = 0.74
    # tau = 0.8 * 1.0 * (1 - 0.74) = 0.8 * 0.26 = 0.208
    graph = _build_golden_graph([
        MitigationType.CIRCUIT_BREAKER.value,
        MitigationType.FALLBACK_CACHE.value,
    ])
    scenario = Scenario(
        failures=[FailureInjection(node_id="node-c", severity=1.0, start_s=0.0)],
        outage_minutes=30.0,
        seed=42,
    )
    result = simulate(graph, scenario)

    assert pytest.approx(result.nodes["node-a"].damage, 1e-4) == 0.208
    assert result.nodes["node-a"].state == NodeState.DEGRADED


def test_golden_chain_three_mitigations() -> None:
    # Add bulkhead (0.25)
    # Arithmetic:
    # m_e = 1 - 0.65 * 0.40 * 0.75 = 1 - 0.195 = 0.805
    # tau = 0.8 * 1.0 * (1 - 0.805) = 0.8 * 0.195 = 0.156
    graph = _build_golden_graph([
        MitigationType.CIRCUIT_BREAKER.value,
        MitigationType.FALLBACK_CACHE.value,
        MitigationType.BULKHEAD.value,
    ])
    scenario = Scenario(
        failures=[FailureInjection(node_id="node-c", severity=1.0, start_s=0.0)],
        outage_minutes=30.0,
        seed=42,
    )
    result = simulate(graph, scenario)

    assert pytest.approx(result.nodes["node-a"].damage, 1e-4) == 0.156
    assert result.nodes["node-a"].state == NodeState.HEALTHY
