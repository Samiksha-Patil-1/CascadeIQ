"""API routes for graph management, structural analysis, and sample loading."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.engine.graph_io import IndexedGraph, load_graph
from app.engine.structure import (
    compute_networkx_metrics,
    find_spof,
    tarjan_scc,
    topological_layers,
)
from app.store.repo import get_graph, list_graphs, save_graph

router = APIRouter(prefix="/graphs", tags=["graphs"])


@router.get("/samples")
def get_sample_graphs() -> list[dict[str, Any]]:
    """List bundled sample systems."""
    return list_graphs()


@router.get("/{graph_id}")
def fetch_graph(graph_id: str) -> dict[str, Any]:
    """Retrieve full dependency graph by ID."""
    g = get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found.")
    return g.model_dump()


@router.post("")
def create_graph(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and store a new graph."""
    try:
        g = load_graph(payload)
        save_graph(g)
        return {"status": "created", "id": g.id, "node_count": len(g.nodes)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{graph_id}/structure")
def analyze_structure(graph_id: str) -> dict[str, Any]:
    """Perform static structural analysis: SCC cycles, layers, SPOFs, centrality."""
    g = get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found.")

    indexed = IndexedGraph(g)
    sccs = tarjan_scc(indexed)
    # Filter cycles (SCCs with size > 1)
    cycles = [
        [indexed.to_id(idx) for idx in scc]
        for scc in sccs if len(scc) > 1
    ]

    layers_idx = topological_layers(indexed)
    layers = [
        [indexed.to_id(idx) for idx in layer]
        for layer in layers_idx
    ]

    spofs = find_spof(indexed)
    nx_metrics = compute_networkx_metrics(indexed)

    return {
        "graph_id": graph_id,
        "cycles": cycles,
        "layers": layers,
        "single_points_of_failure": spofs,
        "articulation_points": nx_metrics["articulation_points"],
        "pagerank_reversed": nx_metrics["pagerank_reversed"],
        "betweenness": nx_metrics["betweenness"],
    }
