"""Rate limiting utility for API calls."""

import asyncio
import time
from collections import deque
from typing import Optional


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(
        self,
        rate: int,
        per: float = 60.0,
    ) -> None:
        """Initialize rate limiter.

        Args:
            rate: Number of requests allowed
            per: Time period in seconds (default: 60s = 1 minute)
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from rate limiter.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Raises:
            ValueError: If tokens requested exceeds rate
        """
        if tokens > self.rate:
            raise ValueError(f"Cannot acquire {tokens} tokens, rate is {self.rate}")

        async with self._lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current

            # Refill allowance based on time passed
            self.allowance += time_passed * (self.rate / self.per)

            # Don't exceed rate
            if self.allowance > self.rate:
                self.allowance = self.rate

            # Check if we have enough allowance
            if self.allowance < tokens:
                # Calculate wait time needed
                needed = tokens - self.allowance
                wait_time = needed * (self.per / self.rate)

                from loguru import logger
                logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")

                await asyncio.sleep(wait_time)

                # Refill after wait
                self.allowance = self.rate

            # Deduct tokens
            self.allowance -= tokens


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for API calls."""

    def __init__(
        self,
        max_requests: int,
        window_seconds: float = 60.0,
    ) -> None:
        """Initialize sliding window rate limiter.

        Args:
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds (default: 60s)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request.

        Blocks if rate limit is exceeded.
        """
        async with self._lock:
            current = time.time()

            # Remove requests outside the window
            while self.requests and self.requests[0] <= current - self.window_seconds:
                self.requests.popleft()

            # Check if we're at the limit
            if len(self.requests) >= self.max_requests:
                # Calculate wait time until oldest request expires
                oldest_request = self.requests[0]
                wait_time = self.window_seconds - (current - oldest_request)

                from loguru import logger
                logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")

                await asyncio.sleep(wait_time)

                # Clean up expired requests
                current = time.time()
                while self.requests and self.requests[0] <= current - self.window_seconds:
                    self.requests.popleft()

            # Add current request
            self.requests.append(current)


# Global rate limiters for different services
_deepseek_rate_limiter: Optional[RateLimiter] = None


def get_deepseek_rate_limiter() -> RateLimiter:
    """Get or create global DeepSeek rate limiter.

    Returns:
        RateLimiter instance
    """
    global _deepseek_rate_limiter
    if _deepseek_rate_limiter is None:
        # DeepSeek free tier: 200 requests per minute
        _deepseek_rate_limiter = RateLimiter(rate=150, per=60.0)
    return _deepseek_rate_limiter
