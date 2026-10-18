"""Unit tests for Pydantic models (T1.1)."""

import pytest
from pydantic import ValidationError

from app.domain.enums import EdgeKind, MitigationType, NodeType
from app.domain.models import Edge, FailureInjection, MitigationItem, Node, Scenario


def test_node_valid_creation() -> None:
    node = Node(
        id="auth-db",
        name="Auth Database",
        type=NodeType.DATABASE,
        tier=0,
        owner="identity-team",
        replicas=1,
        failover_quality=0.0,
        user_facing=False,
    )
    assert node.id == "auth-db"
    assert node.mtbf_hours == 4000.0  # defaulted from NODE_TYPE_DEFAULTS
    assert node.mttr_minutes == 45.0  # defaulted from NODE_TYPE_DEFAULTS


def test_node_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Node(
            id="auth-db",
            name="Auth Database",
            type=NodeType.DATABASE,
            tier=0,
            unknown_property="illegal",  # type: ignore[call-arg]
        )


def test_node_id_kebab_case() -> None:
    with pytest.raises(ValidationError) as exc:
        Node(
            id="Auth_DB_Invalid",
            name="Auth Database",
            type=NodeType.DATABASE,
            tier=0,
        )
    assert "kebab-case" in str(exc.value)


def test_node_ranges_validated() -> None:
    # failover_quality > 1.0
    with pytest.raises(ValidationError):
        Node(
            id="auth-db",
            name="Auth Database",
            type=NodeType.DATABASE,
            tier=0,
            failover_quality=1.5,
        )

    # tier > 3
    with pytest.raises(ValidationError):
        Node(
            id="auth-db",
            name="Auth Database",
            type=NodeType.DATABASE,
            tier=4,
        )

    # degrade_threshold > fail_threshold
    with pytest.raises(ValidationError):
        Node(
            id="auth-db",
            name="Auth Database",
            type=NodeType.DATABASE,
            tier=0,
            degrade_threshold=0.8,
            fail_threshold=0.4,
        )


def test_edge_valid_creation_and_defaults() -> None:
    edge = Edge(
        source="api-gateway",
        target="auth-service",
        kind=EdgeKind.SYNC,
        strength=0.9,
    )
    assert edge.source == "api-gateway"
    assert edge.target == "auth-service"
    assert edge.delay_s == 2.0  # defaulted for sync
    assert edge.strength == 0.9


def test_edge_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        Edge(
            source="api-gateway",
            target="auth-service",
            unexpected_field=123,  # type: ignore[call-arg]
        )


def test_edge_strength_range() -> None:
    with pytest.raises(ValidationError):
        Edge(
            source="api-gateway",
            target="auth-service",
            strength=1.5,
        )


def test_scenario_and_failure_injection() -> None:
    failure = FailureInjection(node_id="auth-db", severity=1.0, start_s=0.0)
    scenario = Scenario(failures=[failure], outage_minutes=30.0, seed=42)
    assert len(scenario.failures) == 1
    assert scenario.failures[0].node_id == "auth-db"
    assert scenario.seed == 42


def test_mitigation_item_model() -> None:
    item = MitigationItem(
        id="m-1",
        type=MitigationType.CIRCUIT_BREAKER,
        target={"edge": ["checkout-service", "auth-service"]},
        cost=2.0,
    )
    assert item.cost == 2.0
    assert item.type == MitigationType.CIRCUIT_BREAKER
