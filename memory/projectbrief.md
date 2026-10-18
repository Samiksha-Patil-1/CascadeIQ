# Project brief: CascadeIQ
One line: model an enterprise system as a dependency graph and predict how one failing service cascades to everything downstream.
Goal: quantify blast radius, rank risks, optimize mitigations, and prove the benefit by comparing before and after on the same failure.
Centerpiece: graph algorithms, fault propagation simulation, risk-weighted prioritization, intervention optimization.
Winning demo: inject a failure into a critical dependency, predict the cascade, apply a mitigation, compare the two outcomes quantitatively.
MVP: graph load and validate, structure analysis, deterministic cascade with timeline, impact metrics, risk ranking, mitigation catalog, compare, greedy optimizer, UI, guided demo.
Non-goals v1: live monitoring, auto-discovery, real fault injection, ML models, multi-tenancy.
Success: demo under 3 minutes, every number from the engine, optimizer within 2 percent of exact on small cases, at least 40 percent loss reduction on the sample at 20 percent budget.
