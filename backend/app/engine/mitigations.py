"""Mitigation catalog and graph mutation engine.

Implements section 2.12 from ARCHITECTURE.md.
Domain rule 6: The engine never mutates its input graph. Mitigations return a new graph.
"""

from __future__ import annotations

from typing import Any

from app.domain.defaults import (
    MITIGATION_COSTS,
    MITIGATION_EFFECTS,
    REPLICA_FAILOVER_BOOST,
    REPLICA_FAILOVER_CAP,
)
from app.domain.enums import EdgeKind, MitigationType
from app.domain.models import Edge, Graph, MitigationItem, Node


def get_mitigation_catalog() -> list[dict[str, Any]]:
    """Return the catalog of available mitigation types, default effects, and effort costs."""
    return [
        {
            "type": MitigationType.CIRCUIT_BREAKER.value,
            "name": "Circuit Breaker",
            "applies_to": "edge",
            "effect": MITIGATION_EFFECTS[MitigationType.CIRCUIT_BREAKER],
            "cost": MITIGATION_COSTS[MitigationType.CIRCUIT_BREAKER],
            "description": "Fails fast on downstream timeouts to prevent cascading worker exhaustion.",
        },
        {
            "type": MitigationType.FALLBACK_CACHE.value,
            "name": "Fallback Cache",
            "applies_to": "edge",
            "effect": MITIGATION_EFFECTS[MitigationType.FALLBACK_CACHE],
            "cost": MITIGATION_COSTS[MitigationType.FALLBACK_CACHE],
            "description": "Serves slightly stale data from a local read replica or local cache.",
        },
        {
            "type": MitigationType.FALLBACK_DEGRADED.value,
            "name": "Static Degraded Response",
            "applies_to": "edge",
            "effect": MITIGATION_EFFECTS[MitigationType.FALLBACK_DEGRADED],
            "cost": MITIGATION_COSTS[MitigationType.FALLBACK_DEGRADED],
            "description": "Returns a static default payload, preserving baseline service functionality.",
        },
        {
            "type": MitigationType.BULKHEAD.value,
            "name": "Bulkhead Isolation",
            "applies_to": "edge",
            "effect": MITIGATION_EFFECTS[MitigationType.BULKHEAD],
            "cost": MITIGATION_COSTS[MitigationType.BULKHEAD],
            "description": "Partitions thread/connection pools so failure of one downstream cannot starve others.",
        },
        {
            "type": MitigationType.ASYNC_DECOUPLE.value,
            "name": "Async Message Decouple",
            "applies_to": "edge",
            "effect": 0.65,
            "cost": MITIGATION_COSTS[MitigationType.ASYNC_DECOUPLE],
            "description": "Converts sync dependency into asynchronous buffered message passing.",
        },
        {
            "type": MitigationType.ADD_REPLICA_FAILOVER.value,
            "name": "Add Replica & Automated Failover",
            "applies_to": "node",
            "effect": REPLICA_FAILOVER_BOOST,
            "cost": MITIGATION_COSTS[MitigationType.ADD_REPLICA_FAILOVER],
            "description": "Provisions redundant hot standby instance with automated health checks.",
        },
        {
            "type": MitigationType.ADD_REDUNDANT_PROVIDER.value,
            "name": "Add Redundant Provider",
            "applies_to": "edge",
            "effect": 1.0,
            "cost": MITIGATION_COSTS[MitigationType.ADD_REDUNDANT_PROVIDER],
            "description": "Configures an alternative secondary provider in an active-active group.",
        },
        {
            "type": MitigationType.BREAK_CYCLE.value,
            "name": "Break Circular Dependency",
            "applies_to": "edge",
            "effect": 1.0,
            "cost": MITIGATION_COSTS[MitigationType.BREAK_CYCLE],
            "description": "Architecturally removes cyclic feedback loop edge.",
        },
    ]


def apply(graph: Graph, plan: list[MitigationItem]) -> Graph:
    """Apply a plan of mitigations and return a new derived Graph copy without mutating original."""
    new_nodes: list[Node] = [n.model_copy() for n in graph.nodes]
    new_edges: list[Edge] = [e.model_copy() for e in graph.edges]

    node_dict = {n.id: n for n in new_nodes}

    edges_to_remove: set[tuple[str, str]] = set()

    for item in plan:
        m_type = item.type
        target = item.target

        # Node-level mitigation
        if "node" in target:
            target_node_id = target["node"]
            if target_node_id in node_dict:
                node = node_dict[target_node_id]
                if m_type == MitigationType.ADD_REPLICA_FAILOVER:
                    new_q = min(REPLICA_FAILOVER_CAP, node.failover_quality + REPLICA_FAILOVER_BOOST)
                    node.failover_quality = new_q
                    node.replicas += 1

        # Edge-level mitigation
        elif "edge" in target:
            src, tgt = target["edge"][0], target["edge"][1]

            if m_type == MitigationType.BREAK_CYCLE:
                edges_to_remove.add((src, tgt))
                continue

            for e in new_edges:
                if e.source == src and e.target == tgt:
                    if m_type.value not in e.mitigations:
                        e.mitigations = list(e.mitigations) + [m_type.value]

                    if m_type == MitigationType.ASYNC_DECOUPLE:
                        e.kind = EdgeKind.ASYNC
                        e.delay_s = max(e.delay_s, 30.0)

                    elif m_type == MitigationType.ADD_REDUNDANT_PROVIDER:
                        if e.group is None:
                            e.group = f"alt-group-{src}-{tgt}"

    # Filter out removed edges (e.g. break_cycle)
    final_edges = [
        e for e in new_edges if (e.source, e.target) not in edges_to_remove
    ]

    return Graph(
        id=f"{graph.id}-mitigated",
        name=f"{graph.name} (Mitigated)",
        nodes=new_nodes,
        edges=final_edges,
    )
