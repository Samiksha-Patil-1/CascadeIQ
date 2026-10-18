"""Unit tests for Phase 2: Structural analysis (T2.1 - T2.5)."""

from app.domain.enums import EdgeKind, NodeType
from app.domain.models import Edge, Graph, Node
from app.engine.graph_io import IndexedGraph
from app.engine.structure import (
    compute_networkx_metrics,
    dijkstra_earliest_arrival,
    find_spof,
    tarjan_scc,
    topological_layers,
    transitive_dependents,
)


def _build_test_graph() -> Graph:
    # A -> B -> C (A depends on B, B depends on C)
    # D -> B (D depends on B)
    nodes = [
        Node(id="service-a", name="Service A", type=NodeType.SERVICE, tier=0, user_facing=True, revenue_per_min=100.0),
        Node(id="service-b", name="Service B", type=NodeType.SERVICE, tier=1, user_facing=False),
        Node(id="db-c", name="Database C", type=NodeType.DATABASE, tier=2, user_facing=False),
        Node(id="service-d", name="Service D", type=NodeType.SERVICE, tier=0, user_facing=True, users_per_min=500.0),
    ]
    edges = [
        Edge(source="service-a", target="service-b", kind=EdgeKind.SYNC, strength=0.9, delay_s=2.0),
        Edge(source="service-b", target="db-c", kind=EdgeKind.DATA, strength=1.0, delay_s=1.0),
        Edge(source="service-d", target="service-b", kind=EdgeKind.SYNC, strength=0.8, delay_s=3.0),
    ]
    return Graph(id="struct-test", name="Structure Test Graph", nodes=nodes, edges=edges)


def test_transitive_dependents_reverse_bfs() -> None:
    graph = _build_test_graph()
    indexed = IndexedGraph(graph)

    # db-c failure should transitively reach db-c, service-b, service-a, service-d
    c_idx = indexed.to_index("db-c")
    deps_c = transitive_dependents(indexed, c_idx)
    dep_ids_c = {indexed.to_id(i) for i in deps_c}
    assert dep_ids_c == {"db-c", "service-b", "service-a", "service-d"}

    # service-b failure should reach service-b, service-a, service-d (not db-c)
    b_idx = indexed.to_index("service-b")
    deps_b = transitive_dependents(indexed, b_idx)
    dep_ids_b = {indexed.to_id(i) for i in deps_b}
    assert dep_ids_b == {"service-b", "service-a", "service-d"}


def test_tarjan_scc_and_cycle_detection() -> None:
    # Build graph with a 2-node cycle: X -> Y and Y -> X
    nodes = [
        Node(id="node-x", name="Service X", type=NodeType.SERVICE, tier=1),
        Node(id="node-y", name="Service Y", type=NodeType.SERVICE, tier=1),
        Node(id="node-z", name="Service Z", type=NodeType.SERVICE, tier=2),
    ]
    edges = [
        Edge(source="node-x", target="node-y", kind=EdgeKind.SYNC),
        Edge(source="node-y", target="node-x", kind=EdgeKind.SYNC),
        Edge(source="node-y", target="node-z", kind=EdgeKind.SYNC),
    ]
    graph = Graph(id="cycle-test", name="Cycle Test", nodes=nodes, edges=edges)
    indexed = IndexedGraph(graph)

    sccs = tarjan_scc(indexed)
    cycle_sccs = [scc for scc in sccs if len(scc) > 1]
    assert len(cycle_sccs) == 1
    cycle_nodes = {indexed.to_id(idx) for idx in cycle_sccs[0]}
    assert cycle_nodes == {"node-x", "node-y"}


def test_topological_layers() -> None:
    graph = _build_test_graph()
    indexed = IndexedGraph(graph)

    layers = topological_layers(indexed)
    # db-c has no providers, so level 0
    layer_0_ids = {indexed.to_id(i) for i in layers[0]}
    assert "db-c" in layer_0_ids

    # service-b relies on db-c, so level 1
    layer_1_ids = {indexed.to_id(i) for i in layers[1]}
    assert "service-b" in layer_1_ids

    # service-a and service-d rely on service-b, so level 2
    layer_2_ids = {indexed.to_id(i) for i in layers[2]}
    assert "service-a" in layer_2_ids
    assert "service-d" in layer_2_ids


def test_find_spof() -> None:
    graph = _build_test_graph()
    indexed = IndexedGraph(graph)

    spofs = find_spof(indexed)
    # db-c and service-b have no alternatives and are depended on by tier 0 capabilities
    assert "db-c" in spofs
    assert "service-b" in spofs


def test_networkx_centrality_and_articulation_points() -> None:
    graph = _build_test_graph()
    indexed = IndexedGraph(graph)

    metrics = compute_networkx_metrics(indexed)
    assert "articulation_points" in metrics
    assert "pagerank_reversed" in metrics
    assert "betweenness" in metrics

    # service-b sits between db-c and services a & d, so it is an articulation point
    assert "service-b" in metrics["articulation_points"]
    # db-c has deep reverse pagerank because all services depend on it
    pr = metrics["pagerank_reversed"]
    assert pr["db-c"] > 0.0


def test_dijkstra_delay() -> None:
    graph = _build_test_graph()
    indexed = IndexedGraph(graph)

    delays = dijkstra_earliest_arrival(indexed, "db-c")
    # db-c start delay: 0.0
    assert delays["db-c"] == 0.0
    # service-b delay = 0 + 1.0 = 1.0
    assert delays["service-b"] == 1.0
    # service-a delay = 1.0 + 2.0 = 3.0
    assert delays["service-a"] == 3.0
    # service-d delay = 1.0 + 3.0 = 4.0
    assert delays["service-d"] == 4.0
