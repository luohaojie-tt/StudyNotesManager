"""Redis caching service for mindmap generation results."""
import hashlib
import json
from typing import Optional

from loguru import logger
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings


class CacheService:
    """Redis-based caching service for expensive operations."""

    def __init__(self):
        """Initialize Redis client."""
        self.redis: Optional[Redis] = None
        self._enabled = None

    async def _get_redis(self) -> Optional[Redis]:
        """Get or create Redis connection."""
        if not await self.is_enabled():
            return None
        
        if self.redis is None:
            try:
                self.redis = Redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
                # Test connection
                await self.redis.ping()
                logger.info("Redis cache service connected successfully")
            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis: {e}. Caching disabled.",
                    extra={"action": "redis_connection_failed"}
                )
                self.redis = None
        
        return self.redis

    async def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        if self._enabled is None:
            # Try to connect to Redis to check if it's available
            try:
                test_redis = Redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await test_redis.ping()
                await test_redis.close()
                self._enabled = True
            except Exception:
                logger.debug("Redis not available, caching disabled")
                self._enabled = False
        
        return self._enabled

    def _generate_cache_key(
        self,
        prefix: str,
        note_content: str,
        max_levels: int,
        **kwargs
    ) -> str:
        """Generate a cache key from input parameters."""
        # Create a hash of the note content
        content_hash = hashlib.sha256(note_content.encode()).hexdigest()[:16]
        
        # Include max_levels and other parameters
        params = f"{max_levels}"
        if kwargs:
            sorted_params = sorted(kwargs.items())
            params += "_" + "_".join(f"{k}={v}" for k, v in sorted_params)
        
        return f"{prefix}:{content_hash}:{params}"

    async def get_cached_mindmap(
        self,
        note_content: str,
        max_levels: int
    ) -> Optional[dict]:
        """Get cached mindmap structure if available."""
        if not await self.is_enabled():
            return None
        
        try:
            redis = await self._get_redis()
            if not redis:
                return None
            
            cache_key = self._generate_cache_key(
                "mindmap",
                note_content,
                max_levels
            )
            
            cached_data = await redis.get(cache_key)
            if cached_data:
                logger.info(
                    "Mindmap cache hit",
                    extra={
                        "cache_key": cache_key,
                        "action": "mindmap_cache_hit"
                    }
                )
                return json.loads(cached_data)
            else:
                logger.debug(
                    "Mindmap cache miss",
                    extra={
                        "cache_key": cache_key,
                        "action": "mindmap_cache_miss"
                    }
                )
                return None
        except RedisError as e:
            logger.error(
                f"Redis error during cache retrieval: {e}",
                extra={"action": "cache_retrieval_error"}
            )
            return None

    async def cache_mindmap(
        self,
        note_content: str,
        max_levels: int,
        mindmap_structure: dict,
        ttl: int = 86400  # 24 hours default
    ) -> bool:
        """Cache a generated mindmap structure."""
        if not await self.is_enabled():
            return False
        
        try:
            redis = await self._get_redis()
            if not redis:
                return False
            
            cache_key = self._generate_cache_key(
                "mindmap",
                note_content,
                max_levels
            )
            
            await redis.setex(
                cache_key,
                ttl,
                json.dumps(mindmap_structure)
            )
            
            logger.info(
                "Mindmap cached successfully",
                extra={
                    "cache_key": cache_key,
                    "ttl": ttl,
                    "action": "mindmap_cached"
                }
            )
            return True
        except RedisError as e:
            logger.error(
                f"Redis error during cache storage: {e}",
                extra={"action": "cache_storage_error"}
            )
            return False

    async def invalidate_mindmap_cache(
        self,
        note_content: str
    ) -> bool:
        """Invalidate cached mindmaps for a note (e.g., after update)."""
        if not await self.is_enabled():
            return False
        
        try:
            redis = await self._get_redis()
            if not redis:
                return False
            
            # Delete all cache entries for this note content
            content_hash = hashlib.sha256(note_content.encode()).hexdigest()[:16]
            pattern = f"mindmap:{content_hash}:*"
            
            keys = await redis.keys(pattern)
            if keys:
                await redis.delete(*keys)
                logger.info(
                    f"Invalidated {len(keys)} mindmap cache entries",
                    extra={
                        "keys_deleted": len(keys),
                        "action": "mindmap_cache_invalidated"
                    }
                )
            
            return True
        except RedisError as e:
            logger.error(
                f"Redis error during cache invalidation: {e}",
                extra={"action": "cache_invalidation_error"}
            )
            return False

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.debug("Redis cache service connection closed")


# Global cache service instance
cache_service = CacheService()
