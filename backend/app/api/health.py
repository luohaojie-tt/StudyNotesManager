"""Health check and monitoring endpoints."""
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check endpoint."""
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "checks": {}
    }
    
    # Check database connection
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "detail": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "detail": f"Database connection failed: {str(e)}"
        }
    
    # Check Redis connection (optional)
    try:
        from app.services.cache_service import cache_service
        redis_available = await cache_service.is_enabled()
        if redis_available:
            health_status["checks"]["redis"] = {
                "status": "healthy",
                "detail": "Redis connection successful"
            }
        else:
            health_status["checks"]["redis"] = {
                "status": "disabled",
                "detail": "Redis not configured or unavailable"
            }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "detail": f"Redis check failed: {str(e)}"
        }
    
    # Check external services
    external_services = {}
    
    # Check DeepSeek API
    if settings.DEEPSEEK_API_KEY:
        external_services["deepseek"] = {
            "status": "configured",
            "detail": "DeepSeek API key is configured"
        }
    else:
        external_services["deepseek"] = {
            "status": "not_configured",
            "detail": "DeepSeek API key not configured"
        }
    
    # Check Baidu OCR
    if settings.BAIDU_OCR_API_KEY and settings.BAIDU_OCR_SECRET_KEY:
        external_services["baidu_ocr"] = {
            "status": "configured",
            "detail": "Baidu OCR credentials are configured"
        }
    else:
        external_services["baidu_ocr"] = {
            "status": "not_configured",
            "detail": "Baidu OCR credentials not configured"
        }
    
    # Check Aliyun OSS
    if settings.ALIYUN_OSS_ACCESS_KEY_ID and settings.ALIYUN_OSS_ACCESS_KEY_SECRET:
        external_services["aliyun_oss"] = {
            "status": "configured",
            "detail": "Aliyun OSS credentials are configured"
        }
    else:
        external_services["aliyun_oss"] = {
            "status": "not_configured",
            "detail": "Aliyun OSS credentials not configured"
        }
    
    health_status["checks"]["external_services"] = external_services
    
    # Determine overall status
    db_healthy = health_status["checks"].get("database", {}).get("status") == "healthy"
    if not db_healthy:
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/live")
async def liveness():
    """Simple liveness check - returns 200 if service is running."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness check - verifies critical dependencies are ready."""
    ready = True
    checks = {}
    
    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        checks["database"] = "ready"
    except Exception as e:
        ready = False
        checks["database"] = f"not_ready: {str(e)}"
    
    return {
        "ready": ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
