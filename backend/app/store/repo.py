"""In-memory and persistent graph repository for CascadeIQ."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.models import Graph
from app.engine.graph_io import load_graph

# In-memory storage of graphs keyed by graph ID
_GRAPHS: dict[str, Graph] = {}
_RUNS: dict[str, dict[str, Any]] = {}


def get_default_sample_graph() -> Graph:
    """Load the default 34-node e-commerce sample graph from disk."""
    sample_file = Path(__file__).resolve().parents[2] / "samples" / "ecommerce.json"
    with open(sample_file, encoding="utf-8") as f:
        data = json.load(f)
    return load_graph(data)


def init_repo() -> None:
    """Initialize repository with bundled sample graphs."""
    sample = get_default_sample_graph()
    _GRAPHS[sample.id] = sample


def get_graph(graph_id: str) -> Graph | None:
    """Retrieve graph by ID."""
    if not _GRAPHS:
        init_repo()
    return _GRAPHS.get(graph_id)


def save_graph(graph: Graph) -> None:
    """Save or update graph."""
    _GRAPHS[graph.id] = graph


def list_graphs() -> list[dict[str, Any]]:
    """List all available graph summaries."""
    if not _GRAPHS:
        init_repo()
    return [
        {
            "id": g.id,
            "name": g.name,
            "node_count": len(g.nodes),
            "edge_count": len(g.edges),
        }
        for g in _GRAPHS.values()
    ]


def save_run(run_id: str, data: dict[str, Any]) -> None:
    """Save an immutable simulation run for sharing and reproducibility."""
    _RUNS[run_id] = data


def get_run(run_id: str) -> dict[str, Any] | None:
    """Retrieve saved simulation run."""
    return _RUNS.get(run_id)
