# Glossary
Blast radius: set of services affected by a failure, with severity and timing.
Dependent / provider: dependent needs provider. Edge source = dependent, target = provider.
Damage (d): fraction of a node's function lost, 0 to 1.
Strength (w): how much a dependent needs a provider, 0 to 1.
Transmission (tau): fraction of provider damage that reaches the dependent over one edge.
Group: set of alternative providers; dependent is hurt only if all are hurt.
Chokepoint: node that dominates a subtree in the failure-propagation graph.
SPOF: single point of failure.
AEL: annualized expected loss = incidents per year x hours per incident x impact per hour.
Time to impact: first time a node reaches degraded.
Knee: point on the cost-benefit curve where extra spend stops paying off.
CRN: common random numbers, same random draws for baseline and mitigated runs.
Capability node: user-visible business function that carries revenue and users.
