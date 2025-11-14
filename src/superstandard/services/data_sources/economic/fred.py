"""
FRED API Service for Economic Data

Production-grade integration with Federal Reserve Economic Data (FRED) API.
API Documentation: https://fred.stlouisfed.org/docs/api/

Provides:
- Macroeconomic indicators (GDP, CPI, unemployment, etc.)
- Time series data with historical observations
- Economic releases and series metadata
- Category browsing and search
- Real-time economic data updates

FRED is maintained by the Federal Reserve Bank of St. Louis and provides
access to 700,000+ economic time series from 100+ sources.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import aiohttp

from superstandard.services.base import BaseDataService, APIError, DataNotFoundError


class FREDService(BaseDataService):
    """
    FRED API service for comprehensive economic data.

    Features:
    - Economic time series retrieval (GDP, inflation, unemployment, etc.)
    - Historical observations with customizable date ranges
    - Series metadata (title, units, frequency, seasonal adjustment)
    - Category browsing for organized data discovery
    - Series search by keywords
    - Release calendar for upcoming data

    Authentication: API Key (query parameter)
    Rate Limits:
    - Free tier: 120 requests per minute (2 per second)
    - No daily limits for registered keys

    Caching Strategy:
    - Series metadata: 7 days (rarely changes)
    - Historical data: 24 hours (updates daily/weekly/monthly depending on series)
    - Latest observation: 1 hour (for real-time indicators)
    - Categories: 7 days (taxonomy is stable)

    Common Series IDs:
    - GDP: Real GDP (GDPC1)
    - Inflation: Consumer Price Index (CPIAUCSL)
    - Unemployment: Unemployment Rate (UNRATE)
    - Interest Rates: Federal Funds Rate (FEDFUNDS)
    - Consumer Confidence: University of Michigan Consumer Sentiment (UMCSENT)
    - Employment: Total Nonfarm Payroll (PAYEMS)
    - Housing: Housing Starts (HOUST)
    - Retail: Retail Sales (RSXFS)
    """

    # Pre-defined series IDs for common economic indicators
    COMMON_SERIES = {
        "gdp": "GDPC1",  # Real Gross Domestic Product
        "gdp_growth": "A191RL1Q225SBEA",  # Real GDP Growth Rate
        "cpi": "CPIAUCSL",  # Consumer Price Index for All Urban Consumers
        "core_cpi": "CPILFESL",  # CPI Less Food & Energy
        "inflation": "FPCPITOTLZGUSA",  # Inflation Rate (CPI)
        "unemployment": "UNRATE",  # Unemployment Rate
        "employment": "PAYEMS",  # Total Nonfarm Payroll Employment
        "fed_funds_rate": "FEDFUNDS",  # Federal Funds Effective Rate
        "10y_treasury": "DGS10",  # 10-Year Treasury Constant Maturity Rate
        "consumer_sentiment": "UMCSENT",  # University of Michigan Consumer Sentiment
        "housing_starts": "HOUST",  # Housing Starts
        "retail_sales": "RSXFS",  # Advance Retail Sales
        "industrial_production": "INDPRO",  # Industrial Production Index
        "capacity_utilization": "TCU",  # Capacity Utilization
        "ppi": "PPIACO",  # Producer Price Index
        "personal_income": "PI",  # Personal Income
        "personal_spending": "PCE",  # Personal Consumption Expenditures
        "ism_manufacturing": "NAPM",  # ISM Manufacturing PMI
    }

    def __init__(
        self,
        api_key: str,
        cache_service: Optional[Any] = None,
        rate_limit: int = 120
    ):
        """
        Initialize FRED service.

        Args:
            api_key: FRED API key (get free at https://fred.stlouisfed.org/docs/api/api_key.html)
            cache_service: Optional cache service instance
            rate_limit: Requests per minute (default: 120 for free tier)
        """
        super().__init__(
            cache_service=cache_service,
            rate_limit=rate_limit,
            retry_attempts=3,
            timeout=15
        )
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"

    async def get_series_observations(
        self,
        series_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        frequency: Optional[str] = None,
        aggregation_method: str = "avg"
    ) -> Dict[str, Any]:
        """
        Fetch time series observations for an economic indicator.

        Args:
            series_id: FRED series ID (e.g., "GDPC1", "UNRATE")
            start_date: Optional start date for observations
            end_date: Optional end date for observations
            frequency: Optional frequency (d=daily, w=weekly, m=monthly, q=quarterly, a=annual)
            aggregation_method: Method for aggregation (avg, sum, eop - end of period)

        Returns:
            Dictionary containing:
            - series_id: Series identifier
            - observations: List of {date, value} observations
            - units: Data units (e.g., "Billions of Dollars", "Percent")
            - frequency: Data frequency
            - last_updated: Last update timestamp

        Raises:
            APIError: If API request fails
            DataNotFoundError: If series not found
        """
        # Default to last 5 years if no dates provided
        if not start_date:
            start_date = datetime.now() - timedelta(days=5*365)
        if not end_date:
            end_date = datetime.now()

        # Check cache first
        cache_key = f"fred:observations:{series_id}:{start_date.date()}:{end_date.date()}:{frequency}"
        if cached := await self.get_cached(cache_key):
            return cached

        # Fetch from API with retry
        async def fetch():
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "observation_start": start_date.strftime("%Y-%m-%d"),
                "observation_end": end_date.strftime("%Y-%m-%d")
            }

            if frequency:
                params["frequency"] = frequency
                params["aggregation_method"] = aggregation_method

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/series/observations"

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        error_data = await response.json()
                        error_msg = error_data.get("error_message", "Bad request")
                        if "api_key" in error_msg.lower():
                            raise APIError("FRED API authentication failed - check API key")
                        elif "series" in error_msg.lower():
                            raise DataNotFoundError(f"Series not found: {series_id}")
                        else:
                            raise APIError(f"FRED API error: {error_msg}")
                    elif response.status == 429:
                        raise APIError("FRED API rate limit exceeded")
                    elif response.status == 500:
                        raise APIError("FRED API internal server error")
                    else:
                        error_text = await response.text()
                        raise APIError(f"FRED API error {response.status}: {error_text}")

        raw_data = await self.fetch_with_retry(fetch)

        # Transform to standardized format
        observations_data = self._transform_observations(raw_data, series_id)

        # Cache for 24 hours (economic data updates periodically)
        await self.cache(cache_key, observations_data, ttl=86400)

        return observations_data

    async def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """
        Fetch metadata for an economic series.

        Args:
            series_id: FRED series ID

        Returns:
            Series metadata including:
            - title: Series title
            - units: Data units
            - frequency: Update frequency
            - seasonal_adjustment: Seasonal adjustment status
            - last_updated: Last update date
            - notes: Series description

        Raises:
            DataNotFoundError: If series not found
        """
        # Check cache (7-day TTL for metadata)
        cache_key = f"fred:series_info:{series_id}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json"
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/series"

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        raise DataNotFoundError(f"Series not found: {series_id}")
                    else:
                        raise APIError(f"Failed to fetch series info: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        metadata = self._transform_series_info(raw_data)

        # Cache for 7 days
        await self.cache(cache_key, metadata, ttl=604800)

        return metadata

    async def get_multiple_series(
        self,
        series_ids: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple economic series in parallel.

        Args:
            series_ids: List of FRED series IDs
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary mapping series_id to observations data
        """
        tasks = [
            self.get_series_observations(series_id, start_date, end_date)
            for series_id in series_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        series_data = {}
        for series_id, result in zip(series_ids, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error fetching {series_id}: {str(result)}")
                series_data[series_id] = {"error": str(result)}
            else:
                series_data[series_id] = result

        return series_data

    async def get_common_indicators(
        self,
        indicators: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch common economic indicators by name.

        Args:
            indicators: List of indicator names (e.g., ["gdp", "unemployment", "inflation"])
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Dictionary mapping indicator name to observations data

        Example:
            >>> data = await fred.get_common_indicators(
            ...     ["gdp", "unemployment", "inflation"],
            ...     start_date=datetime(2020, 1, 1)
            ... )
            >>> print(data["gdp"]["latest_value"])
            25462.7  # Billions of dollars
        """
        # Map indicator names to series IDs
        series_ids = []
        indicator_map = {}

        for indicator in indicators:
            if indicator.lower() in self.COMMON_SERIES:
                series_id = self.COMMON_SERIES[indicator.lower()]
                series_ids.append(series_id)
                indicator_map[series_id] = indicator
            else:
                self.logger.warning(f"Unknown indicator: {indicator}")

        # Fetch all series
        series_data = await self.get_multiple_series(series_ids, start_date, end_date)

        # Remap to indicator names
        indicator_data = {}
        for series_id, data in series_data.items():
            indicator_name = indicator_map.get(series_id, series_id)
            indicator_data[indicator_name] = data

        return indicator_data

    async def search_series(
        self,
        search_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for economic series by keywords.

        Args:
            search_text: Search query
            limit: Maximum number of results

        Returns:
            List of series matching search criteria
        """
        cache_key = f"fred:search:{search_text}:{limit}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            params = {
                "search_text": search_text,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": limit
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/series/search"

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise APIError(f"Failed to search series: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        search_results = self._transform_search_results(raw_data)

        # Cache for 7 days
        await self.cache(cache_key, search_results, ttl=604800)

        return search_results

    async def get_latest_observation(self, series_id: str) -> Dict[str, Any]:
        """
        Get the most recent observation for a series.

        Args:
            series_id: FRED series ID

        Returns:
            Latest observation with date and value
        """
        # Cache for 1 hour (for real-time updates)
        cache_key = f"fred:latest:{series_id}"
        if cached := await self.get_cached(cache_key):
            return cached

        # Fetch last 1 observation
        async def fetch():
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "limit": 1,
                "sort_order": "desc"  # Most recent first
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/series/observations"

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise APIError(f"Failed to fetch latest observation: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)

        if raw_data.get("observations"):
            obs = raw_data["observations"][0]
            latest = {
                "series_id": series_id,
                "date": obs["date"],
                "value": float(obs["value"]) if obs["value"] != "." else None,
                "data_source": "FRED"
            }
        else:
            latest = {
                "series_id": series_id,
                "date": None,
                "value": None,
                "data_source": "FRED"
            }

        # Cache for 1 hour
        await self.cache(cache_key, latest, ttl=3600)

        return latest

    # Transform methods to standardize API responses

    def _transform_observations(self, raw_data: Dict[str, Any], series_id: str) -> Dict[str, Any]:
        """Transform raw FRED observations to standardized format."""
        observations = raw_data.get("observations", [])

        # Parse observations, filtering out missing values
        parsed_observations = []
        for obs in observations:
            if obs["value"] != ".":  # FRED uses "." for missing values
                parsed_observations.append({
                    "date": obs["date"],
                    "value": float(obs["value"])
                })

        # Calculate statistics
        values = [obs["value"] for obs in parsed_observations]
        latest_value = values[-1] if values else None
        avg_value = sum(values) / len(values) if values else None

        # Calculate simple growth rate (latest vs first)
        growth_rate = None
        if len(values) >= 2 and values[0] != 0:
            growth_rate = ((values[-1] - values[0]) / values[0]) * 100

        return {
            "series_id": series_id,
            "observation_count": len(parsed_observations),
            "observations": parsed_observations,
            "latest_value": latest_value,
            "latest_date": parsed_observations[-1]["date"] if parsed_observations else None,
            "average_value": round(avg_value, 2) if avg_value else None,
            "growth_rate_percent": round(growth_rate, 2) if growth_rate else None,
            "data_source": "FRED",
            "fetched_at": datetime.utcnow().isoformat()
        }

    def _transform_series_info(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform series metadata to standardized format."""
        series_list = raw_data.get("seriess", [])
        if not series_list:
            return {}

        series = series_list[0]

        return {
            "series_id": series.get("id"),
            "title": series.get("title"),
            "units": series.get("units"),
            "units_short": series.get("units_short"),
            "frequency": series.get("frequency"),
            "frequency_short": series.get("frequency_short"),
            "seasonal_adjustment": series.get("seasonal_adjustment"),
            "seasonal_adjustment_short": series.get("seasonal_adjustment_short"),
            "last_updated": series.get("last_updated"),
            "observation_start": series.get("observation_start"),
            "observation_end": series.get("observation_end"),
            "popularity": series.get("popularity"),
            "notes": series.get("notes"),
            "data_source": "FRED"
        }

    def _transform_search_results(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform search results to standardized format."""
        series_list = raw_data.get("seriess", [])

        return [
            {
                "series_id": series.get("id"),
                "title": series.get("title"),
                "units": series.get("units_short"),
                "frequency": series.get("frequency_short"),
                "seasonal_adjustment": series.get("seasonal_adjustment_short"),
                "popularity": series.get("popularity"),
                "last_updated": series.get("last_updated")
            }
            for series in series_list
        ]


__all__ = ['FREDService']
