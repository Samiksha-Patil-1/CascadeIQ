"""Pydantic models for CascadeIQ domain entities.

Strictly follows section 2.5 of the Build Pack with extra='forbid'
and range validations.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.defaults import (
    DEFAULT_DEGRADE_THRESHOLD,
    DEFAULT_FAIL_THRESHOLD,
    DEFAULT_SLO_FLOOR,
    EDGE_DELAY_DEFAULTS,
    NODE_TYPE_DEFAULTS,
)
from app.domain.enums import EdgeKind, MitigationType, NodeType

KEBAB_CASE_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class DomainBaseModel(BaseModel):
    """Base model forbidding unexpected extra fields across the domain."""

    model_config = ConfigDict(extra="forbid")


class Node(DomainBaseModel):
    """Represents a service, database, cache, or gateway in the system."""

    id: str = Field(description="Unique node identifier in kebab-case")
    name: str = Field(description="Human-readable node name")
    type: NodeType = Field(description="Component architectural type")
    tier: int = Field(
        ge=0, le=3, description="Criticality tier: 0 is mission-critical, 3 is best effort"
    )
    owner: str = Field(default="unassigned", description="Owning team")
    replicas: int = Field(default=1, ge=1, description="Active replica count")
    failover_quality: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Failover effectiveness (rho) between 0.0 and 1.0",
    )
    mtbf_hours: float = Field(
        default=0.0,
        gt=0.0,
        description="Mean time between failures in hours",
    )
    mttr_minutes: float = Field(
        default=0.0,
        gt=0.0,
        description="Mean time to recover in minutes",
    )
    user_facing: bool = Field(
        default=False, description="Whether node serves end-user traffic directly"
    )
    users_per_min: float = Field(
        default=0.0,
        ge=0.0,
        description="Active users per minute (only for user-facing capability nodes)",
    )
    revenue_per_min: float = Field(
        default=0.0,
        ge=0.0,
        description="Revenue flow in currency/min (only for capability nodes)",
    )
    slo_floor: float = Field(
        default=DEFAULT_SLO_FLOOR,
        ge=0.0,
        le=1.0,
        description="Health floor below which SLO is breached",
    )
    degrade_threshold: float = Field(
        default=DEFAULT_DEGRADE_THRESHOLD,
        ge=0.0,
        le=1.0,
        description="Damage fraction at which node is considered degraded",
    )
    fail_threshold: float = Field(
        default=DEFAULT_FAIL_THRESHOLD,
        ge=0.0,
        le=1.0,
        description="Damage fraction at which node is considered failed",
    )

    @field_validator("id")
    @classmethod
    def validate_kebab_case_id(cls, v: str) -> str:
        if not KEBAB_CASE_PATTERN.match(v):
            raise ValueError(f"Node id '{v}' must be kebab-case (e.g. 'auth-db', 'api-gateway').")
        return v

    @model_validator(mode="before")
    @classmethod
    def apply_type_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            node_type_val = data.get("type")
            if node_type_val:
                try:
                    nt = NodeType(node_type_val)
                    defaults = NODE_TYPE_DEFAULTS.get(nt, {})
                    if "mtbf_hours" not in data or data["mtbf_hours"] == 0.0:
                        data["mtbf_hours"] = defaults.get("mtbf_hours", 2000.0)
                    if "mttr_minutes" not in data or data["mttr_minutes"] == 0.0:
                        data["mttr_minutes"] = defaults.get("mttr_minutes", 30.0)
                except ValueError:
                    pass
        return data

    @model_validator(mode="after")
    def validate_thresholds(self) -> Node:
        if self.degrade_threshold > self.fail_threshold:
            err = (
                f"degrade_threshold ({self.degrade_threshold}) cannot exceed "
                f"fail_threshold ({self.fail_threshold})"
            )
            raise ValueError(err)
        return self


class Edge(DomainBaseModel):
    """Represents a dependency: source depends on target (failure flows target -> source)."""

    source: str = Field(description="Dependent node id")
    target: str = Field(description="Provider node id")
    kind: EdgeKind = Field(default=EdgeKind.SYNC, description="Call/dependency mechanism")
    strength: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Dependency coupling strength (w) between 0.0 and 1.0",
    )
    delay_s: float = Field(
        default=0.0,
        ge=0.0,
        description="Propagation delay in seconds (e.g. timeouts, queue drain)",
    )
    group: str | None = Field(
        default=None,
        description="Redundancy group: edges with identical group act as alternative providers",
    )
    mitigations: list[str] = Field(
        default_factory=list,
        description="List of applied mitigation types on this edge",
    )

    @model_validator(mode="before")
    @classmethod
    def apply_delay_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            kind_val = data.get("kind", EdgeKind.SYNC)
            try:
                kind = EdgeKind(kind_val)
                if "delay_s" not in data or data["delay_s"] == 0.0:
                    data["delay_s"] = EDGE_DELAY_DEFAULTS.get(kind, 2.0)
            except ValueError:
                pass
        return data


class Graph(DomainBaseModel):
    """System dependency graph representation."""

    id: str = Field(description="Unique graph identifier")
    name: str = Field(description="Human-readable system architecture name")
    nodes: list[Node] = Field(default_factory=list, description="System components")
    edges: list[Edge] = Field(default_factory=list, description="Directed dependencies")


class FailureInjection(DomainBaseModel):
    """Injected failure event on a specific node."""

    node_id: str = Field(description="Target node to inject failure on")
    severity: float = Field(
        ge=0.0,
        le=1.0,
        description="Injected failure severity from 0.0 (healthy) to 1.0 (total loss)",
    )
    start_s: float = Field(default=0.0, ge=0.0, description="Outage start time in seconds")


class Scenario(DomainBaseModel):
    """Simulation scenario specifying initial failure events and duration."""

    failures: list[FailureInjection] = Field(description="Injected failure set")
    outage_minutes: float = Field(gt=0.0, description="Outage duration in minutes")
    seed: int = Field(default=42, description="RNG seed for reproducibility")


class MitigationItem(DomainBaseModel):
    """An individual mitigation action applied to a node or edge."""

    id: str = Field(description="Unique mitigation item ID")
    type: MitigationType = Field(description="Mitigation archetype")
    target: dict[str, Any] = Field(
        description="Target element (e.g. {'edge': [src, tgt]} or {'node': id})"
    )
    cost: float = Field(ge=0.0, description="Effort points or financial cost")
