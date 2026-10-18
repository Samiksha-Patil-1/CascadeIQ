# Decision log (append only; newest last)
D-001 Python engine with NetworkX only for textbook algorithms; propagation, Monte Carlo, risk and optimizer written from scratch because they are the centerpiece.
D-002 Two evaluators: deterministic for timeline and optimization, Monte Carlo for uncertainty. Reported separately, never mixed.
D-003 Alternatives are modeled with edge groups (product of damage) instead of a k-of-n parameter, for simplicity. Revisit if k-of-n is needed.
D-004 Mitigation effects combine multiplicatively to model diminishing returns.
D-005 Revenue and users attach to capability nodes only, to prevent double counting.
D-006 Common random numbers for baseline vs mitigated Monte Carlo comparisons.
D-007 Timeline is computed server side and replayed client side; no websockets in v1.
D-008 SQLite for v1; PostgreSQL only if multi-user is added.
D-009 Compare endpoint returns `mitigated_graph` so frontend dynamically renders architectural changes (applied mitigations, severed cycle edges) side-by-side with baseline.
D-010 Why-chain explainer returns consistent node telemetry across all discrete states (healthy, degraded, failed) to avoid frontend empty/undefined states.
