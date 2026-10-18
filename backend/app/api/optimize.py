"""API routes for mitigation catalog and automated intervention optimization."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domain.models import Scenario
from app.engine.mitigations import get_mitigation_catalog
from app.engine.optimizer import optimize
from app.store.repo import get_graph

router = APIRouter(tags=["optimize"])


class ScenarioWeight(BaseModel):
    scenario: Scenario
    weight: float = Field(default=1.0, ge=0.0)


class OptimizeRequest(BaseModel):
    scenarios: list[ScenarioWeight]
    budget: float = Field(ge=0.0, description="Effort points budget")
    algorithm: str = Field(default="greedy", description="'greedy' | 'exact' | 'anneal'")
    allowed_types: list[str] | None = None


@router.get("/mitigations/catalog")
def list_catalog() -> list[dict[str, Any]]:
    """Return all available mitigation archetypes, effects, and default costs."""
    return get_mitigation_catalog()


@router.post("/graphs/{graph_id}/optimize")
def run_optimizer(graph_id: str, request: OptimizeRequest) -> dict[str, Any]:
    """Search mitigation combinations and return greedy CELF optimal plan under budget."""
    g = get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found.")

    scenarios_list = [(sw.scenario, sw.weight) for sw in request.scenarios]
    opt_result = optimize(
        graph=g,
        scenarios=scenarios_list,
        budget=request.budget,
        algorithm=request.algorithm,
        allowed_types=request.allowed_types,
    )
    return opt_result
