"""CausalLens API entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.db import dispose_engine, get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await dispose_engine()


settings = get_settings()

app = FastAPI(
    title="CausalLens API",
    description="Statistical engine for A/B testing, Bayesian inference, and causal impact analysis.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "causallens-api", "version": "0.1.0"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — deliberately does not touch the database."""
    return {"status": "ok", "environment": settings.environment}


@app.get("/health/db")
async def health_db() -> dict[str, str | bool]:
    """Readiness probe for Neon. Reports rather than raises, so a suspended
    free-tier compute doesn't read as a total outage."""
    engine = get_engine()
    if engine is None:
        return {"configured": False, "connected": False, "detail": "DATABASE_URL not set"}

    try:
        async with engine.connect() as conn:
            version = (await conn.execute(text("select version()"))).scalar_one()
        return {"configured": True, "connected": True, "server": str(version)}
    except Exception as exc:  # noqa: BLE001 — surfaced to the caller as status
        return {"configured": True, "connected": False, "detail": f"{type(exc).__name__}: {exc}"}
