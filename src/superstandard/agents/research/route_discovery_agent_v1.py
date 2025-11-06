"""
Route Discovery Agent v1.0 - Architecturally Compliant
======================================================

AGENT METADATA:
--------------
Agent Type: route_discovery
Version: 1.0.0
Protocols: A2A, A2P, ACP, ANP, MCP
Capabilities: route_optimization, path_planning, alternative_routes, time_estimation

ARCHITECTURAL COMPLIANCE:
------------------------
✓ Standardized: Follows BaseAgent architecture with typed configuration
✓ Interoperable: Supports all 5 core protocols (A2A, A2P, ACP, ANP, MCP)
✓ Redeployable: Environment-based configuration, no hardcoded values
✓ Reusable: Clear interfaces, well-documented methods
✓ Atomic: Single responsibility - route discovery and optimization
✓ Composable: Can be combined with other agents in swarms
✓ Orchestratable: Async lifecycle methods for coordination
✓ Agnostic: No vendor/model/system dependencies

DOMAIN ALGORITHMS:
-----------------
- Nearest-neighbor route optimization
- 2-opt edge swap improvement
- Haversine distance calculation
- Efficiency scoring (straightness + stops penalty)
- Alternative route generation

USAGE:
------
    from library.agents.route_discovery_agent_v1 import (
        create_route_discovery_agent,
        RouteDiscoveryAgentConfig
    )

    # Create with environment configuration
    agent = await create_route_discovery_agent()

    # Or with custom configuration
    config = RouteDiscoveryAgentConfig(
        avg_speed_kmh=50.0,
        max_stops=15
    )
    agent = await create_route_discovery_agent(config=config)

    # Execute route optimization
    result = await agent.execute({
        "action": "calculate_route",
        "stops": [(lat1, lon1), (lat2, lon2), ...],
        "start_location": (start_lat, start_lon)
    })
"""

import os
import math
import time
import asyncio
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, field

# Resource monitoring
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Import base framework
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin

# Agent metadata
AGENT_TYPE = "route_discovery"
AGENT_VERSION = "1.0.0"
SUPPORTED_PROTOCOLS = ["A2A", "A2P", "ACP", "ANP", "MCP"]


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class RouteDiscoveryAgentConfig:
    """
    Configuration for Route Discovery Agent

    All parameters can be set via environment variables with prefix:
    ROUTE_DISCOVERY_*

    Example:
        export ROUTE_DISCOVERY_AVG_SPEED_KMH=50.0
        export ROUTE_DISCOVERY_MAX_STOPS=15
    """

    # Logging
    log_level: str = "INFO"

    # Resource limits
    max_memory_mb: int = 512
    max_cpu_percent: int = 80

    # Protocol flags
    enable_a2a: bool = True
    enable_a2p: bool = True
    enable_acp: bool = True
    enable_anp: bool = True
    enable_mcp: bool = True

    # Domain configuration
    avg_speed_kmh: float = 40.0
    cost_per_km: float = 1.5
    max_stops: int = 10

    # Optimization parameters
    enable_2opt: bool = True
    max_2opt_iterations: int = 100

    # Alternative routes
    default_num_alternatives: int = 3

    # Caching
    enable_cache: bool = True
    cache_ttl_seconds: int = 300

    # Performance
    enable_metrics: bool = True

    @classmethod
    def from_environment(cls) -> "RouteDiscoveryAgentConfig":
        """Create configuration from environment variables"""
        return cls(
            # Logging
            log_level=os.getenv("ROUTE_DISCOVERY_LOG_LEVEL", "INFO"),
            # Resource limits
            max_memory_mb=int(os.getenv("ROUTE_DISCOVERY_MAX_MEMORY_MB", "512")),
            max_cpu_percent=int(os.getenv("ROUTE_DISCOVERY_MAX_CPU_PERCENT", "80")),
            # Protocol flags
            enable_a2a=os.getenv("ROUTE_DISCOVERY_ENABLE_A2A", "true").lower() == "true",
            enable_a2p=os.getenv("ROUTE_DISCOVERY_ENABLE_A2P", "true").lower() == "true",
            enable_acp=os.getenv("ROUTE_DISCOVERY_ENABLE_ACP", "true").lower() == "true",
            enable_anp=os.getenv("ROUTE_DISCOVERY_ENABLE_ANP", "true").lower() == "true",
            enable_mcp=os.getenv("ROUTE_DISCOVERY_ENABLE_MCP", "true").lower() == "true",
            # Domain configuration
            avg_speed_kmh=float(os.getenv("ROUTE_DISCOVERY_AVG_SPEED_KMH", "40.0")),
            cost_per_km=float(os.getenv("ROUTE_DISCOVERY_COST_PER_KM", "1.5")),
            max_stops=int(os.getenv("ROUTE_DISCOVERY_MAX_STOPS", "10")),
            # Optimization parameters
            enable_2opt=os.getenv("ROUTE_DISCOVERY_ENABLE_2OPT", "true").lower() == "true",
            max_2opt_iterations=int(os.getenv("ROUTE_DISCOVERY_MAX_2OPT_ITERATIONS", "100")),
            # Alternative routes
            default_num_alternatives=int(
                os.getenv("ROUTE_DISCOVERY_DEFAULT_NUM_ALTERNATIVES", "3")
            ),
            # Caching
            enable_cache=os.getenv("ROUTE_DISCOVERY_ENABLE_CACHE", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("ROUTE_DISCOVERY_CACHE_TTL_SECONDS", "300")),
            # Performance
            enable_metrics=os.getenv("ROUTE_DISCOVERY_ENABLE_METRICS", "true").lower() == "true",
        )


