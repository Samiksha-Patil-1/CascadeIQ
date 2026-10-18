# CascadeIQ Architecture

## 2.1 Principles
1. The engine is pure: no I/O, no globals, randomness only through an injected seeded generator.
2. Graphs are immutable inside the engine. Applying mitigations creates a derived copy.
3. One propagation model, two evaluators: deterministic (timeline, optimizer, ranking) and Monte Carlo (uncertainty).
4. Every output is explainable by a path.
5. Contract first: OpenAPI generates TypeScript types so the UI cannot drift.
6. Simple to run: one container for the API, one for the web app.

## 2.2 Tech Stack
- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, Cytoscape.js, Recharts, Zustand, TanStack Query
- Backend: Python 3.11, FastAPI, Pydantic v2, NumPy, NetworkX, SQLModel + SQLite, pytest, hypothesis, ruff, mypy

## 2.5 Domain Model
- **Node**: id, name, type, tier, owner, replicas, failover_quality, mtbf_hours, mttr_minutes, user_facing, users_per_min, revenue_per_min, slo_floor, degrade_threshold, fail_threshold.
- **Edge**: source (dependent), target (provider), kind (sync, async, data, config), strength (0-1), delay_s, group (alternative providers), mitigations.
- **Scenario**: failures list (node_id, severity, start_s), outage_minutes, seed.
- **MitigationItem**: id, type, target, cost.

## 2.8 Deterministic Propagation Model
1. Edge transmission:
   $\tau_e = w_e \cdot \kappa(\text{kind}_e) \cdot (1 - m_e)$
   where $m_e = 1 - \prod_j (1 - \text{eff}_j)$.
2. Group damage:
   $G_g = \prod_{e \in g} (\tau_e \cdot \text{edge\_damage}_e)$
3. Node loss:
   $L_v = 1 - \prod_g (1 - G_g)$
   $d_v = \max(\text{injected\_damage}_v, L_v)$
   $\text{injected\_damage}_v = \text{severity} \cdot (1 - \text{failover\_quality}_v)$
4. State:
   - HEALTHY if $d < \text{degrade\_threshold}$ (default 0.2)
   - DEGRADED if $\text{degrade\_threshold} \le d < \text{fail\_threshold}$ (default 0.6)
   - FAILED if $d \ge \text{fail\_threshold}$
5. Time simulation: Min-heap event queue driven by $t + \text{delay}_e$.

## 2.9 Monte Carlo Evaluator
- Draws uniform random numbers $U \sim \text{Uniform}(0, 1)$ once per run.
- Edge transmits if $U < \tau_e$.
- Injected node failure: $\text{Bernoulli}(\text{severity} \cdot (1 - \text{failover\_quality}))$.
- Common Random Numbers (CRN) ensure monotonic variance reduction when testing mitigations.

## 2.11 Risk-Weighted Prioritization
$\text{AEL}(v) = \text{incidents\_per\_year}(v) \cdot (\text{mttr\_minutes}(v) / 60) \cdot \text{impact\_per\_hour}(v)$

## 2.12 Mitigation Optimizer
- Lazy greedy (CELF) with best-single-item guard.
- Exact branch-and-bound solver for small graphs ($\le 20$ candidates).
