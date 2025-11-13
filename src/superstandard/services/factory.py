"""
Service Factory

Creates data service instances based on configuration.
Supports multiple providers per service type and environment-based selection.
"""

import logging
from typing import Dict, Any, Optional
from .base import BaseDataService


class ServiceFactory:
    """
    Factory for creating data service instances.

    Supports:
    - Multiple providers per service type
    - Environment-based configuration (dev/staging/prod)
    - Mock data fallback
    - Service caching and reuse
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        use_mock: bool = False,
        cache_service: Optional[Any] = None,
        rate_limiter: Optional[Any] = None
    ):
        self.config = config or {}
        self.use_mock = use_mock
        self.cache_service = cache_service
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(__name__)

        # Service instance cache
        self._service_cache: Dict[str, BaseDataService] = {}

    @classmethod
    def from_config_file(cls, config_path: str, **kwargs):
        """
        Create factory from YAML config file.

        Args:
            config_path: Path to config file
            **kwargs: Additional factory arguments

        Returns:
            ServiceFactory instance
        """
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        return cls(config=config, **kwargs)

    def get_competitive_intelligence_service(self) -> BaseDataService:
        """Get competitive intelligence service"""
        cache_key = "competitive_intelligence"

        if cache_key in self._service_cache:
            return self._service_cache[cache_key]

        if self.use_mock:
            from .data_sources.competitive.mock import MockCompetitiveService
            service = MockCompetitiveService(
                cache_service=self.cache_service,
                rate_limiter=self.rate_limiter
            )
        else:
            provider = self.config.get("data_sources", {}).get(
                "competitive_intelligence", {}
            ).get("provider", "similarweb")

            if provider == "similarweb":
                from .data_sources.competitive.similarweb import SimilarWebService
                api_key = self.config["data_sources"]["competitive_intelligence"]["api_key"]
                service = SimilarWebService(
                    api_key=api_key,
                    cache_service=self.cache_service,
                    rate_limiter=self.rate_limiter
                )
            elif provider == "owler":
                from .data_sources.competitive.owler import OwlerService
                api_key = self.config["data_sources"]["competitive_intelligence"]["api_key"]
                service = OwlerService(
                    api_key=api_key,
                    cache_service=self.cache_service,
                    rate_limiter=self.rate_limiter
                )
            else:
                raise ValueError(f"Unknown competitive intelligence provider: {provider}")

        self._service_cache[cache_key] = service
        return service

    def get_market_research_service(self) -> BaseDataService:
        """Get market research service"""
        cache_key = "market_research"

        if cache_key in self._service_cache:
            return self._service_cache[cache_key]

        if self.use_mock:
            from .data_sources.market_research.mock import MockMarketResearchService
            service = MockMarketResearchService(
                cache_service=self.cache_service,
                rate_limiter=self.rate_limiter
            )
        else:
            provider = self.config.get("data_sources", {}).get(
                "market_research", {}
            ).get("provider", "qualtrics")

            if provider == "qualtrics":
                from .data_sources.market_research.qualtrics import QualtricsService
                api_key = self.config["data_sources"]["market_research"]["api_key"]
                datacenter = self.config["data_sources"]["market_research"].get("datacenter", "us1")
                service = QualtricsService(
                    api_key=api_key,
                    datacenter=datacenter,
                    cache_service=self.cache_service,
                    rate_limiter=self.rate_limiter
                )
            else:
                raise ValueError(f"Unknown market research provider: {provider}")

        self._service_cache[cache_key] = service
        return service

    def get_economic_data_service(self) -> BaseDataService:
        """Get economic data service"""
        cache_key = "economic_data"

        if cache_key in self._service_cache:
            return self._service_cache[cache_key]

        if self.use_mock:
            from .data_sources.economic.mock import MockEconomicDataService
            service = MockEconomicDataService(
                cache_service=self.cache_service,
                rate_limiter=self.rate_limiter
            )
        else:
            provider = self.config.get("data_sources", {}).get(
                "economic_data", {}
            ).get("provider", "fred")

            if provider == "fred":
                from .data_sources.economic.fred import FREDService
                api_key = self.config["data_sources"]["economic_data"]["api_key"]
                service = FREDService(
                    api_key=api_key,
                    cache_service=self.cache_service,
                    rate_limiter=self.rate_limiter
                )
            else:
                raise ValueError(f"Unknown economic data provider: {provider}")

        self._service_cache[cache_key] = service
        return service

    def get_crm_service(self) -> BaseDataService:
        """Get CRM service"""
        cache_key = "crm"

        if cache_key in self._service_cache:
            return self._service_cache[cache_key]

        if self.use_mock:
            from .data_sources.crm.mock import MockCRMService
            service = MockCRMService(
                cache_service=self.cache_service,
                rate_limiter=self.rate_limiter
            )
        else:
            provider = self.config.get("data_sources", {}).get(
                "crm", {}
            ).get("provider", "salesforce")

            if provider == "salesforce":
                from .data_sources.crm.salesforce import SalesforceService
                credentials = self.config["data_sources"]["crm"]
                service = SalesforceService(
                    credentials=credentials,
                    cache_service=self.cache_service,
                    rate_limiter=self.rate_limiter
                )
            elif provider == "hubspot":
                from .data_sources.crm.hubspot import HubSpotService
                api_key = self.config["data_sources"]["crm"]["api_key"]
                service = HubSpotService(
                    api_key=api_key,
                    cache_service=self.cache_service,
                    rate_limiter=self.rate_limiter
                )
            else:
                raise ValueError(f"Unknown CRM provider: {provider}")

        self._service_cache[cache_key] = service
        return service

    def get_financial_planning_service(self) -> BaseDataService:
        """Get financial planning service"""
        cache_key = "financial_planning"

        if cache_key in self._service_cache:
            return self._service_cache[cache_key]

        if self.use_mock:
            from .data_sources.financial.mock import MockFinancialPlanningService
            service = MockFinancialPlanningService(
                cache_service=self.cache_service,
                rate_limiter=self.rate_limiter
            )
        else:
            provider = self.config.get("data_sources", {}).get(
                "financial_planning", {}
            ).get("provider", "anaplan")

            if provider == "anaplan":
                from .data_sources.financial.anaplan import AnaplanService
                credentials = self.config["data_sources"]["financial_planning"]
                service = AnaplanService(
                    credentials=credentials,
                    cache_service=self.cache_service,
                    rate_limiter=self.rate_limiter
                )
            else:
                raise ValueError(f"Unknown financial planning provider: {provider}")

        self._service_cache[cache_key] = service
        return service


__all__ = ['ServiceFactory']