@dataclass
class RouteSegment:
    """A segment of a route"""

    from_location: Tuple[float, float]
    to_location: Tuple[float, float]
    distance_km: float
    duration_minutes: float
    cost_estimate: float


# ============================================================================
# RESOURCE MONITORING
# ============================================================================


class ResourceMonitor:
    """Monitor agent resource usage"""

    def __init__(self, max_memory_mb: int, max_cpu_percent: int):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None

    def check_resources(self) -> Dict[str, Any]:
        """Check if resource usage is within limits"""
        if not self.process:
            return {"status": "ok", "reason": "monitoring_unavailable"}

        try:
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            cpu_percent = self.process.cpu_percent(interval=0.1)

            if memory_mb > self.max_memory_mb:
                return {
                    "status": "error",
                    "reason": f"Memory usage {memory_mb:.1f}MB exceeds limit {self.max_memory_mb}MB",
                }

            if cpu_percent > self.max_cpu_percent:
                return {
                    "status": "warning",
                    "reason": f"CPU usage {cpu_percent:.1f}% exceeds limit {self.max_cpu_percent}%",
                }

            return {
                "status": "ok",
                "memory_mb": round(memory_mb, 2),
                "cpu_percent": round(cpu_percent, 2),
            }
        except Exception as e:
            return {"status": "error", "reason": f"Monitoring error: {str(e)}"}


# ============================================================================
# MAIN AGENT
# ============================================================================


