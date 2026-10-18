"""Intervention optimizer: CELF lazy greedy, candidate generation, and knee point.

Implements section 2.12 from ARCHITECTURE.md.
"""

from __future__ import annotations

import heapq
from typing import Any

from app.domain.defaults import MITIGATION_COSTS
from app.domain.enums import MitigationType
from app.domain.models import Graph, MitigationItem, Scenario
from app.engine.metrics import summarize
from app.engine.mitigations import apply
from app.engine.propagation import simulate


def generate_candidate_mitigations(
    graph: Graph,
    scenarios: list[tuple[Scenario, float]],
    allowed_types: list[str] | None = None,
) -> list[MitigationItem]:
    """Generate candidate mitigations touching only the cascade subgraph (relevance filter)."""
    # Find all nodes affected in at least one scenario
    affected_nodes: set[str] = set()
    for sc, _ in scenarios:
        sim = simulate(graph, sc)
        for nid, nres in sim.nodes.items():
            if nres.damage > 0.05:
                affected_nodes.add(nid)

    types_to_consider = [
        MitigationType.CIRCUIT_BREAKER,
        MitigationType.FALLBACK_CACHE,
        MitigationType.FALLBACK_DEGRADED,
        MitigationType.BULKHEAD,
        MitigationType.ASYNC_DECOUPLE,
        MitigationType.ADD_REPLICA_FAILOVER,
    ]
    if allowed_types:
        types_to_consider = [t for t in types_to_consider if t.value in allowed_types]

    candidates: list[MitigationItem] = []
    item_counter = 0

    # Node mitigations (replicas)
    for nid in affected_nodes:
        if MitigationType.ADD_REPLICA_FAILOVER in types_to_consider:
            item_counter += 1
            candidates.append(
                MitigationItem(
                    id=f"mit-node-{item_counter}",
                    type=MitigationType.ADD_REPLICA_FAILOVER,
                    target={"node": nid},
                    cost=MITIGATION_COSTS[MitigationType.ADD_REPLICA_FAILOVER],
                )
            )

    # Edge mitigations
    for e in graph.edges:
        if e.source in affected_nodes or e.target in affected_nodes:
            for mt in types_to_consider:
                if mt == MitigationType.ADD_REPLICA_FAILOVER:
                    continue
                # Do not suggest if already present
                if mt.value in e.mitigations:
                    continue
                item_counter += 1
                candidates.append(
                    MitigationItem(
                        id=f"mit-edge-{item_counter}",
                        type=mt,
                        target={"edge": [e.source, e.target]},
                        cost=MITIGATION_COSTS[mt],
                    )
                )

    return candidates


def evaluate_loss(graph: Graph, scenarios: list[tuple[Scenario, float]]) -> float:
    """Evaluate objective function f(S): expected outage cost across weighted scenarios."""
    total_loss = 0.0
    for sc, weight in scenarios:
        sim = simulate(graph, sc)
        summary = summarize(sim, graph, sc)
        total_loss += weight * summary["outage_cost"]
    return total_loss


def find_knee_point(curve: list[dict[str, float]]) -> int:
    """Find the knee point on the cost-loss curve farthest from the chord."""
    if len(curve) <= 2:
        return 0

    x0 = curve[0]["cost"]
    y0 = curve[0]["expected_loss"]
    x1 = curve[-1]["cost"]
    y1 = curve[-1]["expected_loss"]

    dx = x1 - x0
    dy = y1 - y0
    chord_len = (dx * dx + dy * dy) ** 0.5
    if chord_len == 0.0:
        return 0

    max_dist = -1.0
    knee_idx = 0

    for i, pt in enumerate(curve):
        xi = pt["cost"]
        yi = pt["expected_loss"]
        # Distance from point (xi, yi) to line (x0, y0) -> (x1, y1)
        dist = abs(dy * xi - dx * yi + x1 * y0 - y1 * x0) / chord_len
        if dist > max_dist:
            max_dist = dist
            knee_idx = i

    return knee_idx


