"""Explainability engine: Why-chains and root cause contribution shares.

Implements section 2.13 from ARCHITECTURE.md.
"""

from __future__ import annotations

from typing import Any

from app.domain.models import Graph
from app.engine.graph_io import IndexedGraph
from app.engine.propagation import SimulationResult, compute_edge_tau


def why(result: SimulationResult, target_node_id: str, graph: Graph) -> dict[str, Any]:
    """Trace why a given node degraded or failed back to root cause failures.

    Returns the failure transmission chain and top contributing edges with narrative explanation.
    """
    indexed = IndexedGraph(graph)
    if target_node_id not in result.nodes:
        return {
            "node_id": target_node_id,
            "damage": 0.0,
            "state": "healthy",
            "chain": [],
            "top_contributors": [],
            "narrative": "Node not found in simulation result.",
        }

    target_sim = result.nodes[target_node_id]
    if target_sim.damage <= 0.0:
        return {
            "node_id": target_node_id,
            "damage": 0.0,
            "state": target_sim.state.value,
            "chain": [],
            "top_contributors": [],
            "narrative": f"Node '{target_node_id}' remained healthy with 0.0 damage.",
        }

    # Trace parent edge backwards
    chain: list[dict[str, Any]] = []
    curr_id = target_node_id
    visited: set[str] = set()

    while curr_id and curr_id not in visited:
        visited.add(curr_id)
        node_res = result.nodes.get(curr_id)
        if not node_res or not node_res.parent_edge:
            break

        src, tgt = node_res.parent_edge
        # Find edge
        edge_matches = [e for e in graph.edges if e.source == src and e.target == tgt]
        if edge_matches:
            e = edge_matches[0]
            indexed_e = [ie for ie in indexed.provider_edges(indexed.to_index(src)) if ie.target == indexed.to_index(tgt)]
            tau = compute_edge_tau(indexed_e[0]) if indexed_e else e.strength
            chain.append({
                "source": src,
                "target": tgt,
                "kind": e.kind.value,
                "strength": e.strength,
                "tau": round(tau, 3),
                "delay_s": e.delay_s,
            })
        curr_id = tgt

    # Top contributing incoming edges for target node
    top_contributors: list[dict[str, Any]] = []
    if target_node_id in indexed.node_to_idx:
        t_idx = indexed.to_index(target_node_id)
        for pe in indexed.provider_edges(t_idx):
            tgt_id = indexed.to_id(pe.target)
            tgt_damage = result.nodes[tgt_id].damage if tgt_id in result.nodes else 0.0
            tau = compute_edge_tau(pe)
            contrib = tau * tgt_damage
            if contrib > 0.0:
                top_contributors.append({
                    "provider": tgt_id,
                    "contribution": round(contrib, 3),
                    "tau": round(tau, 3),
                    "provider_damage": round(tgt_damage, 3),
                })
        top_contributors.sort(key=lambda x: x["contribution"], reverse=True)
        top_contributors = top_contributors[:3]

    # Generate human narrative sentence
    if chain:
        hops_desc = []
        for hop in chain:
            hops_desc.append(
                f"{hop['source']} needs {hop['target']} ({hop['kind']}, strength {hop['strength']})"
            )
        root_cause = chain[-1]["target"]
        narrative = f"{target_node_id} was affected along path: " + " -> ".join(hops_desc) + f", originating from root cause outage at {root_cause}."
    else:
        narrative = f"{target_node_id} was directly affected as an injected root failure."

    return {
        "node_id": target_node_id,
        "damage": target_sim.damage,
        "state": target_sim.state.value,
        "chain": chain,
        "top_contributors": top_contributors,
        "narrative": narrative,
    }
