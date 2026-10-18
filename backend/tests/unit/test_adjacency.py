"""Unit tests for index-based adjacency and failure direction convention (T1.3)."""

from app.domain.enums import EdgeKind, NodeType
from app.domain.models import Edge, Graph, Node
from app.engine.graph_io import IndexedGraph


def test_indexed_graph_adjacency_and_direction_convention() -> None:
    """Validate 3-node chain: A depends on B, B depends on C.

    Domain rule 1 & invariant 1:
    - An edge points from dependent to provider: A -> B, B -> C.
    - Failure flows from provider to dependent: C -> B -> A.
    - providers(u) returns nodes u depends on.
    - dependents(u) returns nodes that depend on u (where failure propagates).
    """
    nodes = [
        Node(id="node-a", name="Service A", type=NodeType.SERVICE, tier=0),
        Node(id="node-b", name="Service B", type=NodeType.SERVICE, tier=0),
        Node(id="node-c", name="Service C", type=NodeType.SERVICE, tier=0),
    ]
    edges = [
        Edge(source="node-a", target="node-b", kind=EdgeKind.SYNC, strength=0.8, delay_s=2.0),
        Edge(source="node-b", target="node-c", kind=EdgeKind.SYNC, strength=1.0, delay_s=2.0),
    ]
    graph = Graph(id="chain-graph", name="3-Node Chain", nodes=nodes, edges=edges)
    indexed = IndexedGraph(graph)

    idx_a = indexed.to_index("node-a")
    idx_b = indexed.to_index("node-b")
    idx_c = indexed.to_index("node-c")

    # Check providers (who does u depend on?)
    assert indexed.providers("node-a") == [idx_b]
    assert indexed.providers("node-b") == [idx_c]
    assert indexed.providers("node-c") == []

    # Check dependents (who depends on u? where does failure spread from u?)
    assert indexed.dependents("node-c") == [idx_b]
    assert indexed.dependents("node-b") == [idx_a]
    assert indexed.dependents("node-a") == []

    # Confirm failure flow sequence: C -> B -> A
    # If C fails, its immediate downstream blast targets are its dependents:
    downstream_from_c = [indexed.to_id(i) for i in indexed.dependents("node-c")]
    assert downstream_from_c == ["node-b"]

    downstream_from_b = [indexed.to_id(i) for i in indexed.dependents("node-b")]
    assert downstream_from_b == ["node-a"]

    # Edges leading into dependents:
    c_dep_edges = indexed.dependents_edges("node-c")
    assert len(c_dep_edges) == 1
    assert c_dep_edges[0].source == idx_b
    assert c_dep_edges[0].target == idx_c
