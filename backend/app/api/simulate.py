"""API routes for running failure simulations and explainability."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domain.models import MitigationItem, Scenario
from app.engine.explain import why
from app.engine.metrics import summarize
from app.engine.mitigations import apply
from app.engine.montecarlo import simulate_mc
from app.engine.propagation import simulate
from app.store.repo import get_graph, save_run

router = APIRouter(tags=["simulation"])


class SimulateRequest(BaseModel):
    scenario: Scenario
    mode: str = Field(default="deterministic", description="'deterministic' | 'monte_carlo'")
    trials: int = Field(default=2000, description="Monte Carlo trials count")
    seed: int = Field(default=42, description="Random seed")
    plan: list[MitigationItem] = Field(default_factory=list, description="Mitigations to apply")


@router.post("/graphs/{graph_id}/simulate")
def run_simulation(graph_id: str, request: SimulateRequest) -> dict[str, Any]:
    """Execute failure cascade simulation in deterministic or Monte Carlo mode."""
    g = get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found.")

    # If plan is provided, simulate on mitigated graph
    target_graph = apply(g, request.plan) if request.plan else g

    if request.mode == "monte_carlo":
        mc_res = simulate_mc(target_graph, request.scenario, request.trials, request.seed)
        return {
            "mode": "monte_carlo",
            "graph_id": graph_id,
            "trials": mc_res["trials"],
            "seed": mc_res["seed"],
            "p_fail": mc_res["p_fail"],
            "ci95": mc_res["ci95"],
            "mean_affected": mc_res["mean_affected"],
        }

    # Deterministic simulation
    sim_result = simulate(target_graph, request.scenario)
    summary = summarize(sim_result, target_graph, request.scenario)

    nodes_out = [
        {
            "id": node_res.id,
            "damage": round(node_res.damage, 4),
            "state": node_res.state.value,
            "time_to_impact_s": node_res.time_to_impact_s,
            "parent_edge": list(node_res.parent_edge) if node_res.parent_edge else None,
        }
        for node_res in sim_result.nodes.values()
    ]

    timeline_out = [
        {
            "t_s": ev.t_s,
            "node_id": ev.node_id,
            "from": ev.from_state,
            "to": ev.to_state,
            "damage": round(ev.damage, 4),
        }
        for ev in sim_result.timeline
    ]

    response_data = {
        "run_id": sim_result.run_id,
        "nodes": nodes_out,
        "timeline": timeline_out,
        "summary": summary,
    }

    # Save run for sharing and reproducibility
    save_run(sim_result.run_id, response_data)

    return response_data


@router.post("/graphs/{graph_id}/why/{node_id}")
def explain_node(graph_id: str, node_id: str, request: SimulateRequest) -> dict[str, Any]:
    """Explain root cause path and contributing edges for a node."""
    g = get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found.")

    target_graph = apply(g, request.plan) if request.plan else g
    sim_result = simulate(target_graph, request.scenario)
    return why(sim_result, node_id, target_graph)
