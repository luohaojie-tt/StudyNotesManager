"""Main FastAPI application."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.auth import router as auth_router
from app.api.notes import router as notes_router
from app.api.mistakes import router as mistakes_router
from app.api.quizzes import router as quizzes_router
from app.api.mindmaps import router as mindmaps_router
from app.api.analytics import router as analytics_router
from app.core.config import get_settings
from app.core.database import engine, Base
from app.utils.logging import setup_logging

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
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
    }

@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
