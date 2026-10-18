"""Typed exceptions for CascadeIQ domain validation and engine."""


class CascadeIQError(Exception):
    """Base error for all CascadeIQ exceptions."""

    def __init__(self, message: str, details: dict[str, str | float | int | None] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class GraphValidationError(CascadeIQError):
    """Base error for graph validation failures."""
    pass


class DuplicateNodeIdError(GraphValidationError):
    """Raised when a graph contains duplicate node IDs."""

    def __init__(self, node_id: str) -> None:
        super().__init__(
            f"Duplicate node ID found: '{node_id}'. Node IDs must be unique.",
            {"node_id": node_id},
        )
        self.node_id = node_id


class DanglingEdgeError(GraphValidationError):
    """Raised when an edge refers to a node ID that does not exist in the graph."""

    def __init__(self, source: str, target: str, missing_id: str) -> None:
        super().__init__(
            f"Edge from '{source}' to '{target}' points to missing node '{missing_id}'.",
            {"source": source, "target": target, "missing_id": missing_id},
        )
        self.source = source
        self.target = target
        self.missing_id = missing_id


class ValueOutOfRangeError(GraphValidationError):
    """Raised when a probability, strength, or damage parameter is outside [0.0, 1.0]."""

    def __init__(self, field_name: str, value: float, entity_id: str) -> None:
        super().__init__(
            f"Value {value} for '{field_name}' on '{entity_id}' is outside the valid range [0.0, 1.0].",
            {"field": field_name, "value": value, "entity_id": entity_id},
        )
        self.field_name = field_name
        self.value = value
        self.entity_id = entity_id


class SelfLoopError(GraphValidationError):
    """Raised when an edge has identical source and target."""

    def __init__(self, node_id: str) -> None:
        super().__init__(
            f"Self-loop detected on node '{node_id}'. A service cannot depend on itself directly.",
            {"node_id": node_id},
        )
        self.node_id = node_id


class ScenarioError(CascadeIQError):
    """Raised when a simulation scenario contains invalid references or parameters."""
    pass


class NodeNotFoundError(ScenarioError):
    """Raised when a scenario references a node not present in the graph."""

    def __init__(self, node_id: str) -> None:
        super().__init__(
            f"Node '{node_id}' referenced in scenario was not found in the graph.",
            {"node_id": node_id},
        )
        self.node_id = node_id
