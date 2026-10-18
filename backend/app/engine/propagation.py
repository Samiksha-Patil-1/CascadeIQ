"""Deterministic event-driven fault propagation simulator.

Implements section 2.8 from ARCHITECTURE.md.
"""

from __future__ import annotations

import heapq
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.domain.defaults import (
    KAPPA_FACTORS,
    MAX_SIMULATION_EVENTS,
    MITIGATION_EFFECTS,
    SIMULATION_EPS,
)
from app.domain.enums import EdgeKind, MitigationType, NodeState
from app.domain.models import Graph, Scenario
from app.engine.graph_io import IndexedEdge, IndexedGraph


def compute_edge_tau(edge: IndexedEdge) -> float:
    """Compute transmission factor tau_e for an edge.

    tau_e = w_e * kappa(kind_e) * (1 - m_e)
    m_e = 1 - product over mitigations j of (1 - eff_j)
    """
    kind = edge.kind
    # Check if async_decouple is present on edge
    if MitigationType.ASYNC_DECOUPLE.value in edge.mitigations:
        kind = EdgeKind.ASYNC

    kappa = KAPPA_FACTORS.get(kind, 1.0)

    # Multiplicative combination of mitigation effects
    prod = 1.0
    for m in edge.mitigations:
        try:
            m_type = MitigationType(m)
            eff = MITIGATION_EFFECTS.get(m_type, 0.0)
            if m_type != MitigationType.ASYNC_DECOUPLE:
                prod *= (1.0 - eff)
        except ValueError:
            pass

    m_e = 1.0 - prod
    tau = edge.strength * kappa * (1.0 - m_e)
    return max(0.0, min(1.0, tau))


def get_node_state(damage: float, degrade_threshold: float, fail_threshold: float) -> NodeState:
    """Map scalar damage to discrete node health state."""
    if damage >= fail_threshold - SIMULATION_EPS:
        return NodeState.FAILED
    if damage >= degrade_threshold - SIMULATION_EPS:
        return NodeState.DEGRADED
    return NodeState.HEALTHY


@dataclass
class TimelineEvent:
    t_s: float
    node_id: str
    from_state: str
    to_state: str
    damage: float


@dataclass
class NodeSimResult:
    id: str
    damage: float
    state: NodeState
    time_to_impact_s: float | None = None
    p_fail: float | None = None
    ci95: tuple[float, float] | None = None
    parent_edge: tuple[str, str] | None = None


@dataclass
class SimulationResult:
    run_id: str
    nodes: dict[str, NodeSimResult]
    timeline: list[TimelineEvent]
    summary: dict[str, Any] = field(default_factory=dict)


