# CascadeIQ

> Predict the blast radius of failure. Simulate outages before they happen, rank risks quantitatively, and optimize interventions under budget.

## Vision
CascadeIQ turns an architecture diagram into a quantitative risk model. You describe a system as a dependency graph, inject a failure into one component, and CascadeIQ predicts who else goes down, how badly, how fast, and at what cost. It then ranks every component by risk, recommends the cheapest set of fixes, and proves the fix works by re-running the same failure and comparing outcomes side by side.

## Tech Stack
- **Backend**: Python 3.11, FastAPI, Pydantic v2, NumPy, NetworkX, SQLite (SQLModel), pytest, hypothesis, ruff, mypy
- **Frontend**: Next.js (App Router), TypeScript strict, Tailwind CSS, shadcn/ui, Cytoscape.js, Recharts, Zustand, TanStack Query
- **Orchestration**: Docker Compose

## Quick Start
```bash
docker compose up --build
```
- Web UI: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
