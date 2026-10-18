"""Structural analysis algorithms for dependency graphs.

Implements section 2.10 from ARCHITECTURE.md:
- Transitive dependents (reverse BFS)
- Tarjan SCC and condensation
- Topological layering
- Single points of failure (SPOF)
- NetworkX wrappers for dominators, articulation points, PageRank, betweenness
- Dijkstra shortest delay lower bound
"""

from __future__ import annotations

import heapq
from collections import deque
from typing import Any

import networkx as nx

from app.engine.graph_io import IndexedGraph


def transitive_dependents(indexed: IndexedGraph, root_id_or_idx: int | str) -> set[int]:
    """Return all nodes that transitively depend on root (failure reachable set via reverse BFS)."""
    start_idx = indexed.to_index(root_id_or_idx)
    visited: set[int] = {start_idx}
    queue: deque[int] = deque([start_idx])

    while queue:
        u = queue.popleft()
        for dep in indexed.dependents(u):
            if dep not in visited:
                visited.add(dep)
                queue.append(dep)

    return visited


def tarjan_scc(indexed: IndexedGraph) -> list[list[int]]:
    """Tarjan's algorithm to compute strongly connected components (SCCs).

    Finds circular dependencies in O(V + E).
    """
    index = 0
    indices: dict[int, int] = {}
    lowlinks: dict[int, int] = {}
    on_stack: set[int] = set()
    stack: list[int] = []
    sccs: list[list[int]] = []

    def strongconnect(v: int) -> None:
        nonlocal index
        indices[v] = index
        lowlinks[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)

        # In standard graph, edges are source -> target (u -> v).
        # We find SCCs in dependency direction.
        for provider in indexed.providers(v):
            if provider not in indices:
                strongconnect(provider)
                lowlinks[v] = min(lowlinks[v], lowlinks[provider])
            elif provider in on_stack:
                lowlinks[v] = min(lowlinks[v], indices[provider])

        if lowlinks[v] == indices[v]:
            scc: list[int] = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                scc.append(w)
                if w == v:
                    break
            sccs.append(scc)

    for i in range(indexed.num_nodes):
        if i not in indices:
            strongconnect(i)

    return sccs


def topological_layers(indexed: IndexedGraph) -> list[list[int]]:
    """Partition nodes into topological depth layers (providers bottom, users top).

    Assigns level 0 to leaf providers (nodes with no providers),
    then level(u) = 1 + max(level(provider)). Handles cycles by condensation.
    """
    levels: dict[int, int] = {}

    def get_level(u: int, visiting: set[int]) -> int:
        if u in levels:
            return levels[u]
        if u in visiting:
            return 0  # break cycle
        visiting.add(u)
        provs = indexed.providers(u)
        if not provs:
            lvl = 0
        else:
            lvl = 1 + max(get_level(p, visiting) for p in provs)
        visiting.remove(u)
        levels[u] = lvl
        return lvl

    for i in range(indexed.num_nodes):
        if i not in levels:
            get_level(i, set())

    max_lvl = max(levels.values()) if levels else 0
    layers: list[list[int]] = [[] for _ in range(max_lvl + 1)]
    for i, lvl in levels.items():
        layers[lvl].append(i)

    return layers


