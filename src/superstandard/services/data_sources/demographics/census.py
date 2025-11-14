"""
US Census Bureau API Service for Demographics Data

Production-grade integration with US Census Bureau Data API.
API Documentation: https://www.census.gov/data/developers/data-sets.html

Provides:
- Population estimates and projections
- Age and sex distribution
- Race and ethnicity demographics
- Income and poverty statistics
- Educational attainment data
- Employment and workforce metrics
- Housing characteristics
- Migration patterns

The Census Bureau provides comprehensive demographic data for the United States
through multiple survey programs including Decennial Census, American Community
Survey (ACS), Current Population Survey (CPS), and more.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import aiohttp

from superstandard.services.base import BaseDataService, APIError, DataNotFoundError


class CensusService(BaseDataService):
    """
    US Census Bureau API service for comprehensive demographics data.

    Features:
    - Population estimates by geography (national, state, county, metro)
    - Age distribution and median age statistics
    - Race and ethnicity composition
    - Income distribution and median household income
    - Educational attainment levels
    - Employment and labor force statistics
    - Poverty rates and thresholds
    - Housing units and homeownership rates

    Authentication: API Key (optional but recommended for higher rate limits)
    Rate Limits:
    - Without key: 500 requests per IP per day
    - With key: 10,000 requests per IP per day

    Caching Strategy:
    - Population estimates: 30 days (updated annually)
    - ACS 5-year data: 180 days (very stable)
    - ACS 1-year data: 7 days (updated annually)
    - Current Population Survey: 1 day (monthly updates)

    Common Datasets:
    - acs/acs5: American Community Survey 5-Year estimates (most reliable)
    - acs/acs1: American Community Survey 1-Year estimates (most current)
    - pep/population: Population Estimates Program
    - cps/basic: Current Population Survey
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_service: Optional[Any] = None,
        rate_limit: int = 500  # Conservative default
    ):
        """
        Initialize Census Bureau service.

        Args:
            api_key: Optional Census API key (get free at https://api.census.gov/data/key_signup.html)
            cache_service: Optional cache service instance
            rate_limit: Requests per day (default: 500 without key, 10000 with key)
        """
        super().__init__(
            cache_service=cache_service,
            rate_limit=rate_limit,
            retry_attempts=3,
            timeout=20
        )
        self.api_key = api_key
        self.base_url = "https://api.census.gov/data"

    async def get_population_estimates(
        self,
        geography: str = "us",
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch population estimates for specified geography.

        Args:
            geography: Geographic level ("us", "state", "county", or FIPS code)
            year: Year for estimates (default: most recent)

        Returns:
            Population data including:
            - total_population: Total population count
            - year: Data year
            - growth_rate: YoY growth rate if available
            - density: Population density if available

        Raises:
            APIError: If API request fails
            DataNotFoundError: If geography not found
        """
        if not year:
            year = datetime.now().year - 1  # Most recent complete year

        # Check cache
        cache_key = f"census:population:{geography}:{year}"
        if cached := await self.get_cached(cache_key):
            return cached

        # Fetch from API
        async def fetch():
            params = {
                "get": "NAME,POP",
                "for": geography if geography != "us" else "us:*"
            }
            if self.api_key:
                params["key"] = self.api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{year}/pep/population"

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 400:
                        raise DataNotFoundError(f"Invalid geography or year: {geography}, {year}")
                    elif response.status == 404:
                        raise DataNotFoundError(f"Data not found for {geography} in {year}")
                    elif response.status == 429:
                        raise APIError("Census API rate limit exceeded")
                    else:
                        error_text = await response.text()
                        raise APIError(f"Census API error {response.status}: {error_text}")

        raw_data = await self.fetch_with_retry(fetch)
        population_data = self._transform_population_estimates(raw_data, geography, year)

        # Cache for 30 days (annual updates)
        await self.cache(cache_key, population_data, ttl=2592000)

        return population_data

    async def get_age_distribution(
        self,
        geography: str = "us",
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch age distribution data from American Community Survey.

        Args:
            geography: Geographic level
            year: ACS year (default: most recent 5-year estimate)

        Returns:
            Age distribution data including:
            - median_age: Median age
            - age_groups: Population by age cohort
            - dependency_ratio: Age dependency ratio
        """
        if not year:
            year = datetime.now().year - 2  # ACS data lags by ~2 years

        cache_key = f"census:age_distribution:{geography}:{year}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            # Fetch median age and age groups
            params = {
                "get": "NAME,B01002_001E,B01001_003E,B01001_027E",  # Median age, male 20-24, female 20-24
                "for": geography if geography != "us" else "us:*"
            }
            if self.api_key:
                params["key"] = self.api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{year}/acs/acs5"

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        # Fallback to older year if current year not available
                        url_fallback = f"{self.base_url}/{year-1}/acs/acs5"
                        async with session.get(url_fallback, params=params) as resp2:
                            if resp2.status == 200:
                                return await resp2.json()
                    raise APIError(f"Failed to fetch age data: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        age_data = self._transform_age_distribution(raw_data, geography, year)

        # Cache for 180 days (ACS 5-year is very stable)
        await self.cache(cache_key, age_data, ttl=15552000)

        return age_data

    async def get_income_statistics(
        self,
        geography: str = "us",
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch income and poverty statistics from ACS.

        Args:
            geography: Geographic level
            year: ACS year

        Returns:
            Income statistics including:
            - median_household_income: Median household income
            - per_capita_income: Per capita income
            - poverty_rate: Percentage below poverty line
            - gini_index: Income inequality measure
        """
        if not year:
            year = datetime.now().year - 2

        cache_key = f"census:income:{geography}:{year}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            # B19013_001E = Median Household Income
            # B19301_001E = Per Capita Income
            # B17001_002E = Income below poverty level
            params = {
                "get": "NAME,B19013_001E,B19301_001E,B17001_002E",
                "for": geography if geography != "us" else "us:*"
            }
            if self.api_key:
                params["key"] = self.api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{year}/acs/acs5"

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise APIError(f"Failed to fetch income data: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        income_data = self._transform_income_statistics(raw_data, geography, year)

        # Cache for 180 days
        await self.cache(cache_key, income_data, ttl=15552000)

        return income_data

    async def get_education_statistics(
        self,
        geography: str = "us",
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch educational attainment statistics from ACS.

        Args:
            geography: Geographic level
            year: ACS year

        Returns:
            Education statistics including:
            - high_school_or_higher: % with high school diploma or higher
            - bachelor_or_higher: % with bachelor's degree or higher
            - graduate_degree: % with graduate/professional degree
        """
        if not year:
            year = datetime.now().year - 2

        cache_key = f"census:education:{geography}:{year}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            # B15003_017E = High school graduate
            # B15003_022E = Bachelor's degree
            # B15003_023E = Master's degree
            params = {
                "get": "NAME,B15003_001E,B15003_017E,B15003_022E",
                "for": geography if geography != "us" else "us:*"
            }
            if self.api_key:
                params["key"] = self.api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{year}/acs/acs5"

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise APIError(f"Failed to fetch education data: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        education_data = self._transform_education_statistics(raw_data, geography, year)

        # Cache for 180 days
        await self.cache(cache_key, education_data, ttl=15552000)

        return education_data

    async def get_employment_statistics(
        self,
        geography: str = "us",
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch employment and labor force statistics from ACS.

        Args:
            geography: Geographic level
            year: ACS year

        Returns:
            Employment statistics including:
            - labor_force_participation: Labor force participation rate
            - unemployment_rate: Unemployment rate
            - employment_by_industry: Employment distribution
        """
        if not year:
            year = datetime.now().year - 2

        cache_key = f"census:employment:{geography}:{year}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            # B23025_002E = In labor force
            # B23025_005E = Unemployed
            params = {
                "get": "NAME,B23025_001E,B23025_002E,B23025_005E",
                "for": geography if geography != "us" else "us:*"
            }
            if self.api_key:
                params["key"] = self.api_key

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{year}/acs/acs5"

                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise APIError(f"Failed to fetch employment data: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        employment_data = self._transform_employment_statistics(raw_data, geography, year)

        # Cache for 180 days
        await self.cache(cache_key, employment_data, ttl=15552000)

        return employment_data

    async def get_comprehensive_demographics(
        self,
        geography: str = "us",
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive demographics profile (all categories in parallel).

        Args:
            geography: Geographic level
            year: Year for estimates

        Returns:
            Comprehensive demographics including population, age, income, education, employment
        """
        # Fetch all demographics in parallel
        tasks = [
            self.get_population_estimates(geography, year),
            self.get_age_distribution(geography, year),
            self.get_income_statistics(geography, year),
            self.get_education_statistics(geography, year),
            self.get_employment_statistics(geography, year)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        demographics = {
            "geography": geography,
            "year": year or (datetime.now().year - 1),
            "data_source": "US Census Bureau"
        }

        categories = ["population", "age", "income", "education", "employment"]
        for category, result in zip(categories, results):
            if isinstance(result, Exception):
                self.logger.error(f"Error fetching {category}: {str(result)}")
                demographics[category] = {"error": str(result)}
            else:
                demographics[category] = result

        return demographics

    # Transform methods to standardize API responses

    def _transform_population_estimates(
        self,
        raw_data: List[List[str]],
        geography: str,
        year: int
    ) -> Dict[str, Any]:
        """Transform population estimates to standardized format."""
        if len(raw_data) < 2:
            return {"error": "No data returned"}

        # Census API returns [headers, data_row]
        headers = raw_data[0]
        data_row = raw_data[1]

        # Find population column
        pop_idx = headers.index("POP") if "POP" in headers else 1

        population = int(data_row[pop_idx]) if len(data_row) > pop_idx else 0

        return {
            "geography": geography,
            "total_population": population,
            "year": year,
            "data_source": "Census Population Estimates Program",
            "fetched_at": datetime.utcnow().isoformat()
        }

    def _transform_age_distribution(
        self,
        raw_data: List[List[str]],
        geography: str,
        year: int
    ) -> Dict[str, Any]:
        """Transform age distribution to standardized format."""
        if len(raw_data) < 2:
            return {"error": "No data returned"}

        headers = raw_data[0]
        data_row = raw_data[1]

        # Extract median age (B01002_001E)
        median_age_idx = 1  # Usually second column after NAME
        median_age = float(data_row[median_age_idx]) if len(data_row) > median_age_idx else None

        return {
            "geography": geography,
            "median_age": median_age,
            "year": year,
            "data_source": "American Community Survey 5-Year",
            "fetched_at": datetime.utcnow().isoformat()
        }

    def _transform_income_statistics(
        self,
        raw_data: List[List[str]],
        geography: str,
        year: int
    ) -> Dict[str, Any]:
        """Transform income statistics to standardized format."""
        if len(raw_data) < 2:
            return {"error": "No data returned"}

        headers = raw_data[0]
        data_row = raw_data[1]

        # B19013_001E = Median Household Income (usually index 1)
        # B19301_001E = Per Capita Income (usually index 2)
        median_income = int(data_row[1]) if len(data_row) > 1 and data_row[1] != "-666666666" else None
        per_capita_income = int(data_row[2]) if len(data_row) > 2 and data_row[2] != "-666666666" else None

        return {
            "geography": geography,
            "median_household_income": median_income,
            "per_capita_income": per_capita_income,
            "year": year,
            "data_source": "American Community Survey 5-Year",
            "fetched_at": datetime.utcnow().isoformat()
        }

    def _transform_education_statistics(
        self,
        raw_data: List[List[str]],
        geography: str,
        year: int
    ) -> Dict[str, Any]:
        """Transform education statistics to standardized format."""
        if len(raw_data) < 2:
            return {"error": "No data returned"}

        headers = raw_data[0]
        data_row = raw_data[1]

        # Calculate percentages from counts
        total_pop = int(data_row[1]) if len(data_row) > 1 else 1
        high_school = int(data_row[2]) if len(data_row) > 2 else 0
        bachelor = int(data_row[3]) if len(data_row) > 3 else 0

        return {
            "geography": geography,
            "high_school_or_higher_percent": round((high_school / total_pop * 100), 1) if total_pop > 0 else None,
            "bachelor_or_higher_percent": round((bachelor / total_pop * 100), 1) if total_pop > 0 else None,
            "year": year,
            "data_source": "American Community Survey 5-Year",
            "fetched_at": datetime.utcnow().isoformat()
        }

    def _transform_employment_statistics(
        self,
        raw_data: List[List[str]],
        geography: str,
        year: int
    ) -> Dict[str, Any]:
        """Transform employment statistics to standardized format."""
        if len(raw_data) < 2:
            return {"error": "No data returned"}

        headers = raw_data[0]
        data_row = raw_data[1]

        # Calculate rates
        pop_16_over = int(data_row[1]) if len(data_row) > 1 else 1
        in_labor_force = int(data_row[2]) if len(data_row) > 2 else 0
        unemployed = int(data_row[3]) if len(data_row) > 3 else 0

        labor_force_rate = round((in_labor_force / pop_16_over * 100), 1) if pop_16_over > 0 else None
        unemployment_rate = round((unemployed / in_labor_force * 100), 1) if in_labor_force > 0 else None

        return {
            "geography": geography,
            "labor_force_participation_rate": labor_force_rate,
            "unemployment_rate": unemployment_rate,
            "year": year,
            "data_source": "American Community Survey 5-Year",
            "fetched_at": datetime.utcnow().isoformat()
        }


__all__ = ['CensusService']
