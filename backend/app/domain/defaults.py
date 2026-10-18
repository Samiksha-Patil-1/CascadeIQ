"""Default parameters and magic numbers for CascadeIQ.

Source of truth: sections 2.5, 2.8, 2.12 and Appendix A of Build Pack.
"""

from app.domain.enums import EdgeKind, MitigationType, NodeType

# -------------------------------------------------------------------------
# Node Defaults by Type (Appendix A, page 43)
# -------------------------------------------------------------------------
NODE_TYPE_DEFAULTS: dict[NodeType, dict[str, float]] = {
    NodeType.DATABASE: {
        "mtbf_hours": 4000.0,  # Highly reliable cluster, infrequent restarts
        "mttr_minutes": 45.0,  # Failover or recovery takes state replay
    },
    NodeType.SERVICE: {
        "mtbf_hours": 1500.0,  # Standard stateless microservice deployment cycle
        "mttr_minutes": 20.0,  # Pod restart or rollback time
    },
    NodeType.CACHE: {
        "mtbf_hours": 3000.0,  # Redis / Memcached in-memory service
        "mttr_minutes": 15.0,  # Fast in-memory restart
    },
    NodeType.QUEUE: {
        "mtbf_hours": 5000.0,  # Kafka / RabbitMQ cluster
        "mttr_minutes": 30.0,  # Partition rebalance and leader election
    },
    NodeType.EXTERNAL: {
        "mtbf_hours": 2000.0,  # Third party API provider (Stripe, carrier API)
        "mttr_minutes": 60.0,  # External provider incident resolution SLA
    },
    NodeType.GATEWAY: {
        "mtbf_hours": 3000.0,  # API Gateway / Ingress router
        "mttr_minutes": 20.0,  # Config reload / instance bounce
    },
    NodeType.STORAGE: {
        "mtbf_hours": 4000.0,  # S3 / blob storage service
        "mttr_minutes": 45.0,  # State recovery / DNS redirect
    },
}

# -------------------------------------------------------------------------
# Edge Delays in Seconds (Appendix A, page 43)
# -------------------------------------------------------------------------
EDGE_DELAY_DEFAULTS: dict[EdgeKind, float] = {
    EdgeKind.SYNC: 2.0,      # HTTP/gRPC synchronous timeout window
    EdgeKind.DATA: 1.0,      # Database read/write connection timeout
    EdgeKind.CONFIG: 10.0,   # Configuration polling / cache expiry delay
    EdgeKind.ASYNC: 30.0,    # Asynchronous queue drain and buffer delay
}

# -------------------------------------------------------------------------
# Edge Kind Transmission Factors (kappa) (Section 2.8, page 12)
# -------------------------------------------------------------------------
KAPPA_FACTORS: dict[EdgeKind, float] = {
    EdgeKind.SYNC: 1.0,      # Synchronous calls directly block caller execution
    EdgeKind.CONFIG: 0.9,    # Config failures severely impact runtime behavior
    EdgeKind.DATA: 0.8,      # Data failures impact persistence and reads heavily
    EdgeKind.ASYNC: 0.35,    # Asynchronous calls buffer failures temporarily
}

# -------------------------------------------------------------------------
# Health and Degradation Thresholds (Section 2.5, page 10 & Section 2.8, page 13)
# -------------------------------------------------------------------------
DEFAULT_DEGRADE_THRESHOLD: float = 0.2  # Damage threshold where node becomes degraded
DEFAULT_FAIL_THRESHOLD: float = 0.6     # Damage threshold where node becomes failed
DEFAULT_SLO_FLOOR: float = 0.8          # Health (1 - damage) below which SLO is breached

# -------------------------------------------------------------------------
# Mitigation Effects and Default Effort Costs (Section 2.12, pages 17-18)
# -------------------------------------------------------------------------
MITIGATION_EFFECTS: dict[MitigationType, float] = {
    MitigationType.CIRCUIT_BREAKER: 0.35,          # Fast failure dampens downstream cascading
    MitigationType.FALLBACK_CACHE: 0.60,           # Stale cached data shields provider outage
    MitigationType.FALLBACK_DEGRADED: 0.50,        # Static response maintains degraded capability
    MitigationType.BULKHEAD: 0.25,                 # Isolated resource pools contain blast radius
    MitigationType.ASYNC_DECOUPLE: 0.65,           # Converts sync call to async (kappa 1.0 -> 0.35)
    MitigationType.ADD_REPLICA_FAILOVER: 0.60,     # Increases failover quality (+0.60, cap 0.95)
    MitigationType.ADD_REDUNDANT_PROVIDER: 1.0,    # Creates redundant parallel alternative provider
    MitigationType.BREAK_CYCLE: 1.0,               # Removes circular dependency edge
}

MITIGATION_COSTS: dict[MitigationType, float] = {
    MitigationType.CIRCUIT_BREAKER: 2.0,           # 2 effort points / days
    MitigationType.FALLBACK_CACHE: 5.0,            # 5 effort points
    MitigationType.FALLBACK_DEGRADED: 3.0,         # 3 effort points
    MitigationType.BULKHEAD: 3.0,                  # 3 effort points
    MitigationType.ASYNC_DECOUPLE: 8.0,            # 8 effort points (architectural shift)
    MitigationType.ADD_REPLICA_FAILOVER: 6.0,      # 6 effort points (infrastructure provisioning)
    MitigationType.ADD_REDUNDANT_PROVIDER: 10.0,   # 10 effort points (contract & integration)
    MitigationType.BREAK_CYCLE: 4.0,               # 4 effort points (refactoring)
}

# Add-replica specific limits
REPLICA_FAILOVER_BOOST: float = 0.60
REPLICA_FAILOVER_CAP: float = 0.95

# -------------------------------------------------------------------------
# Simulation Invariants and Numerical Thresholds (Section 2.8, page 13)
# -------------------------------------------------------------------------
SIMULATION_EPS: float = 1e-4          # Minimum damage increase to trigger edge push
MAX_SIMULATION_EVENTS: int = 10_000   # Guards against infinite loops in cyclic graphs
DEFAULT_SIMULATION_SEED: int = 42     # Default reproducible seed
DEFAULT_MC_TRIALS: int = 2000         # Default Monte Carlo sample trials
HOURS_PER_YEAR: float = 8760.0        # Constant for annual incident frequency