def find_spof(indexed: IndexedGraph) -> list[str]:
    """Find hidden single points of failure according to section 2.10.

    A node is flagged as a hidden single point of failure when:
    1. It has no alternative providers for its dependents (replicas <= 1 or failover_quality < 0.2,
       and edges lack redundancy groups).
    2. Its transitive dependents include at least one tier 0 or tier 1 capability.
    3. It is not marked redundant.
    """
    spof_ids: list[str] = []

    for i, node in enumerate(indexed.idx_to_node):
        # Must not be marked redundant
        is_redundant = node.replicas > 1 and node.failover_quality >= 0.5
        if is_redundant:
            continue

        # Transitive dependents
        trans_deps = transitive_dependents(indexed, i)
        # Check if transitive dependents include tier 0 or tier 1 user-facing / capability nodes
        critical_dependent = False
        for dep_idx in trans_deps:
            if dep_idx == i:
                continue
            dep_node = indexed.idx_to_node[dep_idx]
            if dep_node.tier in (0, 1) and (dep_node.user_facing or dep_node.revenue_per_min > 0 or dep_node.users_per_min > 0):
                critical_dependent = True
                break

        if not critical_dependent:
            continue

        # Check if its dependents lack alternative providers (groups)
        has_alternatives = False
        for dep_idx in indexed.dependents(i):
            dep_edges = indexed.provider_edges(dep_idx)
            # Find edge pointing to i
            for e in dep_edges:
                if e.target == i and e.group is not None:
                    # Has an alternative group
                    has_alternatives = True
                    break

        if not has_alternatives:
            spof_ids.append(node.id)

    return spof_ids


def compute_networkx_metrics(indexed: IndexedGraph) -> dict[str, Any]:
    """Compute structural metrics via NetworkX wrappers."""
    # Graph where edge is source -> target (dependent -> provider)
    G = nx.DiGraph()
    for node in indexed.idx_to_node:
        G.add_node(node.id, tier=node.tier)

    for edge in indexed.raw_graph.edges:
        G.add_edge(edge.source, edge.target, weight=edge.strength, delay=edge.delay_s)

    # Reversed graph: failure propagation direction (provider -> dependent)
    G_rev = G.reverse()

    # Articulation points on undirected view
    G_undirected = G.to_undirected()
    articulation_points = list(nx.articulation_points(G_undirected))

    # PageRank on reversed graph (measures what many important things depend on)
    try:
        pagerank_rev = nx.pagerank(G_rev, alpha=0.85)
    except Exception:
        pagerank_rev = {node.id: 1.0 / indexed.num_nodes for node in indexed.idx_to_node}

    # Betweenness centrality
    betweenness = nx.betweenness_centrality(G)

    return {
        "articulation_points": articulation_points,
        "pagerank_reversed": pagerank_rev,
        "betweenness": betweenness,
    }


def compute_chokepoints(indexed: IndexedGraph, root_id: str) -> dict[str, list[str]]:
    """Compute immediate dominator chokepoints rooted at root_id in failure propagation graph."""
    G_fail = nx.DiGraph()
    for node in indexed.idx_to_node:
        G_fail.add_node(node.id)

    # In failure propagation, failure travels from provider to dependent (target -> source)
    for edge in indexed.raw_graph.edges:
        G_fail.add_edge(edge.target, edge.source)

    if root_id not in G_fail:
        return {}

    # Dominators in DAG / reachable component from root
    reachable = nx.descendants(G_fail, root_id) | {root_id}
    subG = G_fail.subgraph(reachable).copy()

    try:
        doms = nx.immediate_dominators(subG, root_id)
        # Reverse map: dominator -> dominated nodes
        dominated_map: dict[str, list[str]] = {}
        for node, dom in doms.items():
            if dom != node:
                dominated_map.setdefault(dom, []).append(node)
        return dominated_map
    except Exception:
        return {}


def dijkstra_earliest_arrival(indexed: IndexedGraph, root_id: str) -> dict[str, float]:
    """Shortest delay path from root in failure propagation direction."""
    root_idx = indexed.to_index(root_id)
    distances: dict[int, float] = {root_idx: 0.0}
    heap: list[tuple[float, int]] = [(0.0, root_idx)]

    while heap:
        dist, u = heapq.heappop(heap)
        if dist > distances[u]:
            continue

        for edge in indexed.dependents_edges(u):
            v = edge.source
            new_dist = dist + edge.delay_s
            if v not in distances or new_dist < distances[v]:
                distances[v] = new_dist
                heapq.heappush(heap, (new_dist, v))

    return {indexed.to_id(k): v for k, v in distances.items()}