def simulate(graph: Graph, scenario: Scenario) -> SimulationResult:
    """Execute deterministic event-driven cascade simulation with min-heap and delays."""
    indexed = IndexedGraph(graph)
    run_id = f"run-{uuid.uuid4().hex[:8]}"

    # Precompute edge taus
    taus: dict[tuple[int, int], float] = {}
    for src in range(indexed.num_nodes):
        for e in indexed.provider_edges(src):
            taus[(e.source, e.target)] = compute_edge_tau(e)

    # Node states
    damage: list[float] = [0.0] * indexed.num_nodes
    injected_damage: list[float] = [0.0] * indexed.num_nodes
    current_state: list[NodeState] = [NodeState.HEALTHY] * indexed.num_nodes
    time_to_impact: list[float | None] = [None] * indexed.num_nodes
    parent_edges: list[tuple[str, str] | None] = [None] * indexed.num_nodes

    # Edge damages: (source_idx, target_idx) -> damage received from provider target
    edge_damage: dict[tuple[int, int], float] = {k: 0.0 for k in taus}

    timeline: list[TimelineEvent] = []

    # Priority queue: min-heap of (t, event_id, event_type, payload)
    # event_types: 'inject', 'edge_update'
    event_counter = 0
    heap: list[tuple[float, int, str, Any]] = []

    def push_event(t: float, event_type: str, payload: Any) -> None:
        nonlocal event_counter
        event_counter += 1
        heapq.heappush(heap, (t, event_counter, event_type, payload))

    # Seed injected failures
    for failure in scenario.failures:
        if failure.node_id in indexed.node_to_idx:
            u_idx = indexed.to_index(failure.node_id)
            node_u = indexed.idx_to_node[u_idx]
            inj_val = failure.severity * (1.0 - node_u.failover_quality)
            injected_damage[u_idx] = max(injected_damage[u_idx], inj_val)
            push_event(failure.start_s, "inject", (u_idx, inj_val))

    def compute_loss(u: int) -> tuple[float, IndexedEdge | None]:
        """Compute node loss via noisy-OR across provider groups (steps 2 & 3)."""
        prov_edges = indexed.provider_edges(u)
        if not prov_edges:
            return 0.0, None

        # Group edges by edge.group
        grouped_edges: dict[str | None, list[IndexedEdge]] = {}
        for e in prov_edges:
            grouped_edges.setdefault(e.group, []).append(e)

        max_contrib = -1.0
        argmax_edge: IndexedEdge | None = None
        prob_not_lost = 1.0

        for grp, edges in grouped_edges.items():
            if grp is None:
                # Singleton edges: each edge is its own provider group
                for e in edges:
                    t_val = taus[(e.source, e.target)]
                    e_dam = edge_damage[(e.source, e.target)]
                    contrib = t_val * e_dam
                    if contrib > max_contrib:
                        max_contrib = contrib
                        argmax_edge = e
                    prob_not_lost *= (1.0 - contrib)
            else:
                # Alternative providers in a group: group is hurt only if ALL alternatives fail
                g_group = 1.0
                for e in edges:
                    t_val = taus[(e.source, e.target)]
                    e_dam = edge_damage[(e.source, e.target)]
                    g_group *= (t_val * e_dam)
                if g_group > max_contrib:
                    max_contrib = g_group
                    argmax_edge = edges[0]
                prob_not_lost *= (1.0 - g_group)

        loss_u = 1.0 - prob_not_lost
        return max(0.0, min(1.0, loss_u)), argmax_edge

    events_processed = 0

    while heap and events_processed < MAX_SIMULATION_EVENTS:
        t, _, etype, payload = heapq.heappop(heap)
        events_processed += 1

        if etype == "inject":
            u_idx, inj_val = payload
            if inj_val > damage[u_idx] + SIMULATION_EPS:
                damage[u_idx] = inj_val
                u_node = indexed.idx_to_node[u_idx]
                new_state = get_node_state(inj_val, u_node.degrade_threshold, u_node.fail_threshold)
                if new_state != current_state[u_idx]:
                    timeline.append(TimelineEvent(
                        t_s=t,
                        node_id=u_node.id,
                        from_state=current_state[u_idx].value,
                        to_state=new_state.value,
                        damage=inj_val,
                    ))
                    if current_state[u_idx] == NodeState.HEALTHY and new_state != NodeState.HEALTHY:
                        if time_to_impact[u_idx] is None:
                            time_to_impact[u_idx] = t
                    current_state[u_idx] = new_state

                # Push to all dependent edges (edges whose target is u_idx)
                for dep_e in indexed.dependents_edges(u_idx):
                    push_event(t + dep_e.delay_s, "edge_update", (dep_e, damage[u_idx]))

        elif etype == "edge_update":
            dep_e, val = payload
            edge_key = (dep_e.source, dep_e.target)
            if val > edge_damage[edge_key]:
                edge_damage[edge_key] = val
                src_idx = dep_e.source
                l_new, best_edge = compute_loss(src_idx)
                new_d = max(injected_damage[src_idx], l_new)

                if new_d > damage[src_idx] + SIMULATION_EPS:
                    damage[src_idx] = new_d
                    if best_edge is not None:
                        parent_edges[src_idx] = (indexed.to_id(best_edge.source), indexed.to_id(best_edge.target))

                    src_node = indexed.idx_to_node[src_idx]
                    new_state = get_node_state(new_d, src_node.degrade_threshold, src_node.fail_threshold)
                    if new_state != current_state[src_idx]:
                        timeline.append(TimelineEvent(
                            t_s=t,
                            node_id=src_node.id,
                            from_state=current_state[src_idx].value,
                            to_state=new_state.value,
                            damage=new_d,
                        ))
                        if current_state[src_idx] == NodeState.HEALTHY and new_state != NodeState.HEALTHY:
                            if time_to_impact[src_idx] is None:
                                time_to_impact[src_idx] = t
                        current_state[src_idx] = new_state

                    # Propagate further to dependents of src_idx
                    for next_dep in indexed.dependents_edges(src_idx):
                        push_event(t + next_dep.delay_s, "edge_update", (next_dep, new_d))

    # Build final node results map
    nodes_result: dict[str, NodeSimResult] = {}
    for i, node in enumerate(indexed.idx_to_node):
        nodes_result[node.id] = NodeSimResult(
            id=node.id,
            damage=damage[i],
            state=current_state[i],
            time_to_impact_s=time_to_impact[i],
            parent_edge=parent_edges[i],
        )

    # Sort timeline by time
    timeline.sort(key=lambda ev: ev.t_s)

    return SimulationResult(
        run_id=run_id,
        nodes=nodes_result,
        timeline=timeline,
    )
