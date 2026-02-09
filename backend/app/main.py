"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.auth import router as auth_router, limiter
from app.api.notes import router as notes_router, upload_limiter
from app.api.mistakes import router as mistakes_router
from app.api.quizzes import router as quizzes_router
from app.api.mindmaps import router as mindmaps_router
from app.api.analytics import router as analytics_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.database import engine, Base
from app.utils.logging import setup_logging
from app.middleware.csrf import CSRFMiddleware

settings = get_settings()

# Setup logging
setup_logging(log_level="INFO")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    # Startup
    logger.info("Starting StudyNotesManager API")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Shutdown
    logger.info("Shutting down StudyNotesManager API")

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered study notes management system",
    lifespan=lifespan,
)

# Set up rate limiting
app.state.limiter = limiter
app.state.upload_limiter = upload_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CSRF protection
app.add_middleware(CSRFMiddleware)

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(mistakes_router)
app.include_router(quizzes_router)
app.include_router(mindmaps_router)
app.include_router(analytics_router)

@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "StudyNotesManager API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
