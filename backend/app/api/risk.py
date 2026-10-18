"""API route for single-failure risk sweep and AEL ranking."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.engine.risk import rank_risk
from app.store.repo import get_graph

router = APIRouter(tags=["risk"])


@router.post("/graphs/{graph_id}/risk")
def get_risk_ranking(graph_id: str) -> dict[str, Any]:
    """Execute single-failure sweep and return ranked AEL table."""
    g = get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found.")

    ranking = rank_risk(g)
    return {
        "graph_id": graph_id,
        "total_nodes": len(g.nodes),
        "rankings": ranking,
    }
