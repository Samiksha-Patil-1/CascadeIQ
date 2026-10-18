# Product Requirements Document (PRD)

## 1.1 Vision
CascadeIQ turns an architecture diagram into a quantitative risk model. You describe a system as a dependency graph, inject a failure into one component, and CascadeIQ predicts who else goes down, how badly, how fast and at what cost. It then ranks every component by risk, recommends the cheapest set of fixes, and proves the fix works by re-running the same failure and comparing outcomes side by side.

One-line pitch: chaos engineering without the chaos. Simulate the outage before it happens, then fix the right thing first.

## 1.2 Problem
- Modern systems have dozens to thousands of services with tangled, often undocumented dependencies.
- Teams learn the true blast radius of a component during an incident, at the worst possible time.
- Chaos tools inject real faults (risky, slow to set up, need production-like environments). Observability tools explain what already happened. Architecture reviews are qualitative.
- Reliability budgets get spent by intuition, not by expected loss.
- Gap: a predictive, quantitative, explainable and prioritizing tool that runs on a graph in seconds.

## 1.3 Users
- **SRE / platform engineer**: Which dependency do I harden first? (Ranked risk board, chokepoints, mitigation plan)
- **Engineering manager / CTO**: Justify reliability spend in money (Before vs after loss, cost-benefit curve)
- **Demo audience / judges**: A clear story in 3 minutes, depth if probed (Guided demo, explainable math, reproducible runs)

## 1.4 Goals and Non-goals
### Goals
- G1: Predict cascade for injected failure (affected set, severity, timing).
- G2: Quantify impact (nodes, users, money per hour, SLO breaches).
- G3: Prioritize (rank services by risk-weighted criticality).
- G4: Optimize (recommend best mitigation set under budget, delta before/after).
- G5: Explain (every number traces back to graph paths).

### Non-goals v1
- Live monitoring or auto-discovery from production.
- Real fault injection.
- ML-trained propagation models.
- Multi-tenant auth, billing, teams.
- Packet-level network modelling.
