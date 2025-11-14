"""
Qualtrics API Service for Market Research Data

Production-grade integration with Qualtrics Experience Management Platform.
API Documentation: https://api.qualtrics.com/

Provides:
- Survey response data (quantitative metrics)
- Text analytics and sentiment analysis (qualitative insights)
- Cross-tabulation analysis
- Demographics and sample statistics
- Response quality metrics
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import aiohttp

from superstandard.services.base import BaseDataService, APIError, DataNotFoundError


class QualtricsService(BaseDataService):
    """
    Qualtrics API service for comprehensive market research data.

    Features:
    - Survey response collection with filtering
    - Real-time response statistics
    - Advanced text analytics and sentiment scoring
    - Cross-tabulation analysis by demographics
    - Response quality assessment (completion rate, time spent)
    - Multi-language support

    Authentication: API Token (X-API-TOKEN header)
    Rate Limits:
    - 60 requests per minute (standard tier)
    - 200 requests per minute (enterprise tier)

    Caching Strategy:
    - Survey metadata: 24 hours (surveys don't change frequently)
    - Response data: 1 hour (responses come in continuously)
    - Analytics: 6 hours (derived data, expensive to compute)
    """

    def __init__(
        self,
        api_token: str,
        datacenter: str = "iad1",  # Default US datacenter
        cache_service: Optional[Any] = None,
        rate_limit: int = 60
    ):
        """
        Initialize Qualtrics service.

        Args:
            api_token: Qualtrics API token
            datacenter: Qualtrics datacenter ID (e.g., 'iad1', 'fra1', 'syd1')
            cache_service: Optional cache service instance
            rate_limit: Requests per minute (default: 60)
        """
        super().__init__(
            cache_service=cache_service,
            rate_limit=rate_limit,
            retry_attempts=3,
            timeout=30
        )
        self.api_token = api_token
        self.datacenter = datacenter
        self.base_url = f"https://{datacenter}.qualtrics.com/API/v3"

    async def get_survey_responses(
        self,
        survey_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Fetch survey responses with optional date filtering.

        Args:
            survey_id: Qualtrics survey ID (format: SV_xxxxxxxxx)
            start_date: Optional start date for response filtering
            end_date: Optional end date for response filtering
            limit: Maximum number of responses to fetch (default: 1000)

        Returns:
            Dictionary containing:
            - responses: List of survey responses with answers
            - metadata: Survey metadata (name, creation date, status)
            - statistics: Response statistics (count, completion rate, avg time)

        Raises:
            APIError: If API request fails
            DataNotFoundError: If survey not found
        """
        # Check cache first
        cache_key = f"qualtrics:responses:{survey_id}:{start_date}:{end_date}:{limit}"
        if cached := await self.get_cached(cache_key):
            return cached

        # Fetch from API with retry
        async def fetch():
            headers = {
                "X-API-TOKEN": self.api_token,
                "Content-Type": "application/json"
            }

            # Build parameters
            params = {
                "limit": limit,
                "format": "json"
            }

            if start_date:
                params["startDate"] = start_date.isoformat()
            if end_date:
                params["endDate"] = end_date.isoformat()

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/surveys/{survey_id}/export-responses"

                # Create export
                async with session.post(url, headers=headers, json=params) as response:
                    if response.status == 200:
                        export_data = await response.json()
                        progress_id = export_data["result"]["progressId"]

                        # Poll for completion
                        return await self._poll_export_completion(session, headers, survey_id, progress_id)
                    elif response.status == 401:
                        raise APIError("Qualtrics API authentication failed - check API token")
                    elif response.status == 403:
                        raise APIError("Qualtrics API access denied - check permissions")
                    elif response.status == 404:
                        raise DataNotFoundError(f"Survey not found: {survey_id}")
                    elif response.status == 429:
                        raise APIError("Qualtrics API rate limit exceeded")
                    elif response.status == 500:
                        raise APIError("Qualtrics API internal server error")
                    else:
                        error_text = await response.text()
                        raise APIError(f"Qualtrics API error {response.status}: {error_text}")

        raw_data = await self.fetch_with_retry(fetch)

        # Transform to standardized format
        responses_data = self._transform_responses(raw_data, survey_id)

        # Cache for 1 hour (responses are dynamic)
        await self.cache(cache_key, responses_data, ttl=3600)

        return responses_data

    async def _poll_export_completion(
        self,
        session: aiohttp.ClientSession,
        headers: Dict[str, str],
        survey_id: str,
        progress_id: str,
        max_attempts: int = 30
    ) -> Dict[str, Any]:
        """
        Poll for export completion and download results.

        Qualtrics exports are asynchronous - need to poll until complete.
        """
        check_url = f"{self.base_url}/surveys/{survey_id}/export-responses/{progress_id}"

        for attempt in range(max_attempts):
            await asyncio.sleep(2)  # Wait 2 seconds between checks

            async with session.get(check_url, headers=headers) as response:
                if response.status == 200:
                    progress_data = await response.json()
                    status = progress_data["result"]["status"]

                    if status == "complete":
                        file_id = progress_data["result"]["fileId"]

                        # Download the file
                        download_url = f"{self.base_url}/surveys/{survey_id}/export-responses/{file_id}/file"
                        async with session.get(download_url, headers=headers) as file_response:
                            if file_response.status == 200:
                                return await file_response.json()
                            else:
                                raise APIError(f"Failed to download export file: {file_response.status}")

                    elif status == "failed":
                        raise APIError("Qualtrics export failed")

                    # Status is still "inProgress", continue polling

        raise APIError("Qualtrics export timeout - took longer than 60 seconds")

    async def get_survey_metadata(self, survey_id: str) -> Dict[str, Any]:
        """
        Fetch survey metadata and structure.

        Args:
            survey_id: Qualtrics survey ID

        Returns:
            Survey metadata including name, questions, options, creation date
        """
        # Check cache first (24-hour TTL for metadata)
        cache_key = f"qualtrics:metadata:{survey_id}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            headers = {
                "X-API-TOKEN": self.api_token,
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/surveys/{survey_id}"

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise DataNotFoundError(f"Survey not found: {survey_id}")
                    else:
                        raise APIError(f"Failed to fetch survey metadata: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        metadata = self._transform_survey_metadata(raw_data)

        # Cache for 24 hours
        await self.cache(cache_key, metadata, ttl=86400)

        return metadata

    async def get_text_analytics(
        self,
        survey_id: str,
        question_id: str
    ) -> Dict[str, Any]:
        """
        Get text analytics and sentiment analysis for open-ended questions.

        Args:
            survey_id: Qualtrics survey ID
            question_id: Question ID for text analysis

        Returns:
            Text analytics including:
            - Sentiment scores (positive, negative, neutral)
            - Top themes and topics
            - Word frequency
            - Representative quotes
        """
        # Check cache (6-hour TTL for analytics)
        cache_key = f"qualtrics:text_analytics:{survey_id}:{question_id}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            headers = {
                "X-API-TOKEN": self.api_token,
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/surveys/{survey_id}/questions/{question_id}/text-analytics"

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        # Text analytics not available - return empty structure
                        return {"result": {"sentiment": {}, "topics": []}}
                    else:
                        raise APIError(f"Failed to fetch text analytics: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        analytics = self._transform_text_analytics(raw_data)

        # Cache for 6 hours
        await self.cache(cache_key, analytics, ttl=21600)

        return analytics

    async def get_cross_tabs(
        self,
        survey_id: str,
        question_ids: List[str],
        demographic_field: str
    ) -> Dict[str, Any]:
        """
        Get cross-tabulation analysis by demographics.

        Args:
            survey_id: Qualtrics survey ID
            question_ids: List of question IDs to cross-tabulate
            demographic_field: Demographic field for segmentation (e.g., 'age', 'industry')

        Returns:
            Cross-tabulation results showing response patterns by segment
        """
        cache_key = f"qualtrics:crosstabs:{survey_id}:{','.join(question_ids)}:{demographic_field}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            headers = {
                "X-API-TOKEN": self.api_token,
                "Content-Type": "application/json"
            }

            body = {
                "questionIds": question_ids,
                "segmentField": demographic_field
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/surveys/{survey_id}/cross-tabulation"

                async with session.post(url, headers=headers, json=body) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        # Cross-tabs may not be available in all Qualtrics tiers
                        return {"result": {"crosstabs": []}}

        raw_data = await self.fetch_with_retry(fetch)
        crosstabs = self._transform_crosstabs(raw_data)

        # Cache for 6 hours
        await self.cache(cache_key, crosstabs, ttl=21600)

        return crosstabs

    async def get_response_statistics(self, survey_id: str) -> Dict[str, Any]:
        """
        Get high-level response statistics for a survey.

        Args:
            survey_id: Qualtrics survey ID

        Returns:
            Statistics including:
            - Total responses
            - Completion rate
            - Average completion time
            - Response rate over time
        """
        cache_key = f"qualtrics:stats:{survey_id}"
        if cached := await self.get_cached(cache_key):
            return cached

        async def fetch():
            headers = {
                "X-API-TOKEN": self.api_token,
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/surveys/{survey_id}/response-counts"

                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        raise DataNotFoundError(f"Survey not found: {survey_id}")
                    else:
                        raise APIError(f"Failed to fetch response statistics: {response.status}")

        raw_data = await self.fetch_with_retry(fetch)
        stats = self._transform_response_statistics(raw_data)

        # Cache for 1 hour
        await self.cache(cache_key, stats, ttl=3600)

        return stats

    # Transform methods to standardize API responses

    def _transform_responses(self, raw_data: Dict[str, Any], survey_id: str) -> Dict[str, Any]:
        """Transform raw Qualtrics response data to standardized format."""
        responses = raw_data.get("responses", [])

        return {
            "survey_id": survey_id,
            "response_count": len(responses),
            "responses": responses,
            "data_source": "Qualtrics",
            "fetched_at": datetime.utcnow().isoformat()
        }

    def _transform_survey_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform survey metadata to standardized format."""
        result = raw_data.get("result", {})

        return {
            "survey_id": result.get("id"),
            "survey_name": result.get("name"),
            "status": result.get("isActive", False),
            "creation_date": result.get("creationDate"),
            "last_modified": result.get("lastModified"),
            "question_count": len(result.get("questions", [])),
            "questions": result.get("questions", []),
            "data_source": "Qualtrics"
        }

    def _transform_text_analytics(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform text analytics to standardized format."""
        result = raw_data.get("result", {})
        sentiment = result.get("sentiment", {})
        topics = result.get("topics", [])

        return {
            "sentiment": {
                "positive_percentage": sentiment.get("positive", 0),
                "negative_percentage": sentiment.get("negative", 0),
                "neutral_percentage": sentiment.get("neutral", 0),
                "mixed_percentage": sentiment.get("mixed", 0)
            },
            "themes": [
                {
                    "theme": topic.get("name"),
                    "frequency": topic.get("count"),
                    "score": topic.get("score")
                }
                for topic in topics[:10]  # Top 10 themes
            ],
            "data_source": "Qualtrics Text Analytics"
        }

    def _transform_crosstabs(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform cross-tabulation data to standardized format."""
        result = raw_data.get("result", {})
        crosstabs = result.get("crosstabs", [])

        return {
            "crosstabs": crosstabs,
            "segment_count": len(set([ct.get("segment") for ct in crosstabs])),
            "data_source": "Qualtrics Cross-Tabulation"
        }

    def _transform_response_statistics(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform response statistics to standardized format."""
        result = raw_data.get("result", {})

        return {
            "total_responses": result.get("auditable", 0),
            "completed_responses": result.get("generated", 0),
            "completion_rate": (
                round(result.get("generated", 0) / result.get("auditable", 1) * 100, 1)
                if result.get("auditable", 0) > 0 else 0
            ),
            "deleted_responses": result.get("deleted", 0),
            "data_source": "Qualtrics"
        }


__all__ = ['QualtricsService']
