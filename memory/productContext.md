# Product context
Problem: teams discover blast radius during incidents. Chaos tools are risky, observability explains the past, architecture reviews are qualitative.
Users: SRE or platform engineer (what to harden first), engineering manager (justify spend in money), demo audience (clear story, probe-able depth).
Experience goals: first cascade in under 60 seconds, every red node can explain why, one screen answers one question, numbers always beside the animation.
Sample system: e-commerce platform with 34 services, one hidden single point of failure (auth-db) and one circular dependency (pricing and promo). See docs/DEMO.md.
Honesty: the model is a mean-field approximation with editable assumptions. Always say so.
