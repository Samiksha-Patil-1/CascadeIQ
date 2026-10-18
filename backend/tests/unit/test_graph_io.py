"""Unit tests for graph_io: validation, named errors, and CSV round-trip (T1.2, T1.4)."""

import pytest

from app.domain.enums import EdgeKind, NodeType
from app.domain.errors import (
    DanglingEdgeError,
    DuplicateNodeIdError,
    SelfLoopError,
)
from app.domain.models import Edge, Graph, Node
from app.engine.graph_io import (
    export_graph_to_csv,
    load_graph_from_csv,
    validate_graph,
)


def _make_sample_graph() -> Graph:
    nodes = [
        Node(id="api-gateway", name="API Gateway", type=NodeType.GATEWAY, tier=0),
        Node(id="auth-service", name="Auth Service", type=NodeType.SERVICE, tier=0),
        Node(id="auth-db", name="Auth Database", type=NodeType.DATABASE, tier=0),
    ]
    edges = [
        Edge(
            source="api-gateway",
            target="auth-service",
            kind=EdgeKind.SYNC,
            strength=0.9,
            delay_s=2.0,
        ),
        Edge(
            source="auth-service", target="auth-db", kind=EdgeKind.DATA, strength=1.0, delay_s=1.0
        ),
    ]
    return Graph(id="mini-system", name="Mini System", nodes=nodes, edges=edges)


def test_validate_graph_valid() -> None:
    graph = _make_sample_graph()
    validate_graph(graph)  # does not raise


def test_duplicate_node_id_error() -> None:
    nodes = [
        Node(id="auth-service", name="Auth Service 1", type=NodeType.SERVICE, tier=0),
        Node(id="auth-service", name="Auth Service 2", type=NodeType.SERVICE, tier=0),
    ]
    graph = Graph(id="test-dup", name="Test Dup", nodes=nodes, edges=[])
    with pytest.raises(DuplicateNodeIdError) as exc:
        validate_graph(graph)
    assert exc.value.node_id == "auth-service"
    assert "Duplicate node ID found" in str(exc.value)


def test_dangling_edge_error() -> None:
    nodes = [
        Node(id="api-gateway", name="API Gateway", type=NodeType.GATEWAY, tier=0),
    ]
    edges = [
        Edge(source="api-gateway", target="missing-backend", kind=EdgeKind.SYNC, strength=1.0),
    ]
    graph = Graph(id="test-dangling", name="Test Dangling", nodes=nodes, edges=edges)
    with pytest.raises(DanglingEdgeError) as exc:
        validate_graph(graph)
    assert exc.value.missing_id == "missing-backend"
    assert exc.value.source == "api-gateway"


def test_self_loop_error() -> None:
    nodes = [
        Node(id="recursive-service", name="Self Service", type=NodeType.SERVICE, tier=0),
    ]
    edges = [
        Edge(
            source="recursive-service", target="recursive-service", kind=EdgeKind.SYNC, strength=0.5
        ),
    ]
    graph = Graph(id="test-loop", name="Test Loop", nodes=nodes, edges=edges)
    with pytest.raises(SelfLoopError) as exc:
        validate_graph(graph)
    assert exc.value.node_id == "recursive-service"


def test_csv_round_trip_identical() -> None:
    original_graph = _make_sample_graph()
    nodes_csv, edges_csv = export_graph_to_csv(original_graph)

    # Re-import from CSV
    imported_graph = load_graph_from_csv(
        nodes_csv=nodes_csv,
        edges_csv=edges_csv,
        graph_id=original_graph.id,
        graph_name=original_graph.name,
    )

    assert len(imported_graph.nodes) == len(original_graph.nodes)
    assert len(imported_graph.edges) == len(original_graph.edges)

    for orig_node, imp_node in zip(original_graph.nodes, imported_graph.nodes, strict=True):
        assert orig_node.id == imp_node.id
        assert orig_node.name == imp_node.name
        assert orig_node.type == imp_node.type
        assert orig_node.tier == imp_node.tier
        assert orig_node.owner == imp_node.owner
        assert orig_node.replicas == imp_node.replicas
        assert pytest.approx(orig_node.failover_quality, 1e-3) == imp_node.failover_quality
        assert pytest.approx(orig_node.mtbf_hours, 1e-1) == imp_node.mtbf_hours
        assert pytest.approx(orig_node.mttr_minutes, 1e-1) == imp_node.mttr_minutes
        assert orig_node.user_facing == imp_node.user_facing

    for orig_edge, imp_edge in zip(original_graph.edges, imported_graph.edges, strict=True):
        assert orig_edge.source == imp_edge.source
        assert orig_edge.target == imp_edge.target
        assert orig_edge.kind == imp_edge.kind
        assert pytest.approx(orig_edge.strength, 1e-3) == imp_edge.strength
        assert pytest.approx(orig_edge.delay_s, 1e-1) == imp_edge.delay_s
        assert orig_edge.group == imp_edge.group
        assert orig_edge.mitigations == imp_edge.mitigations
