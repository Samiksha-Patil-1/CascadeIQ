# System patterns
Architecture: Next.js UI -> FastAPI routes -> services -> pure Python engine -> SQLite.
Engine modules: graph_io, structure, propagation, montecarlo, metrics, risk, mitigations, optimizer, explain.
Core model: damage d in [0,1], monotone. tau_e = w * kappa(kind) * (1 - m_e). Group damage is the product over alternative providers. Node loss is noisy-OR over groups. Event-driven simulation with edge delays. States: healthy < 0.2 <= degraded < 0.6 <= failed.
Evaluators: deterministic (timeline, optimizer, ranking) and Monte Carlo (probabilities, CIs).
Invariants: edge points dependent -> provider, failure flows the other way. Pure engine.
Seeded RNG only. Graph immutable, mitigations return a copy. Same seed for compare runs.
Impact attached to capability nodes only. Every UI number comes from the engine.
Optimizer: candidate generation, relevance filter, lazy greedy, best-single guard, exact solver as test oracle, knee point on cost-benefit curve.