class RouteDiscoveryAgent(BaseAgent, ProtocolMixin):
    """
    Route Discovery Agent - Architecturally Compliant v1.0

    Discovers and optimizes routes using nearest-neighbor and 2-opt algorithms.
    Provides time estimation, alternative routes, and efficiency scoring.

    Architectural Principles:
    - Standardized: BaseAgent + ProtocolMixin architecture
    - Interoperable: Full protocol support (A2A, A2P, ACP, ANP, MCP)
    - Redeployable: Environment-based configuration
    - Reusable: Clear public API with type hints
    - Atomic: Single responsibility - route optimization
    - Composable: Works in swarms with other agents
    - Orchestratable: Async lifecycle support
    - Agnostic: No vendor dependencies
    """

    def __init__(self, agent_id: str, config: RouteDiscoveryAgentConfig):
        """
        Initialize Route Discovery Agent

        Args:
            agent_id: Unique identifier for this agent instance
            config: Agent configuration
        """
        # Initialize BaseAgent (must be first for ABC)
        super(BaseAgent, self).__init__()

        # Set required attributes
        self.agent_id = agent_id
        self.agent_type = AGENT_TYPE
        self.version = AGENT_VERSION

        # Initialize ProtocolMixin
        ProtocolMixin.__init__(self)

        # Store configuration
        self.typed_config = config

        # Resource monitoring
        self._resource_monitor = ResourceMonitor(
            max_memory_mb=config.max_memory_mb, max_cpu_percent=config.max_cpu_percent
        )

        # State
        self._initialized = False
        self._metrics = {
            "routes_calculated": 0,
            "alternatives_generated": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_execution_time_ms": 0.0,
        }

        # Cache for route calculations
        self._route_cache: Dict[str, Tuple[Any, float]] = {}

        # Status
        self._status = "created"

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize agent

        Returns:
            Initialization result with status
        """
        if self._initialized:
            return {"status": "already_initialized", "agent_id": self.agent_id}

        try:
            # Check resources
            resource_check = self._resource_monitor.check_resources()
            if resource_check["status"] == "error":
                return {
                    "status": "error",
                    "reason": resource_check["reason"],
                    "agent_id": self.agent_id,
                }

            self._initialized = True
            self._status = "ready"

            return {
                "status": "initialized",
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "version": self.version,
                "protocols": SUPPORTED_PROTOCOLS,
                "config": {
                    "avg_speed_kmh": self.typed_config.avg_speed_kmh,
                    "max_stops": self.typed_config.max_stops,
                    "enable_2opt": self.typed_config.enable_2opt,
                    "enable_cache": self.typed_config.enable_cache,
                },
            }

        except Exception as e:
            self._status = "error"
            return {
                "status": "error",
                "reason": f"Initialization failed: {str(e)}",
                "agent_id": self.agent_id,
            }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute route discovery task

        Args:
            input_data: Task with 'action' and parameters
                - action: "calculate_route" | "estimate_time" | "find_alternatives"
                - Additional parameters based on action

        Returns:
            Execution result
        """
        start_time = time.time()

        if not self._initialized:
            return {"success": False, "error": "Agent not initialized", "agent_id": self.agent_id}

        # Check resources
        resource_check = self._resource_monitor.check_resources()
        if resource_check["status"] == "error":
            return {"success": False, "error": resource_check["reason"], "agent_id": self.agent_id}

        try:
            action = input_data.get("action")

            if action == "calculate_route":
                result = await self._handle_route_calculation(input_data)
            elif action == "estimate_time":
                result = await self._handle_time_estimation(input_data)
            elif action == "find_alternatives":
                result = await self._handle_alternative_routes(input_data)
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}

            # Update metrics
            if self.typed_config.enable_metrics:
                execution_time_ms = (time.time() - start_time) * 1000
                self._metrics["total_execution_time_ms"] += execution_time_ms
                result["execution_time_ms"] = round(execution_time_ms, 2)

            result["agent_id"] = self.agent_id
            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "agent_id": self.agent_id,
            }

    async def shutdown(self) -> Dict[str, Any]:
        """
        Shutdown agent gracefully

        Returns:
            Shutdown result with final metrics
        """
        try:
            # Clear cache
            self._route_cache.clear()

            self._initialized = False
            self._status = "shutdown"

            return {
                "status": "shutdown",
                "agent_id": self.agent_id,
                "final_metrics": self._metrics.copy(),
            }

        except Exception as e:
            return {
                "status": "error",
                "reason": f"Shutdown failed: {str(e)}",
                "agent_id": self.agent_id,
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check agent health

        Returns:
            Health status with resource metrics
        """
        resource_check = self._resource_monitor.check_resources()

        return {
            "status": self._status,
            "initialized": self._initialized,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "version": self.version,
            "resources": resource_check,
            "metrics": self._metrics.copy() if self.typed_config.enable_metrics else {},
            "cache_size": len(self._route_cache),
            "timestamp": datetime.now().isoformat(),
        }

    # ========================================================================
    # BASEAGENT ABSTRACT METHOD IMPLEMENTATIONS
    # ========================================================================

    async def _configure_data_sources(self):
        """Configure data sources - not required for route discovery"""
        pass

    async def _initialize_specific(self):
        """Agent-specific initialization - handled in initialize()"""
        pass

    async def _fetch_required_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch required data - route discovery doesn't need external data"""
        return {}

    async def _execute_logic(
        self, input_data: Dict[str, Any], fetched_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Core execution logic - delegates to execute() method"""
        return await self.execute(input_data)

    # ========================================================================
    # DOMAIN METHODS - Route Optimization
    # ========================================================================

    def calculate_optimal_route(
        self, stops: List[Tuple[float, float]], start_location: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal route through multiple stops using nearest-neighbor algorithm

        Args:
            stops: List of (lat, lon) waypoints to visit
            start_location: Starting point (if None, use first stop)

        Returns:
            Optimized route with sequence and metrics
        """
        if not stops:
            return {
                "route": [],
                "sequence": [],
                "total_distance_km": 0.0,
                "total_time_minutes": 0.0,
                "algorithm": "none",
            }

        # Check cache
        cache_key = f"{start_location}:{tuple(stops)}"
        if self.typed_config.enable_cache and cache_key in self._route_cache:
            cached_result, cache_time = self._route_cache[cache_key]
            if time.time() - cache_time < self.typed_config.cache_ttl_seconds:
                self._metrics["cache_hits"] += 1
                return cached_result

        self._metrics["cache_misses"] += 1

        # Start from specified location or first stop
        current = start_location if start_location else stops[0]
        remaining = stops.copy()

        if start_location:
            route = [start_location]
            sequence = []
        else:
            route = [stops[0]]
            remaining.remove(stops[0])
            sequence = [0]

        total_distance = 0.0

        # Nearest-neighbor algorithm
        while remaining:
            # Find nearest unvisited stop
            nearest = min(remaining, key=lambda stop: self._calculate_distance(current, stop))

            distance = self._calculate_distance(current, nearest)
            total_distance += distance

            route.append(nearest)
            sequence.append(stops.index(nearest))
            remaining.remove(nearest)
            current = nearest

        # Apply 2-opt improvement if enabled
        algorithm = "nearest_neighbor"
        if self.typed_config.enable_2opt and len(route) >= 4:
            route = self._two_opt_improvement(route)
            algorithm = "nearest_neighbor_2opt"
            # Recalculate distance after optimization
            total_distance = sum(
                self._calculate_distance(route[i], route[i + 1]) for i in range(len(route) - 1)
            )

        # Calculate total time
        total_time = (total_distance / self.typed_config.avg_speed_kmh) * 60

        result = {
            "route": route,
            "sequence": sequence,
            "total_distance_km": round(total_distance, 2),
            "total_time_minutes": round(total_time, 2),
            "stops": len(stops),
            "algorithm": algorithm,
        }

        # Cache result
        if self.typed_config.enable_cache:
            self._route_cache[cache_key] = (result, time.time())

        self._metrics["routes_calculated"] += 1

        return result

    def estimate_total_time(
        self, route: List[Tuple[float, float]], traffic_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Estimate total travel time for a route

        Args:
            route: List of (lat, lon) waypoints
            traffic_multiplier: Traffic delay factor (1.0 = normal, 2.0 = double time)

        Returns:
            Time estimation with breakdown
        """
        if len(route) < 2:
            return {"total_time_minutes": 0.0, "segments": [], "traffic_adjusted": False}

        segments = []
        total_distance = 0.0

        for i in range(len(route) - 1):
            distance = self._calculate_distance(route[i], route[i + 1])
            base_time = (distance / self.typed_config.avg_speed_kmh) * 60
            adjusted_time = base_time * traffic_multiplier

            segments.append(
                {
                    "from": route[i],
                    "to": route[i + 1],
                    "distance_km": round(distance, 2),
                    "base_time_minutes": round(base_time, 2),
                    "adjusted_time_minutes": round(adjusted_time, 2),
                }
            )

            total_distance += distance

        total_base_time = (total_distance / self.typed_config.avg_speed_kmh) * 60
        total_adjusted_time = total_base_time * traffic_multiplier

        return {
            "total_time_minutes": round(total_adjusted_time, 2),
            "base_time_minutes": round(total_base_time, 2),
            "total_distance_km": round(total_distance, 2),
            "traffic_multiplier": traffic_multiplier,
            "segments": segments,
            "traffic_adjusted": traffic_multiplier != 1.0,
        }

    def get_alternative_routes(
        self, route: List[Tuple[float, float]], num_alternatives: int = None
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative routes by varying the stop order

        Args:
            route: Original route waypoints
            num_alternatives: Number of alternatives to generate (uses config default if None)

        Returns:
            List of alternative route options
        """
        if num_alternatives is None:
            num_alternatives = self.typed_config.default_num_alternatives

        if len(route) < 3:
            return []

        alternatives = []

        # Alternative 1: Reverse some segments
        if len(route) >= 4:
            alt_route = route.copy()
            mid = len(alt_route) // 2
            alt_route[1:mid] = reversed(alt_route[1:mid])
            alt_metrics = self.estimate_total_time(alt_route)
            alternatives.append(
                {"route": alt_route, "strategy": "segment_reversal", "metrics": alt_metrics}
            )

        # Alternative 2: 2-opt improvement (swap edges)
        if len(route) >= 4 and self.typed_config.enable_2opt:
            alt_route = self._two_opt_improvement(route)
            alt_metrics = self.estimate_total_time(alt_route)
            alternatives.append(
                {"route": alt_route, "strategy": "2opt_optimization", "metrics": alt_metrics}
            )

        # Alternative 3: Different starting point
        if len(route) >= 4:
            start_idx = len(route) // 3
            alt_route = route[start_idx:] + route[:start_idx]
            alt_metrics = self.estimate_total_time(alt_route)
            alternatives.append(
                {"route": alt_route, "strategy": "alternate_start", "metrics": alt_metrics}
            )

        self._metrics["alternatives_generated"] += len(alternatives[:num_alternatives])

        return alternatives[:num_alternatives]

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    async def _handle_route_calculation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle route calculation task"""
        stops = task.get("stops", [])
        start_location = task.get("start_location")

        route_result = self.calculate_optimal_route(stops, start_location)

        return {"success": True, "route": route_result}

    async def _handle_time_estimation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle time estimation task"""
        route = task.get("route", [])
        traffic_multiplier = task.get("traffic_multiplier", 1.0)

        estimation = self.estimate_total_time(route, traffic_multiplier)

        return {"success": True, "estimation": estimation}

    async def _handle_alternative_routes(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alternative route finding task"""
        route = task.get("route", [])
        num_alternatives = task.get("num_alternatives")

        alternatives = self.get_alternative_routes(route, num_alternatives)

        return {"success": True, "alternatives": alternatives, "count": len(alternatives)}

    def _calculate_distance(
        self, point1: Tuple[float, float], point2: Tuple[float, float]
    ) -> float:
        """
        Calculate distance using Haversine formula

        Args:
            point1: (latitude, longitude) tuple
            point2: (latitude, longitude) tuple

        Returns:
            Distance in kilometers
        """
        lat1, lon1 = point1
        lat2, lon2 = point2

        R = 6371  # Earth radius in km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _two_opt_improvement(self, route: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Apply 2-opt improvement to route
        Swaps edges to reduce total distance

        Args:
            route: Original route

        Returns:
            Improved route
        """
        improved_route = route.copy()
        improved = True
        iterations = 0

        while improved and iterations < self.typed_config.max_2opt_iterations:
            improved = False
            iterations += 1

            for i in range(1, len(improved_route) - 2):
                for j in range(i + 1, len(improved_route) - 1):
                    # Calculate current distance
                    current_dist = self._calculate_distance(
                        improved_route[i - 1], improved_route[i]
                    ) + self._calculate_distance(improved_route[j], improved_route[j + 1])

                    # Calculate distance after swap
                    new_dist = self._calculate_distance(
                        improved_route[i - 1], improved_route[j]
                    ) + self._calculate_distance(improved_route[i], improved_route[j + 1])

                    # If improvement found, apply swap
                    if new_dist < current_dist:
                        improved_route[i : j + 1] = reversed(improved_route[i : j + 1])
                        improved = True
                        break

                if improved:
                    break

        return improved_route

    def _calculate_efficiency_score(
        self, route: List[Tuple[float, float]], total_distance: float
    ) -> float:
        """
        Calculate route efficiency score (0-1, higher is better)
        Based on straightness and number of stops

        Args:
            route: Route waypoints
            total_distance: Total route distance

        Returns:
            Efficiency score (0-1)
        """
        if len(route) < 2:
            return 0.0

        # Calculate direct distance from start to end
        direct_distance = self._calculate_distance(route[0], route[-1])

        # Straightness factor: how close is the route to a straight line
        if total_distance > 0:
            straightness = direct_distance / total_distance
        else:
            straightness = 0.0

        # Stops penalty: fewer stops is better
        stops_factor = 1.0 - (len(route) / self.typed_config.max_stops)
        stops_factor = max(0.0, stops_factor)

        # Combined score (60% straightness, 40% stops)
        efficiency = 0.6 * straightness + 0.4 * stops_factor

        return min(1.0, efficiency)


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


async def create_route_discovery_agent(
    agent_id: str = None, config: RouteDiscoveryAgentConfig = None
) -> RouteDiscoveryAgent:
    """
    Factory function to create and initialize Route Discovery Agent

    Args:
        agent_id: Unique identifier (auto-generated if None)
        config: Agent configuration (uses environment if None)

    Returns:
        Initialized RouteDiscoveryAgent instance
    """
    if agent_id is None:
        agent_id = f"route_discovery_{int(time.time())}"

    if config is None:
        config = RouteDiscoveryAgentConfig.from_environment()

    agent = RouteDiscoveryAgent(agent_id=agent_id, config=config)
    await agent.initialize()

    return agent


# ============================================================================
# CLI INTERFACE
# ============================================================================


async def main():
    """CLI interface for testing and demonstration"""
    import argparse

    parser = argparse.ArgumentParser(description="Route Discovery Agent v1.0")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--test", action="store_true", help="Run test scenario")
    parser.add_argument("--agent-id", default="route_discovery_cli", help="Agent ID")

    args = parser.parse_args()

    # Create agent
    print(f"Creating Route Discovery Agent: {args.agent_id}")
    agent = await create_route_discovery_agent(agent_id=args.agent_id)

    if args.health_check:
        print("\nRunning health check...")
        health = await agent.health_check()
        print(f"Status: {health['status']}")
        print(f"Initialized: {health['initialized']}")
        print(f"Resources: {health['resources']}")
        print(f"Metrics: {health.get('metrics', {})}")

    if args.test:
        print("\nRunning test scenario...")

        # Test 1: Calculate optimal route
        print("\n1. Calculate optimal route:")
        stops = [
            (37.7749, -122.4194),  # San Francisco
            (37.3382, -121.8863),  # San Jose
            (37.8044, -122.2712),  # Oakland
            (37.5485, -121.9886),  # Fremont
        ]

        result = await agent.execute({"action": "calculate_route", "stops": stops})

        print(f"Success: {result['success']}")
        if result["success"]:
            route = result["route"]
            print(f"Algorithm: {route['algorithm']}")
            print(f"Total distance: {route['total_distance_km']} km")
            print(f"Total time: {route['total_time_minutes']} minutes")
            print(f"Stops: {route['stops']}")

        # Test 2: Find alternative routes
        print("\n2. Find alternative routes:")
        result = await agent.execute(
            {"action": "find_alternatives", "route": stops, "num_alternatives": 2}
        )

        print(f"Success: {result['success']}")
        if result["success"]:
            print(f"Alternatives found: {result['count']}")
            for i, alt in enumerate(result["alternatives"], 1):
                print(
                    f"  Alternative {i} ({alt['strategy']}): "
                    f"{alt['metrics']['total_distance_km']} km, "
                    f"{alt['metrics']['total_time_minutes']} minutes"
                )

        # Final health check
        print("\n3. Final health check:")
        health = await agent.health_check()
        print(f"Metrics: {health.get('metrics', {})}")

    # Shutdown
    print("\nShutting down agent...")
    shutdown_result = await agent.shutdown()
    print(f"Shutdown status: {shutdown_result['status']}")
    print(f"Final metrics: {shutdown_result.get('final_metrics', {})}")


if __name__ == "__main__":
    asyncio.run(main())
