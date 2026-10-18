"""Domain enumeration types for CascadeIQ."""

from enum import Enum


class NodeType(str, Enum):
    SERVICE = "service"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    EXTERNAL = "external"
    GATEWAY = "gateway"
    STORAGE = "storage"


class EdgeKind(str, Enum):
    SYNC = "sync"
    ASYNC = "async"
    DATA = "data"
    CONFIG = "config"


class NodeState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


class MitigationType(str, Enum):
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK_CACHE = "fallback_cache"
    FALLBACK_DEGRADED = "fallback_degraded"
    BULKHEAD = "bulkhead"
    ASYNC_DECOUPLE = "async_decouple"
    ADD_REPLICA_FAILOVER = "add_replica_failover"
    ADD_REDUNDANT_PROVIDER = "add_redundant_provider"
    BREAK_CYCLE = "break_cycle"
