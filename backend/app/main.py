"""CascadeIQ FastAPI Application Entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import compare, graphs, optimize, risk, simulate
from app.store.repo import init_repo


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize repository with bundled sample graphs at application startup."""
    init_repo()
    yield


app = FastAPI(
    title="CascadeIQ API",
    description="Predictive Fault Propagation & Mitigation Engine",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under /api
app.include_router(graphs.router, prefix="/api")
app.include_router(simulate.router, prefix="/api")
app.include_router(risk.router, prefix="/api")
app.include_router(optimize.router, prefix="/api")
app.include_router(compare.router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for container checks and CI."""
    return {"status": "ok"}
