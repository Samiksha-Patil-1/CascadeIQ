"""Vectorized Monte Carlo failure propagation evaluator with Common Random Numbers.

Implements section 2.9 from ARCHITECTURE.md.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from app.domain.defaults import DEFAULT_MC_TRIALS
from app.domain.models import Graph, Scenario
from app.engine.graph_io import IndexedGraph
from app.engine.propagation import compute_edge_tau
from app.engine.structure import tarjan_scc


def simulate_mc(
    graph: Graph,
    scenario: Scenario,
    trials: int = DEFAULT_MC_TRIALS,
    seed: int = 42,
) -> dict[str, Any]:
    """Execute vectorized Monte Carlo cascade simulation.

    Answers the question: what is the probability of hard failure P(fail) for each node?
    Uses Common Random Numbers (CRN) for low-variance delta evaluation.
    """
    indexed = IndexedGraph(graph)
    rng = np.random.default_rng(seed)

    # Map edges to indices
    edge_list = []
    for u in range(indexed.num_nodes):
        for e in indexed.provider_edges(u):
            edge_list.append(e)

    num_edges = len(edge_list)
    edge_taus = np.array([compute_edge_tau(e) for e in edge_list], dtype=np.float64)

    # Draw random uniform matrix U for edges: trials x num_edges
    U = rng.random((trials, max(num_edges, 1)))
    live_edges = U < edge_taus if num_edges > 0 else np.zeros((trials, 1), dtype=bool)

    # Failure matrix: trials x num_nodes
    failed = np.zeros((trials, indexed.num_nodes), dtype=bool)

    # Injected node failures
    for failure in scenario.failures:
        if failure.node_id in indexed.node_to_idx:
            u_idx = indexed.to_index(failure.node_id)
            node_u = indexed.idx_to_node[u_idx]
            fail_prob = failure.severity * (1.0 - node_u.failover_quality)
            injected_draws = rng.random(trials) < fail_prob
            failed[:, u_idx] = injected_draws

    # Edge map by target and source
    # Providers fail first -> propagate to dependents
    # Use SCC condensation ordering (providers first, then callers)
    sccs = tarjan_scc(indexed)
    # Reverse topological ordering: providers at bottom
    sccs.reverse()

    # Pre-build provider edge mappings
    prov_edges_by_node: list[list[tuple[int, int, str | None]]] = [[] for _ in range(indexed.num_nodes)]
    for e_idx, e in enumerate(edge_list):
        prov_edges_by_node[e.source].append((e_idx, e.target, e.group))

    # Evaluate nodes
    for scc in sccs:
        # For small SCCs (cycles), iterate until convergence
        max_iters = 5 if len(scc) > 1 else 1
        for _ in range(max_iters):
            changed = False
            for v in scc:
                if not prov_edges_by_node[v]:
                    continue

                # Group edges
                groups: dict[str | None, list[tuple[int, int]]] = {}
                for e_idx, tgt, grp in prov_edges_by_node[v]:
                    groups.setdefault(grp, []).append((e_idx, tgt))

                # Node v fails if ANY group fails (OR)
                # A group fails if ALL alternatives in it fail (AND)
                node_fail_from_prov = np.zeros(trials, dtype=bool)

                for grp, edge_pairs in groups.items():
                    if grp is None:
                        for e_idx, tgt in edge_pairs:
                            # singleton: live and provider failed
                            branch_failed = live_edges[:, e_idx] & failed[:, tgt]
                            node_fail_from_prov |= branch_failed
                    else:
                        # alternative group: all alternatives must fail
                        group_all_fail = np.ones(trials, dtype=bool)
                        for e_idx, tgt in edge_pairs:
                            group_all_fail &= (live_edges[:, e_idx] & failed[:, tgt])
                        node_fail_from_prov |= group_all_fail

                new_failed = failed[:, v] | node_fail_from_prov
                if not np.array_equal(new_failed, failed[:, v]):
                    failed[:, v] = new_failed
                    changed = True

            if not changed:
                break

    # Compute failure probabilities and 95% Confidence Intervals
    p_fail_map: dict[str, float] = {}
    ci95_map: dict[str, list[float]] = {}

    for i, node in enumerate(indexed.idx_to_node):
        p = float(np.mean(failed[:, i]))
        # 95% Normal approximation CI: p +- 1.96 * sqrt(p * (1 - p) / trials)
        se = math.sqrt(max(0.0, p * (1.0 - p)) / trials)
        ci_lower = max(0.0, p - 1.96 * se)
        ci_upper = min(1.0, p + 1.96 * se)

        p_fail_map[node.id] = round(p, 4)
        ci95_map[node.id] = [round(ci_lower, 4), round(ci_upper, 4)]

    # Expected affected count per trial
    affected_per_trial = np.sum(failed, axis=1)
    mean_affected = float(np.mean(affected_per_trial))

    return {
        "p_fail": p_fail_map,
        "ci95": ci95_map,
        "mean_affected": round(mean_affected, 1),
        "trials": trials,
        "seed": seed,
    }