def optimize(
    graph: Graph,
    scenarios: list[tuple[Scenario, float]],
    budget: float,
    algorithm: str = "greedy",
    allowed_types: list[str] | None = None,
) -> dict[str, Any]:
    """Optimize mitigation plan subject to budget using CELF lazy greedy and best-single guard."""
    candidates = generate_candidate_mitigations(graph, scenarios, allowed_types)
    baseline_loss = evaluate_loss(graph, scenarios)

    if not candidates or budget <= 0.0:
        return {
            "plan": [],
            "curve": [{"cost": 0.0, "expected_loss": baseline_loss}],
            "knee_index": 0,
            "baseline_loss": round(baseline_loss, 2),
            "final_loss": round(baseline_loss, 2),
        }

    # Best-single-item guard
    best_single_item: MitigationItem | None = None
    best_single_loss = baseline_loss

    for cand in candidates:
        if cand.cost <= budget:
            test_graph = apply(graph, [cand])
            loss = evaluate_loss(test_graph, scenarios)
            if loss < best_single_loss:
                best_single_loss = loss
                best_single_item = cand

    # CELF Lazy Greedy
    # Priority queue stores (-gain_per_cost, cand_id, iteration_when_evaluated, cand)
    heap: list[tuple[float, str, int, MitigationItem]] = []
    for cand in candidates:
        if cand.cost <= budget:
            test_graph = apply(graph, [cand])
            gain = max(0.0, baseline_loss - evaluate_loss(test_graph, scenarios))
            ratio = gain / max(cand.cost, 0.1)
            heapq.heappush(heap, (-ratio, cand.id, 0, cand))

    current_graph = graph
    current_loss = baseline_loss
    current_cost = 0.0
    selected_plan: list[dict[str, Any]] = []
    curve: list[dict[str, float]] = [{"cost": 0.0, "expected_loss": baseline_loss}]

    iteration = 0
    accepted_items: list[MitigationItem] = []

    while heap:
        neg_ratio, cid, last_iter, cand = heapq.heappop(heap)

        if cand.cost + current_cost > budget:
            continue

        if last_iter == iteration:
            # Value is fresh! Accept item
            new_graph = apply(current_graph, [cand])
            new_loss = evaluate_loss(new_graph, scenarios)
            marginal_gain = current_loss - new_loss

            if marginal_gain > 0.01:
                current_graph = new_graph
                current_loss = new_loss
                current_cost += cand.cost
                accepted_items.append(cand)
                selected_plan.append({
                    "item": cand.model_dump(),
                    "marginal_gain": round(marginal_gain, 2),
                    "cumulative_cost": round(current_cost, 2),
                })
                curve.append({"cost": round(current_cost, 2), "expected_loss": round(current_loss, 2)})
                iteration += 1
        else:
            # Value is stale: recompute marginal gain
            test_graph = apply(current_graph, [cand])
            gain = max(0.0, current_loss - evaluate_loss(test_graph, scenarios))
            new_ratio = gain / max(cand.cost, 0.1)
            heapq.heappush(heap, (-new_ratio, cand.id, iteration, cand))

    # Compare with best-single guard
    if best_single_item and best_single_loss < current_loss:
        selected_plan = [{
            "item": best_single_item.model_dump(),
            "marginal_gain": round(baseline_loss - best_single_loss, 2),
            "cumulative_cost": round(best_single_item.cost, 2),
        }]
        current_loss = best_single_loss
        curve = [
            {"cost": 0.0, "expected_loss": baseline_loss},
            {"cost": best_single_item.cost, "expected_loss": best_single_loss},
        ]

    knee_idx = find_knee_point(curve)

    return {
        "plan": selected_plan,
        "curve": curve,
        "knee_index": knee_idx,
        "baseline_loss": round(baseline_loss, 2),
        "final_loss": round(current_loss, 2),
    }
