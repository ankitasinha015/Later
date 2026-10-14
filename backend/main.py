"""FastAPI application for Later.

Phase 1 scaffold: only /health exists. Saves, screenshots and the MCP
adapter get added on top of a shared service layer (see docs/TOOLS.md).
"""

from fastapi import FastAPI

app = FastAPI(
    title="Later",
    description="Agents that turn saved screenshots into things you do.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Returns ok when the app is serving requests."""
    return {"status": "ok", "service": "later-backend", "version": "0.1.0"}
