# CascadeIQ Task Plan

## Phase 0: Setup
- T0.1: Create monorepo, folders from section 2.4, README stub
- T0.2: Backend skeleton: FastAPI, pytest, ruff, mypy, health route
- T0.3: Frontend skeleton: Next.js, Tailwind, shadcn/ui, Cytoscape installed
- T0.4: Docker Compose for both services

## Phase 1: Domain model and graph I/O
- T1.1: Pydantic models for Node, Edge, Scenario, MitigationItem, enums and defaults.py
- T1.2: load_graph and validate_graph
- T1.3: Internal index-based adjacency with dependents(u) and providers(v)
- T1.4: CSV import (nodes.csv, edges.csv)
- T1.5: Build the e-commerce sample (Appendix A)

## Phase 2: Structural analysis
- T2.1: Transitive dependents (reverse BFS)
- T2.2: Tarjan SCC, condensation, topological layers
- T2.3: Articulation points, PageRank, betweenness through NetworkX wrappers
- T2.4: Single point of failure rule
- T2.5: GET /graphs/{id}/structure

## Phase 3: Deterministic propagation
- T3.1: Edge transmission tau with kind factors and mitigation combination
- T3.2: Group damage (alternatives) and noisy-OR node loss
- T3.3: Event-driven simulate() with min-heap and delays
- T3.4: Cycle safety and termination (EPS, MAX_EVENTS)
- T3.5: Dijkstra cross-check of time_to_impact
- T3.6: Parent-edge tracking

## Phase 4: Metrics and risk ranking
- T4.1: summarize(): affected, failed, users, money per hour, outage cost, SLO breaches
- T4.2: Single-failure sweep and AEL
- T4.3: Criticality index and normalization
- T4.4: POST /simulate and POST /risk routes

## Phase 5: Mitigations and compare
- T5.1: Mitigation catalog with effects and costs
- T5.2: apply(graph, plan) returns a new graph, never mutates
- T5.3: Compare endpoint
- T5.4: Property test: adding a mitigation never increases outage cost
- T5.5: Dominator chokepoints

## Phase 6: Optimizer
- T6.1: Candidate generator and relevance filter
- T6.2: Greedy with marginal gain per cost
- T6.3: Lazy evaluation (CELF)
- T6.4: Best-single-item guard
- T6.5: Exact solver for up to 20 candidates
- T6.6: Oracle test: greedy gap
- T6.7: Cost-benefit curve and knee point
- T6.8: POST /optimize

## Phase 7: Monte Carlo and explainability
- T7.1: Vectorized Monte Carlo with common random numbers
- T7.2: Confidence intervals
- T7.3: Monte Carlo mode in /simulate and /compare
- T7.4: why() chain and contribution shares
- T7.5: Benchmarks in CI

## Phase 8: Frontend core
- T8.1: Generate TS client from OpenAPI
- T8.2: Library screen, sample loader, import dialog
- T8.3: GraphCanvas with dagre layout, node and edge encoding, state colors
- T8.4: NodeInspector and selection
- T8.5: StructurePanel
- T8.6: Parameter editing with re-validation

## Phase 9: Simulation Lab, Risk, Planner, Compare
- T9.1: FailurePicker and Run
- T9.2: Timeline scrubber and replay engine
- T9.3: KpiCards with animated counters
- T9.4: RiskTable and heatmap
- T9.5: Planner: budget slider, optimize, candidate checklist, curve
- T9.6: CompareView with two synced canvases and delta cards
- T9.7: WhyChain component

## Phase 10: Guided demo and polish
- T10.1: Guided demo mode
- T10.2: Empty, loading and error states everywhere
- T10.3: Reduced motion, keyboard shortcuts, aria-live summary
- T10.4: Playwright end-to-end test of the demo

## Phase 11: Documentation and delivery
- T11.1: README with problem, screenshots, architecture diagram, how to run
- T11.2: Report export (Markdown and JSON)
- T11.3: Record demo video and tag release
