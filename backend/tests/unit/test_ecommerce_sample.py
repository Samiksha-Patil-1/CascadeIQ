"""Unit test validating the 34-node e-commerce sample dataset (T1.5)."""

import json
from pathlib import Path

from app.engine.graph_io import IndexedGraph, load_graph


def test_ecommerce_sample_loads_and_validates() -> None:
    sample_path = Path(__file__).resolve().parents[2] / "samples" / "ecommerce.json"
    assert sample_path.exists(), f"Sample file not found at {sample_path}"

    with open(sample_path, encoding="utf-8") as f:
        data = json.load(f)

    graph = load_graph(data)

    # Acceptance criteria: exactly 34 nodes, loads and validates
    assert len(graph.nodes) == 34, f"Expected 34 nodes, got {len(graph.nodes)}"
    assert len(graph.edges) == 46, f"Expected 46 edges, got {len(graph.edges)}"

    # Check key topology characteristics from the spec
    node_map = {n.id: n for n in graph.nodes}
    assert "auth-db" in node_map
    auth_db = node_map["auth-db"]
    assert auth_db.tier == 0
    assert auth_db.failover_quality == 0.0

    # Verify cyclic dependency exists between pricing-service and promo-service
    edges_from_to = {(e.source, e.target) for e in graph.edges}
    assert ("pricing-service", "promo-service") in edges_from_to
    assert ("promo-service", "pricing-service") in edges_from_to

    # Verify IndexedGraph works seamlessly on the e-commerce sample
    indexed = IndexedGraph(graph)
    assert indexed.num_nodes == 34

    # auth-db's only dependent is auth-service
    auth_db_dependents = [indexed.to_id(i) for i in indexed.dependents("auth-db")]
    assert "auth-service" in auth_db_dependents

    # Capability nodes carry users / revenue, while infra carry zero (Domain Invariant 8)
    assert node_map["checkout-service"].revenue_per_min == 900.0
    assert node_map["checkout-service"].users_per_min == 1500.0
    assert node_map["auth-db"].revenue_per_min == 0.0
    assert node_map["auth-db"].users_per_min == 0.0
    assert node_map["api-gateway"].revenue_per_min == 0.0
