"""Graph parsing, validation, CSV import/export, and indexed adjacency representation.

Implements section 2.6, 2.7, and 2.16 from ARCHITECTURE.md.
"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import EdgeKind, NodeType
from app.domain.errors import (
    DanglingEdgeError,
    DuplicateNodeIdError,
    SelfLoopError,
    ValueOutOfRangeError,
)
from app.domain.models import Edge, Graph, Node


def validate_graph(graph: Graph) -> None:
    """Validate graph invariants: unique IDs, no dangling edges, no self-loops, and valid ranges."""
    seen_node_ids: set[str] = set()

    for node in graph.nodes:
        if node.id in seen_node_ids:
            raise DuplicateNodeIdError(node.id)
        seen_node_ids.add(node.id)

        # Validate range constraints
        if not (0.0 <= node.failover_quality <= 1.0):
            raise ValueOutOfRangeError("failover_quality", node.failover_quality, node.id)
        if not (0.0 <= node.slo_floor <= 1.0):
            raise ValueOutOfRangeError("slo_floor", node.slo_floor, node.id)
        if not (0.0 <= node.degrade_threshold <= 1.0):
            raise ValueOutOfRangeError("degrade_threshold", node.degrade_threshold, node.id)
        if not (0.0 <= node.fail_threshold <= 1.0):
            raise ValueOutOfRangeError("fail_threshold", node.fail_threshold, node.id)

    for edge in graph.edges:
        if edge.source == edge.target:
            raise SelfLoopError(edge.source)
        if edge.source not in seen_node_ids:
            raise DanglingEdgeError(edge.source, edge.target, edge.source)
        if edge.target not in seen_node_ids:
            raise DanglingEdgeError(edge.source, edge.target, edge.target)

        if not (0.0 <= edge.strength <= 1.0):
            raise ValueOutOfRangeError("strength", edge.strength, f"{edge.source}->{edge.target}")


def load_graph(data: dict[str, Any] | str) -> Graph:
    """Parse a Graph model from a dictionary or JSON string, then validate invariants."""
    if isinstance(data, str):
        parsed = json.loads(data)
    else:
        parsed = data

    graph = Graph.model_validate(parsed)
    validate_graph(graph)
    return graph


@dataclass(frozen=True)
class IndexedEdge:
    """Internal integer-indexed edge representation for performance."""

    source: int
    target: int
    kind: EdgeKind
    strength: float
    delay_s: float
    group: str | None
    mitigations: tuple[str, ...] = field(default_factory=tuple)


class IndexedGraph:
    """Integer index-based graph adjacency structure for pure algorithmic computations.

    Conventions:
    - Edge (u, v): u is source (dependent), v is target (provider).
    - Failure flows in the reverse direction: from target v to dependent u.
    - dependents(v): returns nodes that depend on v.
    - providers(u): returns nodes that u depends on.
    """

    def __init__(self, graph: Graph) -> None:
        self.raw_graph = graph
        self.node_to_idx: dict[str, int] = {node.id: idx for idx, node in enumerate(graph.nodes)}
        self.idx_to_node: list[Node] = list(graph.nodes)
        self.num_nodes: int = len(graph.nodes)

        # Adjacency lists by integer index
        self._provider_edges: list[list[IndexedEdge]] = [[] for _ in range(self.num_nodes)]
        self._dependent_edges: list[list[IndexedEdge]] = [[] for _ in range(self.num_nodes)]

        for e in graph.edges:
            src_idx = self.node_to_idx[e.source]
            tgt_idx = self.node_to_idx[e.target]
            indexed_e = IndexedEdge(
                source=src_idx,
                target=tgt_idx,
                kind=e.kind,
                strength=e.strength,
                delay_s=e.delay_s,
                group=e.group,
                mitigations=tuple(e.mitigations),
            )
            # source depends on target:
            self._provider_edges[src_idx].append(indexed_e)
            # target has dependent source:
            self._dependent_edges[tgt_idx].append(indexed_e)

    def to_index(self, node_id_or_idx: int | str) -> int:
        """Resolve node ID or index into an integer index."""
        if isinstance(node_id_or_idx, int):
            return node_id_or_idx
        return self.node_to_idx[node_id_or_idx]

    def to_id(self, idx: int) -> str:
        """Resolve integer index to node string ID."""
        return self.idx_to_node[idx].id

    def providers(self, node: int | str) -> list[int]:
        """Return list of provider node indices that `node` depends on."""
        idx = self.to_index(node)
        return [e.target for e in self._provider_edges[idx]]

    def dependents(self, node: int | str) -> list[int]:
        """Return list of dependent node indices that depend on `node` (where failure flows)."""
        idx = self.to_index(node)
        return [e.source for e in self._dependent_edges[idx]]

    def dependents_edges(self, node: int | str) -> list[IndexedEdge]:
        """Return edges whose target/provider is `node`."""
        idx = self.to_index(node)
        return self._dependent_edges[idx]

    def provider_edges(self, node: int | str) -> list[IndexedEdge]:
        """Return edges whose source/dependent is `node`."""
        idx = self.to_index(node)
        return self._provider_edges[idx]


# -------------------------------------------------------------------------
# CSV Import / Export Helpers (Section 2.7, T1.4)
# -------------------------------------------------------------------------


def export_graph_to_csv(graph: Graph) -> tuple[str, str]:
    """Export a Graph into two CSV string buffers: (nodes_csv, edges_csv)."""
    # Nodes CSV
    nodes_out = io.StringIO()
    node_writer = csv.writer(nodes_out, lineterminator="\n")
    node_writer.writerow(
        [
            "id",
            "name",
            "type",
            "tier",
            "owner",
            "replicas",
            "failover_quality",
            "mtbf_hours",
            "mttr_minutes",
            "user_facing",
            "users_per_min",
            "revenue_per_min",
            "slo_floor",
            "degrade_threshold",
            "fail_threshold",
        ]
    )
    for n in graph.nodes:
        node_writer.writerow(
            [
                n.id,
                n.name,
                n.type.value,
                n.tier,
                n.owner,
                n.replicas,
                f"{n.failover_quality:.4f}",
                f"{n.mtbf_hours:.2f}",
                f"{n.mttr_minutes:.2f}",
                str(n.user_facing).lower(),
                f"{n.users_per_min:.2f}",
                f"{n.revenue_per_min:.2f}",
                f"{n.slo_floor:.4f}",
                f"{n.degrade_threshold:.4f}",
                f"{n.fail_threshold:.4f}",
            ]
        )

    # Edges CSV
    edges_out = io.StringIO()
    edge_writer = csv.writer(edges_out, lineterminator="\n")
    edge_writer.writerow(
        [
            "source",
            "target",
            "kind",
            "strength",
            "delay_s",
            "group",
            "mitigations",
        ]
    )
    for e in graph.edges:
        edge_writer.writerow(
            [
                e.source,
                e.target,
                e.kind.value,
                f"{e.strength:.4f}",
                f"{e.delay_s:.2f}",
                e.group or "",
                ";".join(e.mitigations),
            ]
        )

    return nodes_out.getvalue(), edges_out.getvalue()


def load_graph_from_csv(
    nodes_csv: str,
    edges_csv: str,
    graph_id: str = "imported-graph",
    graph_name: str = "Imported Graph",
) -> Graph:
    """Construct and validate a Graph from nodes.csv and edges.csv contents."""
    node_reader = csv.DictReader(io.StringIO(nodes_csv))
    nodes: list[Node] = []
    for row in node_reader:
        nodes.append(
            Node(
                id=row["id"],
                name=row["name"],
                type=NodeType(row["type"]),
                tier=int(row["tier"]),
                owner=row["owner"],
                replicas=int(row["replicas"]),
                failover_quality=float(row["failover_quality"]),
                mtbf_hours=float(row["mtbf_hours"]),
                mttr_minutes=float(row["mttr_minutes"]),
                user_facing=row["user_facing"].strip().lower() in ("true", "1", "yes"),
                users_per_min=float(row["users_per_min"]),
                revenue_per_min=float(row["revenue_per_min"]),
                slo_floor=float(row["slo_floor"]),
                degrade_threshold=float(row["degrade_threshold"]),
                fail_threshold=float(row["fail_threshold"]),
            )
        )

    edge_reader = csv.DictReader(io.StringIO(edges_csv))
    edges: list[Edge] = []
    for row in edge_reader:
        mitigations_val = row.get("mitigations", "").strip()
        mitigations = (
            [m.strip() for m in mitigations_val.split(";") if m.strip()] if mitigations_val else []
        )
        group_val = row.get("group", "").strip()
        edges.append(
            Edge(
                source=row["source"],
                target=row["target"],
                kind=EdgeKind(row["kind"]),
                strength=float(row["strength"]),
                delay_s=float(row["delay_s"]),
                group=group_val if group_val else None,
                mitigations=mitigations,
            )
        )

    graph = Graph(id=graph_id, name=graph_name, nodes=nodes, edges=edges)
    validate_graph(graph)
    return graph
