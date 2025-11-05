"""
Agent Library Client SDK

Provides a Python client for consuming the Agent Library Service.
Can be used both locally and remotely via HTTP.
"""

import httpx
import asyncio
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClientConfig:
    """Configuration for Agent Library Client"""
    base_url: str = "http://localhost:8000"
    timeout: float = 30.0
    verify_ssl: bool = True
    retries: int = 3


class AgentLibraryClient:
    """
    Client for accessing Agent Library Service via REST API.

    Provides methods for:
    - Discovering agents
    - Executing agents
    - Monitoring execution
    - Checking health
    - Managing agent registry

    Example:
        client = AgentLibraryClient("http://localhost:8000")

        # Discover agents
        agents = await client.discover_agents(apqc_process="3.0")

        # Execute an agent
        result = await client.execute_agent(
            "analyze_market_trends_sales_marketing",
            {"market": "automotive"}
        )

        # Check status
        status = await client.get_execution_status(result.execution_id)
    """

    def __init__(self, config: Optional[ClientConfig] = None):
        """
        Initialize the client.

        Args:
            config: Client configuration. If None, uses defaults.
        """
        self.config = config or ClientConfig()
        self.base_url = self.config.base_url.rstrip('/')
        self.client = None
        logger.info(f"Initialized Agent Library Client pointing to {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry"""
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()

    async def _ensure_client(self):
        """Ensure client is initialized"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )

    async def close(self):
        """Close the client connection"""
        if self.client:
            await self.client.aclose()

    # ========================================================================
    # Discovery Endpoints
    # ========================================================================

    async def discover_agents(
        self,
        apqc_process: Optional[str] = None,
        apqc_level: Optional[str] = None,
        capability: Optional[str] = None,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        min_proficiency: Optional[float] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Discover agents with flexible filtering.

        Args:
            apqc_process: Filter by APQC process (e.g., '3.0')
            apqc_level: Filter by APQC level
            capability: Filter by capability name
            keyword: Search by keyword in name/description
            status: Filter by status (draft, staging, production, deprecated)
            min_proficiency: Minimum proficiency level (0.0-1.0)
            skip: Number of results to skip (pagination)
            limit: Maximum number of results

        Returns:
            Dict with discovery results including total count and agent list
        """
        await self._ensure_client()

        payload = {
            "apqc_process": apqc_process,
            "apqc_level": apqc_level,
            "capability": capability,
            "keyword": keyword,
            "status": status,
            "min_proficiency": min_proficiency,
            "skip": skip,
            "limit": limit,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        logger.info(f"Discovering agents with filters: {payload}")
        response = await self.client.post("/api/v1/agents/discover", json=payload)
        response.raise_for_status()
        return response.json()

    async def search_agents(
        self,
        q: Optional[str] = None,
        apqc: Optional[str] = None,
        capability: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Quick search for agents.

        Args:
            q: Search query
            apqc: APQC process filter
            capability: Capability filter
            skip: Pagination offset
            limit: Result limit

        Returns:
            Search results
        """
        await self._ensure_client()

        params = {
            "q": q,
            "apqc": apqc,
            "capability": capability,
            "skip": skip,
            "limit": limit,
        }

        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        logger.info(f"Searching agents: {params}")
        response = await self.client.get("/api/v1/agents/search", params=params)
        response.raise_for_status()
        return response.json()

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific agent.

        Args:
            agent_id: The agent identifier

        Returns:
            Agent metadata and details
        """
        await self._ensure_client()

        logger.info(f"Fetching agent: {agent_id}")
        response = await self.client.get(f"/api/v1/agents/{agent_id}")
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Execution Endpoints
    # ========================================================================

    async def execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        timeout_ms: int = 30000,
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an agent.

        Args:
            agent_id: The agent to execute
            input_data: Input data for the agent
            timeout_ms: Execution timeout in milliseconds
            priority: Execution priority (1-10)
            metadata: Additional metadata

        Returns:
            Execution response with execution_id and status
        """
        await self._ensure_client()

        payload = {
            "agent_id": agent_id,
            "input_data": input_data,
            "timeout_ms": timeout_ms,
            "priority": priority,
            "metadata": metadata or {},
        }

        logger.info(f"Executing agent: {agent_id}")
        response = await self.client.post("/api/v1/agents/execute", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get the status of an execution.

        Args:
            execution_id: The execution identifier

        Returns:
            Execution status and results if complete
        """
        await self._ensure_client()

        logger.info(f"Checking execution status: {execution_id}")
        response = await self.client.get(f"/api/v1/agents/executions/{execution_id}")
        response.raise_for_status()
        return response.json()

    async def cancel_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        Cancel a running execution.

        Args:
            execution_id: The execution identifier

        Returns:
            Confirmation of cancellation
        """
        await self._ensure_client()

        logger.info(f"Cancelling execution: {execution_id}")
        response = await self.client.delete(f"/api/v1/agents/executions/{execution_id}")
        response.raise_for_status()
        return response.json()

    async def get_execution_history(
        self,
        agent_id: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get execution history for an agent.

        Args:
            agent_id: The agent identifier
            limit: Maximum history items to return

        Returns:
            Execution history for the agent
        """
        await self._ensure_client()

        params = {"limit": limit}
        logger.info(f"Fetching execution history for agent: {agent_id}")
        response = await self.client.get(
            f"/api/v1/agents/{agent_id}/history",
            params=params
        )
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Health & Monitoring Endpoints
    # ========================================================================

    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health status.

        Returns:
            System health metrics
        """
        await self._ensure_client()

        logger.info("Checking system health")
        response = await self.client.get("/api/v1/agents/health/system")
        response.raise_for_status()
        return response.json()

    async def get_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """
        Get health status for a specific agent.

        Args:
            agent_id: The agent identifier

        Returns:
            Agent health metrics
        """
        await self._ensure_client()

        logger.info(f"Checking health for agent: {agent_id}")
        response = await self.client.get(f"/api/v1/agents/{agent_id}/health")
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Registry Management Endpoints
    # ========================================================================

    async def register_agent(self, agent_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new agent in the library.

        Args:
            agent_metadata: Agent metadata including id, name, description, etc.

        Returns:
            Registered agent metadata
        """
        await self._ensure_client()

        logger.info(f"Registering agent: {agent_metadata.get('agent_id')}")
        response = await self.client.post(
            "/api/v1/agents/registry/register",
            json=agent_metadata
        )
        response.raise_for_status()
        return response.json()

    async def unregister_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Unregister an agent from the library.

        Args:
            agent_id: The agent identifier

        Returns:
            Confirmation of unregistration
        """
        await self._ensure_client()

        logger.info(f"Unregistering agent: {agent_id}")
        response = await self.client.delete(f"/api/v1/agents/{agent_id}/registry")
        response.raise_for_status()
        return response.json()

    async def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Registry statistics and metrics
        """
        await self._ensure_client()

        logger.info("Fetching registry statistics")
        response = await self.client.get("/api/v1/agents/registry/stats")
        response.raise_for_status()
        return response.json()

    # ========================================================================
    # Health Check
    # ========================================================================

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the service is running.

        Returns:
            Health check response
        """
        await self._ensure_client()

        logger.info("Performing health check")
        response = await self.client.get("/api/v1/agents/health")
        response.raise_for_status()
        return response.json()


# ============================================================================
# Convenience Functions
# ============================================================================

async def get_default_client() -> AgentLibraryClient:
    """
    Get a default client pointing to localhost.

    Returns:
        AgentLibraryClient instance
    """
    return AgentLibraryClient()


# ============================================================================
# Example Usage
# ============================================================================

async def example_usage():
    """Example of how to use the client"""
    config = ClientConfig(base_url="http://localhost:8000")

    async with AgentLibraryClient(config) as client:
        # Discover agents
        print("Discovering agents...")
        agents = await client.discover_agents(apqc_process="3.0", limit=5)
        print(f"Found {agents['total']} agents")

        # Get specific agent
        if agents['agents']:
            agent = agents['agents'][0]
            print(f"Agent: {agent['name']} ({agent['agent_id']})")

            # Execute the agent
            print("Executing agent...")
            result = await client.execute_agent(
                agent['agent_id'],
                {"test": "data"}
            )
            print(f"Execution started: {result['execution_id']}")

            # Check status
            status = await client.get_execution_status(result['execution_id'])
            print(f"Status: {status['status']}")

        # Check system health
        print("Checking system health...")
        health = await client.get_system_health()
        print(f"System status: {health['status']}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
