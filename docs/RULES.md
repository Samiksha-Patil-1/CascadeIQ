# Engineering and Domain Rules

## 3.1 Domain invariants (never break these)
1. An edge points from dependent to provider. Failure flows from provider to dependent. Use dependents(u) and providers(v) helpers only.
2. Damage, strength, severity and probabilities are in [0, 1]. Validate at the model boundary and assert in tests.
3. Damage never decreases during a run. This is what guarantees termination.
4. Engine functions are pure. No file, network or database access, no global state, no time.now().
5. All randomness comes from a numpy Generator created from the request seed and passed in. Never call random or np.random directly.
6. The engine never mutates its input graph. Mitigations return a new graph.
7. Baseline and mitigated comparisons use the same scenario and the same seed (common random numbers).
8. Revenue and users attach to business capability nodes only. Infrastructure nodes carry zero impact so totals are not double counted.
9. Deterministic results (expected degradation) and Monte Carlo results (probability of failure) are shown with different labels and never combined in one KPI.
10. Every number shown in the UI comes from the engine. No hard-coded demo figures, ever.
11. Mitigation effects combine multiplicatively: m = 1 - product(1 - eff_j).
12. Magic numbers live in domain/defaults.py with a comment explaining the source or reasoning.

## 3.2 Python rules
- Python 3.11, full type hints, mypy strict on app/engine, ruff for lint and format.
- Pydantic v2 models at the API and file boundary. Engine uses plain dataclasses or typed arrays.
- Functions do one thing, ideally under 40 lines. Module-level docstring states the math it implements and references the section number in ARCHITECTURE.md.
- Raise typed errors (GraphValidationError, ScenarioError) and let the API layer map them to the error shape.
- No bare except. No print for logging, use the logging module.

## 3.3 TypeScript and React rules
- TypeScript strict. No any. API types come only from the generated client.
- Components are small and presentational. Data fetching in hooks. Global UI state in one Zustand store.
- Graph state colors come from lib/colors.ts only. Never hard-code a hex in a component.
- Every async view has loading, empty and error states.
- Animations respect prefers-reduced-motion.

## 3.4 API rules
- Contract first: change the Pydantic model, regenerate OpenAPI, regenerate the TS types, then touch the UI.
- Validation errors name the field and the node or edge id.
- No breaking changes once the demo is recorded. Add fields, do not rename.

## 3.5 Testing rules
- A bug fix starts with a failing test.
- Every formula in the architecture document has a hand-computed test. Show the arithmetic in a comment.
- Property tests for invariants 2, 3, 5 and 11 are mandatory.
- Do not mock the engine in API tests.

## 3.6 Git and workflow
- Trunk with short branches named type/short-name.
- Conventional commits: feat, fix, test, docs, refactor, perf, chore.
- Small pull requests (under about 300 lines). CI must pass: ruff, mypy, pytest, frontend lint and build.
- Tag a release before every demo or submission so you can always recover a known-good state.

## 3.8 Definition of done (per task)
- Acceptance criteria in TASKS.md are met.
- Tests added and passing, coverage on touched engine code at least 85 percent.
- Types, lint and format clean.
- Docs or memory updated if behavior or decisions changed.
- Demonstrated once in the running app if it is user-visible.

## 3.9 Forbidden
- Hard-coded demo outputs or fake loading delays.
- Hidden global state or time-dependent behavior in the engine.
- Catching and swallowing errors.
- Adding a dependency without recording the reason in decisionLog.md.
- Rewriting the model equations without updating ARCHITECTURE.md and the golden tests in the same change.
