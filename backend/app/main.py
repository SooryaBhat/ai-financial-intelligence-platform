"""
AI Financial Intelligence Platform — FastAPI Application Entry Point

Startup sequence:
  1. Configure structured logging (Loguru)
  2. Create FastAPI app with metadata
  3. Add CORS middleware
  4. Add request logging middleware
  5. Register exception handlers
  6. Mount auth router (public — no auth required)
  7. Mount all v1 API routers (protected via dependencies)
  8. Add health check endpoint

Run:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.exceptions.handlers import register_exception_handlers
from app.middleware.logging import LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler — called on startup and shutdown."""
    configure_logging()
    logger.info(
        "[STARTUP] {} v{} starting | env={}",
        settings.app_name,
        settings.app_version,
        settings.app_env,
    )
    yield
    logger.info("Application shutting down.")


def create_app() -> FastAPI:
    """Factory function that creates and configures the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "AI Financial Intelligence Platform — REST API\n\n"
            "Multi-tenant SaaS backend with:\n"
            "- Supabase Auth + JWT authentication\n"
            "- Role-Based Access Control (RBAC)\n"
            "- Complete ERP module coverage\n"
            "- AI/ML prediction endpoints\n"
            "- Conversational AI assistant\n\n"
            "**All protected endpoints require:**\n"
            "- `Authorization: Bearer <token>` header\n"
            "- `X-Company-ID: <uuid>` header"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # ── CORS ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Response-Time"],
    )

    # ── Request logging ───────────────────────────────────────
    app.add_middleware(LoggingMiddleware)

    # ── Exception handlers ────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────
    # Auth routes (public)
    app.include_router(auth_router, prefix="/api/v1")

    # All protected module routes
    app.include_router(api_router)

    # ── Health check ──────────────────────────────────────────
    @app.get(
        "/health",
        tags=["Health"],
        summary="Health check",
        description="Returns 200 OK when the service is running.",
    )
    def health():
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
        }

    @app.get("/", tags=["Health"], summary="Root", include_in_schema=False)
    def root():
        return {
            "message": f"Welcome to {settings.app_name} API",
            "docs": "/docs",
            "version": settings.app_version,
        }

    logger.info("FastAPI app created | {} routes registered", len(app.routes))
    return app


# The ASGI application instance
app = create_app()
