"""Unit tests for rate limiter utility."""
import asyncio
import time
import pytest

from app.utils.rate_limiter import RateLimiter, SlidingWindowRateLimiter, get_deepseek_rate_limiter


@pytest.mark.unit
class TestRateLimiter:
    """Test RateLimiter (token bucket) implementation."""

    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self):
        """Test basic rate limiting."""
        # Allow 5 requests per second
        limiter = RateLimiter(rate=5, per=1.0)

        # Should allow first 5 requests immediately
        start = time.time()
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.time() - start

        assert elapsed < 0.5  # Should complete quickly

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self):
        """Test that rate limit is enforced."""
        # Allow 2 requests per second
        limiter = RateLimiter(rate=2, per=1.0)

        start = time.time()

        # First 2 should be fast
        await limiter.acquire()
        await limiter.acquire()

        # Third request should trigger rate limit
        await limiter.acquire()

        elapsed = time.time() - start

        # Should take at least 0.5 seconds due to rate limiting
        assert elapsed >= 0.3

    @pytest.mark.asyncio
    async def test_token_replenishment(self):
        """Test that tokens replenish over time."""
        # Allow 2 requests per 0.1 seconds
        limiter = RateLimiter(rate=2, per=0.1)

        # Use all tokens
        await limiter.acquire()
        await limiter.acquire()

        # Wait for replenishment
        await asyncio.sleep(0.15)

        # Should have tokens available again
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should not wait

    @pytest.mark.asyncio
    async def test_multiple_tokens(self):
        """Test acquiring multiple tokens at once."""
        limiter = RateLimiter(rate=10, per=1.0)

        # Acquire 5 tokens at once
        await limiter.acquire(tokens=5)

        # Should have 5 remaining
        await limiter.acquire(tokens=5)

        # Next request should trigger rate limit
        start = time.time()
        await limiter.acquire(tokens=1)
        elapsed = time.time() - start

        assert elapsed >= 0.05  # Should wait

    @pytest.mark.asyncio
    async def test_acquire_too_many_tokens(self):
        """Test that requesting too many tokens raises error."""
        limiter = RateLimiter(rate=5, per=1.0)

        with pytest.raises(ValueError, match="Cannot acquire"):
            await limiter.acquire(tokens=10)


@pytest.mark.unit
class TestSlidingWindowRateLimiter:
    """Test SlidingWindowRateLimiter implementation."""

    @pytest.mark.asyncio
    async def test_basic_window(self):
        """Test basic sliding window behavior."""
        # Allow 3 requests per 0.1 seconds
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=0.1)

        # First 3 should be allowed
        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()

        # 4th should trigger rate limit
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        assert elapsed >= 0.05  # Should wait

    @pytest.mark.asyncio
    async def test_window_sliding(self):
        """Test that window slides over time."""
        # Allow 2 requests per 0.1 seconds
        limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=0.1)

        # Use up quota
        await limiter.acquire()
        await limiter.acquire()

        # Wait for window to slide
        await asyncio.sleep(0.15)

        # Should allow new requests
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        assert elapsed < 0.1  # Should not wait


@pytest.mark.unit
class TestGlobalRateLimiters:
    """Test global rate limiter instances."""

    def test_get_deepseek_rate_limiter_singleton(self):
        """Test that DeepSeek rate limiter is singleton."""
        limiter1 = get_deepseek_rate_limiter()
        limiter2 = get_deepseek_rate_limiter()

        assert limiter1 is limiter2  # Same instance

    def test_deepseek_rate_limiter_config(self):
        """Test DeepSeek rate limiter configuration."""
        limiter = get_deepseek_rate_limiter()

        # Should be configured for DeepSeek free tier
        assert limiter.rate == 150
        assert limiter.per == 60.0
