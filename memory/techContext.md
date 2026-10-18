# Tech context
Backend: Python 3.11, FastAPI, Pydantic v2, NumPy, NetworkX, SQLModel + SQLite, pytest, hypothesis, ruff, mypy.
Frontend: Next.js (App Router), TypeScript strict, Tailwind, shadcn/ui, Cytoscape.js (dagre, fcose), Recharts, Zustand, TanStack Query, openapi-typescript.
Tooling: Docker Compose, GitHub Actions, Playwright.

Commands:
backend test: cd backend && pytest -q
backend lint: ruff check . && mypy app
backend run: uvicorn app.main:app --reload --port 8000
frontend run: cd frontend && npm run dev
types: npm run gen:types (reads /openapi.json)
everything: docker compose up --build

Performance targets: 500 nodes and 2,000 edges simulate under 100 ms, Monte Carlo 2,000 trials under 2 s, optimizer under 10 s on 100 nodes and 50 candidates.
Limits: uploads 5 MB and 5,000 nodes.
