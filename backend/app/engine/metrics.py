"""Metrics aggregation and KPI computations.

Implements section 2.8 Step 6 and section 2.14 ImpactSummary from ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import Any

from app.domain.models import Graph, Scenario
from app.engine.propagation import SimulationResult


def summarize(result: SimulationResult, graph: Graph, scenario: Scenario) -> dict[str, Any]:
    """Aggregate simulation results into impact KPIs.

    Formulas:
    - affected: count of nodes with d >= degrade_threshold
    - failed: count of nodes with d >= fail_threshold
    - users_impacted: sum over user-facing v of users_per_min(v) * d(v)
    - money_per_hour: 60 * sum over v of revenue_per_min(v) * d(v)
    - outage_cost: sum over v of revenue_per_min(v) * integral of d(v)(t) dt up to outage_minutes
    - slo_breaches: count of nodes with (1 - d) < slo_floor
    - max_time_to_impact_s: max time to reach degraded state
    """
    node_map = {n.id: n for n in graph.nodes}

    affected_count = 0
    failed_count = 0
    users_impacted = 0.0
    money_per_hour = 0.0
    slo_breaches = 0.0
    impact_times: list[float] = []

    for node_id, sim in result.nodes.items():
        node = node_map.get(node_id)
        if not node:
            continue

        d = sim.damage
        if d >= node.degrade_threshold:
            affected_count += 1
            if sim.time_to_impact_s is not None:
                impact_times.append(sim.time_to_impact_s)

        if d >= node.fail_threshold:
            failed_count += 1

        if node.user_facing:
            users_impacted += node.users_per_min * d

        money_per_hour += 60.0 * (node.revenue_per_min * d)

        if (1.0 - d) < node.slo_floor:
            slo_breaches += 1

    # Outage cost integration:
    # outage_minutes total duration in minutes.
    # For each node with revenue_per_min > 0, integrate damage over time.
    total_outage_s = scenario.outage_minutes * 60.0
    outage_cost = 0.0

    # Build per-node damage step functions from timeline
    for node in graph.nodes:
        if node.revenue_per_min <= 0.0:
            continue

        # Extract events for this node
        node_events = [ev for ev in result.timeline if ev.node_id == node.id]
        if not node_events:
            # Steady damage throughout
            final_d = result.nodes[node.id].damage
            outage_cost += node.revenue_per_min * scenario.outage_minutes * final_d
            continue

        # Integrate piecewise constant damage
        integral_d_seconds = 0.0
        prev_t = 0.0
        prev_d = 0.0

        for ev in node_events:
            t = min(ev.t_s, total_outage_s)
            if t > prev_t:
                integral_d_seconds += prev_d * (t - prev_t)
            prev_t = t
            prev_d = ev.damage
            if prev_t >= total_outage_s:
                break

        if prev_t < total_outage_s:
            integral_d_seconds += prev_d * (total_outage_s - prev_t)

        outage_cost += node.revenue_per_min * (integral_d_seconds / 60.0)

    max_tti = max(impact_times) if impact_times else 0.0

    return {
        "affected": affected_count,
        "failed": failed_count,
        "users_impacted": round(users_impacted, 1),
        "money_per_hour": round(money_per_hour, 2),
        "outage_cost": round(outage_cost, 2),
        "slo_breaches": int(slo_breaches),
        "max_time_to_impact_s": round(max_tti, 2),
    }
