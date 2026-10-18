# CascadeIQ Demo Guide

## Three-Minute Script
1. **0:00 - Load sample**: Open app, click Load sample, point at the graph. Explain 34 services modeled as a dependency graph.
2. **0:20 - Structure panel**: Highlight hidden single point of failure (auth-db) and circular dependency (pricing <-> promo).
3. **0:40 - Inject failure**: Inject auth-db at severity 1.0, press Run. Watch damage cascade against dependency arrows.
4. **1:10 - KPI and Why Chain**: 18 services affected, users and revenue loss computed live. Click red node to trace root cause path.
5. **1:30 - Risk Board**: Show single-failure sweep ranking by Annualized Expected Loss (AEL).
6. **1:50 - Planner**: Set budget slider to 20 pts, click Optimize. Greedy CELF algorithm picks best mitigations.
7. **2:15 - Compare View**: Run baseline vs mitigated on identical scenario and seed. Show side-by-side dampening.
8. **2:40 - Delta Cards & Confidence Intervals**: Point to >40% loss reduction and Monte Carlo confidence bounds.
9. **2:55 - Close**: Reliability spend justified by quantifiable expected loss.
