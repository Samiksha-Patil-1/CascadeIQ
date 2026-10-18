"""Risk prioritization and Annualized Expected Loss (AEL) ranking.

Implements section 2.11 from ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import Any

from app.domain.defaults import HOURS_PER_YEAR
from app.domain.models import FailureInjection, Graph, Scenario
from app.engine.graph_io import IndexedGraph
from app.engine.propagation import simulate
from app.engine.structure import compute_networkx_metrics, transitive_dependents


def rank_percentile(values: list[float]) -> list[float]:
    """Compute normalized rank-percentile [0.0, 1.0] to prevent outlier distortion."""
    n = len(values)
    if n <= 1:
        return [1.0] * n

    # Sort indices by value
    indexed_vals = sorted(enumerate(values), key=lambda x: x[1])
    scores = [0.0] * n
    for rank, (original_idx, _) in enumerate(indexed_vals):
        scores[original_idx] = rank / (n - 1)
    return scores


def rank_risk(graph: Graph) -> list[dict[str, Any]]:
    """Execute single-failure sweep across all nodes with severity 1.0 and calculate AEL."""
    indexed = IndexedGraph(graph)
    nx_metrics = compute_networkx_metrics(indexed)
    pagerank_rev = nx_metrics["pagerank_reversed"]
    betweenness = nx_metrics["betweenness"]

    results: list[dict[str, Any]] = []

    ael_list: list[float] = []
    chokepoint_list: list[float] = []
    pr_list: list[float] = []
    bet_list: list[float] = []

    for node in graph.nodes:
        # Run single-failure scenario
        scenario = Scenario(
            failures=[FailureInjection(node_id=node.id, severity=1.0, start_s=0.0)],
            outage_minutes=node.mttr_minutes,
            seed=42,
        )
        sim_res = simulate(graph, scenario)

        # impact_per_hour = 60 * sum over x of revenue_per_min(x) * d_x
        impact_per_hour = sum(
            60.0 * (target_node.revenue_per_min * sim_res.nodes[target_node.id].damage)
            for target_node in graph.nodes
        )

        incidents_per_year = HOURS_PER_YEAR / max(node.mtbf_hours, 1.0)
        hours_per_incident = node.mttr_minutes / 60.0
        impact_per_incident = (impact_per_hour / 60.0) * node.mttr_minutes
        ael = incidents_per_year * hours_per_incident * impact_per_hour

        affected_count = sum(
            1 for sim in sim_res.nodes.values()
            if sim.damage >= graph.nodes[indexed.to_index(sim.id)].degrade_threshold
        )

        # Chokepoint subtree impact (transitive dependents count)
        trans_deps = transitive_dependents(indexed, node.id)
        chokepoint_score = float(len(trans_deps))

        pr_val = float(pagerank_rev.get(node.id, 0.0))
        bet_val = float(betweenness.get(node.id, 0.0))

        ael_list.append(ael)
        chokepoint_list.append(chokepoint_score)
        pr_list.append(pr_val)
        bet_list.append(bet_val)

        results.append({
            "node_id": node.id,
            "name": node.name,
            "tier": node.tier,
            "ael": round(ael, 2),
            "impact_per_hour": round(impact_per_hour, 2),
            "impact_per_incident": round(impact_per_incident, 2),
            "incidents_per_year": round(incidents_per_year, 2),
            "mtbf_hours": node.mtbf_hours,
            "mttr_minutes": node.mttr_minutes,
            "affected_count": affected_count,
        })

    # Normalize into rank percentiles
    norm_ael = rank_percentile(ael_list)
    norm_choke = rank_percentile(chokepoint_list)
    norm_pr = rank_percentile(pr_list)
    norm_bet = rank_percentile(bet_list)

    for i, item in enumerate(results):
        crit = (
            0.50 * norm_ael[i]
            + 0.20 * norm_choke[i]
            + 0.15 * norm_pr[i]
            + 0.15 * norm_bet[i]
        )
        item["criticality"] = round(crit, 3)

    # Sort descending by AEL (primary monetary ranking)
    results.sort(key=lambda r: (r["ael"], r["criticality"]), reverse=True)

    # Assign 1-indexed ranks
    for rank, item in enumerate(results, start=1):
        item["rank"] = rank

    return results
