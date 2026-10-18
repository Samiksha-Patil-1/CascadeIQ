"""API route for before-vs-after baseline vs mitigated comparison."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.domain.models import MitigationItem, Scenario
from app.engine.metrics import summarize
from app.engine.mitigations import apply
from app.engine.propagation import simulate
from app.store.repo import get_graph

router = APIRouter(tags=["compare"])


class CompareRequest(BaseModel):
    scenario: Scenario
    plan: list[MitigationItem] = Field(default_factory=list)


@router.post("/graphs/{graph_id}/compare")
def compare_runs(graph_id: str, request: CompareRequest) -> dict[str, Any]:
    """Execute baseline and mitigated simulations on identical scenario and seed to compare outcomes."""
    g = get_graph(graph_id)
    if not g:
        raise HTTPException(status_code=404, detail=f"Graph '{graph_id}' not found.")

    # 1. Baseline run
    base_sim = simulate(g, request.scenario)
    base_summary = summarize(base_sim, g, request.scenario)

    # 2. Mitigated run
    mit_graph = apply(g, request.plan)
    mit_sim = simulate(mit_graph, request.scenario)
    mit_summary = summarize(mit_sim, mit_graph, request.scenario)

    # Compute deltas
    plan_cost = sum(item.cost for item in request.plan)
    base_cost = base_summary["outage_cost"]
    mit_cost = mit_summary["outage_cost"]

    pct_loss_reduction = 0.0
    if base_cost > 0.0:
        pct_loss_reduction = max(0.0, ((base_cost - mit_cost) / base_cost) * 100.0)

    delta = {
        "affected": mit_summary["affected"] - base_summary["affected"],
        "failed": mit_summary["failed"] - base_summary["failed"],
        "users_impacted": round(mit_summary["users_impacted"] - base_summary["users_impacted"], 1),
        "money_per_hour": round(mit_summary["money_per_hour"] - base_summary["money_per_hour"], 2),
        "outage_cost": round(mit_cost - base_cost, 2),
        "slo_breaches": mit_summary["slo_breaches"] - base_summary["slo_breaches"],
        "pct_loss_reduction": round(pct_loss_reduction, 1),
        "plan_cost": plan_cost,
    }

    def format_nodes(sim: Any) -> list[dict[str, Any]]:
        return [
            {
                "id": nr.id,
                "damage": round(nr.damage, 4),
                "state": nr.state.value,
                "time_to_impact_s": nr.time_to_impact_s,
                "parent_edge": list(nr.parent_edge) if nr.parent_edge else None,
            }
            for nr in sim.nodes.values()
        ]

    def format_timeline(sim: Any) -> list[dict[str, Any]]:
        return [
            {
                "t_s": ev.t_s,
                "node_id": ev.node_id,
                "from": ev.from_state,
                "to": ev.to_state,
                "damage": round(ev.damage, 4),
            }
            for ev in sim.timeline
        ]

    return {
        "baseline": {
            "run_id": base_sim.run_id,
            "nodes": format_nodes(base_sim),
            "timeline": format_timeline(base_sim),
            "summary": base_summary,
        },
        "mitigated": {
            "run_id": mit_sim.run_id,
            "nodes": format_nodes(mit_sim),
            "timeline": format_timeline(mit_sim),
            "summary": mit_summary,
        },
        "mitigated_graph": mit_graph.model_dump(),
        "delta": delta,
        "plan_cost": plan_cost,
    }
