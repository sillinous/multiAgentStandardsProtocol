"""
SimilarWeb Competitive Intelligence Service

Production-ready service for fetching competitive intelligence data from SimilarWeb API.

API Documentation: https://api.similarweb.com/docs
"""

import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...base import BaseDataService, APIError


class SimilarWebService(BaseDataService):
    """
    SimilarWeb API service for competitive intelligence.

    Features:
    - Competitor identification and analysis
    - Traffic and engagement metrics
    - Market share data
    - Audience demographics
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.similarweb.com/v1",
        cache_service: Optional[Any] = None,
        rate_limiter: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(cache_service=cache_service, rate_limiter=rate_limiter, **kwargs)
        self.api_key = api_key
        self.base_url = base_url

    async def get_competitors(
        self,
        domain: str,
        limit: int = 10,
        country: str = "US"
    ) -> List[Dict[str, Any]]:
        """
        Get competitor list for a domain.

        Args:
            domain: Target domain (e.g., "example.com")
            limit: Maximum number of competitors to return
            country: Country code for localization (default: "US")

        Returns:
            List of competitor dictionaries with standardized format

        Raises:
            APIError: If API call fails
        """
        # Check cache first
        cache_key = f"similarweb:competitors:{domain}:{limit}:{country}"
        if cached := await self.get_cached(cache_key):
            self.logger.info(f"Cache hit for competitors: {domain}")
            return cached

        # Fetch from API
        async def fetch():
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/website/{domain}/competitors"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }
                params = {
                    "limit": limit,
                    "country": country
                }

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    elif response.status == 401:
                        raise APIError("SimilarWeb API authentication failed - check API key")
                    elif response.status == 403:
                        raise APIError("SimilarWeb API access forbidden - check permissions")
                    elif response.status == 429:
                        raise APIError("SimilarWeb API rate limit exceeded")
                    else:
                        error_text = await response.text()
                        raise APIError(f"SimilarWeb API error {response.status}: {error_text}")

        # Fetch with retry
        raw_data = await self.fetch_with_retry(fetch)

        # Transform to standard format
        competitors = self._transform_competitors(raw_data, domain)

        # Cache result (24 hour TTL)
        await self.cache(cache_key, competitors, ttl=86400)

        self.logger.info(f"Fetched {len(competitors)} competitors for {domain}")
        return competitors

    async def get_traffic_metrics(
        self,
        domain: str,
        start_date: str,
        end_date: str,
        country: str = "US"
    ) -> Dict[str, Any]:
        """
        Get traffic and engagement metrics for a domain.

        Args:
            domain: Target domain
            start_date: Start date (YYYY-MM)
            end_date: End date (YYYY-MM)
            country: Country code

        Returns:
            Dictionary with traffic metrics
        """
        cache_key = f"similarweb:traffic:{domain}:{start_date}:{end_date}:{country}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/website/{domain}/total-traffic-and-engagement/visits"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }
                params = {
                    "start_date": start_date,
                    "end_date": end_date,
                    "country": country,
                    "granularity": "monthly",
                    "main_domain_only": "false"
                }

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise APIError(f"SimilarWeb traffic API error: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        traffic_data = self._transform_traffic_metrics(raw_data)

        await self.cache(cache_key, traffic_data, ttl=3600)  # 1 hour TTL
        return traffic_data

    async def get_market_share(
        self,
        domain: str,
        category: str,
        country: str = "US"
    ) -> Dict[str, Any]:
        """
        Get market share data for a domain within its category.

        Args:
            domain: Target domain
            category: Industry category
            country: Country code

        Returns:
            Market share information
        """
        cache_key = f"similarweb:market_share:{domain}:{category}:{country}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/website/{domain}/category-rank/category-rank"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Accept": "application/json"
                }
                params = {
                    "country": country
                }

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise APIError(f"SimilarWeb market share API error: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        market_data = self._transform_market_share(raw_data)

        await self.cache(cache_key, market_data, ttl=86400)  # 24 hour TTL
        return market_data

    def _transform_competitors(
        self,
        raw_data: Dict[str, Any],
        source_domain: str
    ) -> List[Dict[str, Any]]:
        """
        Transform SimilarWeb competitor data to standard format.

        Args:
            raw_data: Raw API response
            source_domain: Source domain for context

        Returns:
            List of standardized competitor dictionaries
        """
        competitors_data = raw_data.get("data", {}).get("competitors", [])

        competitors = []
        for comp in competitors_data:
            competitor = {
                "name": comp.get("domain", "Unknown"),
                "domain": comp.get("domain", ""),
                "market_share": comp.get("share", 0.0),
                "monthly_visits": comp.get("visits", 0),
                "category": comp.get("category", "Unknown"),
                "rank": comp.get("rank", 0),
                "similarity_score": comp.get("similarity", 0.0),
                "source": "SimilarWeb",
                "fetched_at": datetime.utcnow().isoformat(),
                "source_domain": source_domain
            }
            competitors.append(competitor)

        return competitors

    def _transform_traffic_metrics(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform traffic metrics to standard format"""
        visits = raw_data.get("visits", [])

        return {
            "total_visits": sum(v.get("visits", 0) for v in visits),
            "average_monthly_visits": sum(v.get("visits", 0) for v in visits) / len(visits) if visits else 0,
            "monthly_data": [
                {
                    "date": v.get("date"),
                    "visits": v.get("visits", 0)
                }
                for v in visits
            ],
            "source": "SimilarWeb",
            "fetched_at": datetime.utcnow().isoformat()
        }

    def _transform_market_share(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform market share data to standard format"""
        return {
            "category": raw_data.get("category", "Unknown"),
            "rank": raw_data.get("rank", 0),
            "share": raw_data.get("share", 0.0),
            "source": "SimilarWeb",
            "fetched_at": datetime.utcnow().isoformat()
        }

    async def health_check(self) -> bool:
        """
        Check if SimilarWeb API is accessible.

        Returns:
            True if service is healthy
        """
        try:
            # Try a simple API call (e.g., checking a well-known domain)
            await self.get_competitors("example.com", limit=1)
            return True
        except Exception as e:
            self.logger.error(f"SimilarWeb health check failed: {e}")
            return False


__all__ = ['SimilarWebService']
