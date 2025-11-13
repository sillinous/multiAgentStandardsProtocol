"""
Base Data Service

Abstract base class for all data services with common functionality:
- Retry logic with exponential backoff
- Error handling and fallback
- Caching interface
- Rate limiting interface
- Logging
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, TypeVar
from datetime import datetime

T = TypeVar('T')


class DataServiceError(Exception):
    """Base exception for data service errors"""
    pass


class APIError(DataServiceError):
    """API call failed"""
    pass


class DataQualityError(DataServiceError):
    """Data quality below threshold"""
    pass


class BaseDataService(ABC):
    """
    Base class for all data services.

    Provides common functionality:
    - Retry with exponential backoff
    - Error handling
    - Caching interface
    - Logging
    """

    def __init__(
        self,
        cache_service: Optional[Any] = None,
        rate_limiter: Optional[Any] = None,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 30.0
    ):
        self.cache_service = cache_service
        self.rate_limiter = rate_limiter
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)

    async def fetch_with_retry(
        self,
        fetch_func: Callable[[], T],
        retries: Optional[int] = None
    ) -> T:
        """
        Fetch data with exponential backoff retry.

        Args:
            fetch_func: Async function to call
            retries: Number of retry attempts (default: self.retry_attempts)

        Returns:
            Result from fetch_func

        Raises:
            APIError: If all retries exhausted
        """
        retries = retries or self.retry_attempts

        for attempt in range(retries):
            try:
                # Rate limiting if configured
                if self.rate_limiter:
                    await self.rate_limiter.acquire()

                # Execute fetch with timeout
                result = await asyncio.wait_for(
                    fetch_func(),
                    timeout=self.timeout
                )
                return result

            except asyncio.TimeoutError:
                if attempt == retries - 1:
                    self.logger.error(f"Timeout after {retries} attempts")
                    raise APIError(f"Request timeout after {retries} attempts")

                delay = self.retry_delay * (2 ** attempt)
                self.logger.warning(f"Timeout on attempt {attempt + 1}, retrying in {delay}s")
                await asyncio.sleep(delay)

            except Exception as e:
                if attempt == retries - 1:
                    self.logger.error(f"Failed after {retries} attempts: {e}")
                    raise APIError(f"Request failed after {retries} attempts: {str(e)}")

                delay = self.retry_delay * (2 ** attempt)
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)

        raise APIError("Retry loop completed without success")

    async def fetch_or_fallback(
        self,
        primary_func: Callable[[], T],
        fallback_func: Callable[[], T]
    ) -> T:
        """
        Try primary data source, fall back to secondary.

        Args:
            primary_func: Primary data source function
            fallback_func: Fallback function if primary fails

        Returns:
            Data from primary or fallback source
        """
        try:
            return await self.fetch_with_retry(primary_func)
        except Exception as e:
            self.logger.warning(f"Primary source failed, using fallback: {e}")
            return await fallback_func()

    async def get_cached(self, key: str) -> Optional[Any]:
        """
        Get data from cache if available.

        Args:
            key: Cache key

        Returns:
            Cached data or None
        """
        if not self.cache_service:
            return None

        try:
            return await self.cache_service.get(key)
        except Exception as e:
            self.logger.warning(f"Cache get failed: {e}")
            return None

    async def cache(self, key: str, value: Any, ttl: int = 3600):
        """
        Store data in cache.

        Args:
            key: Cache key
            value: Data to cache
            ttl: Time to live in seconds
        """
        if not self.cache_service:
            return

        try:
            await self.cache_service.set(key, value, ttl=ttl)
        except Exception as e:
            self.logger.warning(f"Cache set failed: {e}")

    def assess_data_quality(self, data: Any, metadata: Dict[str, Any]) -> float:
        """
        Assess data quality on 0-10 scale.

        Args:
            data: Data to assess
            metadata: Metadata about data (source, timestamp, etc.)

        Returns:
            Quality score 0-10
        """
        score = 10.0

        # Check data completeness
        if not data:
            return 0.0

        # Check data freshness (if timestamp provided)
        if "timestamp" in metadata:
            try:
                data_age = (datetime.utcnow() - metadata["timestamp"]).total_seconds()
                # Deduct points for old data (> 24 hours)
                if data_age > 86400:
                    days_old = data_age / 86400
                    score -= min(3.0, days_old * 0.5)
            except Exception:
                pass

        # Check data structure completeness
        if isinstance(data, (list, tuple)):
            if len(data) == 0:
                score -= 3.0
            elif hasattr(data[0], '__dict__'):
                # Check if objects have expected fields
                required_fields = metadata.get("required_fields", [])
                if required_fields:
                    missing_count = sum(
                        1 for field in required_fields
                        if not hasattr(data[0], field)
                    )
                    score -= min(2.0, missing_count * 0.5)

        elif isinstance(data, dict):
            required_fields = metadata.get("required_fields", [])
            if required_fields:
                missing_count = sum(
                    1 for field in required_fields
                    if field not in data
                )
                score -= min(2.0, missing_count * 0.5)

        # Source credibility (if provided)
        source_quality = metadata.get("source_quality", 1.0)  # 0-1 scale
        score *= source_quality

        return max(0.0, min(10.0, score))

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if service is healthy and accessible.

        Returns:
            True if service is healthy
        """
        pass


__all__ = ['BaseDataService', 'DataServiceError', 'APIError', 'DataQualityError']
