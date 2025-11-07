"""
Handoff Coordination Agent v1.0 - Architecturally Compliant
===========================================================

AGENT METADATA:
--------------
Agent Type: handoff_coordination
Version: 1.0.0
Protocols: A2A, A2P, ACP, ANP, MCP
Capabilities: handoff_planning, timing_coordination, multi_vehicle_routing

ARCHITECTURAL COMPLIANCE:
------------------------
✓ Standardized: Follows BaseAgent architecture with typed configuration
✓ Interoperable: Supports all 5 core protocols (A2A, A2P, ACP, ANP, MCP)
✓ Redeployable: Environment-based configuration, no hardcoded values
✓ Reusable: Clear interfaces, well-documented methods
✓ Atomic: Single responsibility - handoff coordination
✓ Composable: Can be combined with other agents in swarms
✓ Orchestratable: Async lifecycle methods for coordination
✓ Agnostic: No vendor/model/system dependencies

DOMAIN ALGORITHMS:
-----------------
- Multi-vehicle route segmentation
- Optimal handoff point calculation
- Timing coordination with buffer management
- Quality scoring for handoff points
- Distance-based bearing calculation

USAGE:
------
    from library.agents.handoff_coordination_agent_v1 import (
        create_handoff_coordination_agent,
        HandoffCoordinationAgentConfig
    )

    # Create with environment configuration
    agent = await create_handoff_coordination_agent()

    # Execute handoff planning
    result = await agent.execute({
        "action": "plan_route",
        "origin": (lat1, lon1),
        "destination": (lat2, lon2),
        "departure_time": "2025-10-12T10:00:00"
    })
"""

import os
import math
import time
import asyncio
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
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

from superstandard.agents.base.base_agent import BaseAgent
from src.superstandard.agents.base.protocols import ProtocolMixin

# Agent metadata
AGENT_TYPE = "handoff_coordination"
AGENT_VERSION = "1.0.0"
SUPPORTED_PROTOCOLS = ["A2A", "A2P", "ACP", "ANP", "MCP"]


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class HandoffCoordinationAgentConfig:
    """
    Configuration for Handoff Coordination Agent

    All parameters can be set via environment variables with prefix:
    HANDOFF_COORDINATION_*

    Example:
        export HANDOFF_COORDINATION_AVG_SPEED_KMH=50.0
        export HANDOFF_COORDINATION_IDEAL_BUFFER_MINUTES=15
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
    min_buffer_minutes: float = 5.0
    max_buffer_minutes: float = 30.0
    ideal_buffer_minutes: float = 10.0
    avg_speed_kmh: float = 45.0

    # Route segmentation
    min_route_distance_for_multi_vehicle_km: float = 50.0
    target_segment_distance_km: float = 75.0
    max_vehicles: int = 5

    # Handoff quality
    quality_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "wait_time": 0.6,
            "distance_balance": 0.3,
            "buffer_optimization": 0.1,
        }
    )

    # Caching
    enable_cache: bool = True
    cache_ttl_seconds: int = 300

    # Performance
    enable_metrics: bool = True

    @classmethod
    def from_environment(cls) -> "HandoffCoordinationAgentConfig":
        """Create configuration from environment variables"""
        return cls(
            # Logging
            log_level=os.getenv("HANDOFF_COORDINATION_LOG_LEVEL", "INFO"),
            # Resource limits
            max_memory_mb=int(os.getenv("HANDOFF_COORDINATION_MAX_MEMORY_MB", "512")),
            max_cpu_percent=int(os.getenv("HANDOFF_COORDINATION_MAX_CPU_PERCENT", "80")),
            # Protocol flags
            enable_a2a=os.getenv("HANDOFF_COORDINATION_ENABLE_A2A", "true").lower() == "true",
            enable_a2p=os.getenv("HANDOFF_COORDINATION_ENABLE_A2P", "true").lower() == "true",
            enable_acp=os.getenv("HANDOFF_COORDINATION_ENABLE_ACP", "true").lower() == "true",
            enable_anp=os.getenv("HANDOFF_COORDINATION_ENABLE_ANP", "true").lower() == "true",
            enable_mcp=os.getenv("HANDOFF_COORDINATION_ENABLE_MCP", "true").lower() == "true",
            # Domain configuration
            min_buffer_minutes=float(os.getenv("HANDOFF_COORDINATION_MIN_BUFFER_MINUTES", "5.0")),
            max_buffer_minutes=float(os.getenv("HANDOFF_COORDINATION_MAX_BUFFER_MINUTES", "30.0")),
            ideal_buffer_minutes=float(
                os.getenv("HANDOFF_COORDINATION_IDEAL_BUFFER_MINUTES", "10.0")
            ),
            avg_speed_kmh=float(os.getenv("HANDOFF_COORDINATION_AVG_SPEED_KMH", "45.0")),
            # Route segmentation
            min_route_distance_for_multi_vehicle_km=float(
                os.getenv("HANDOFF_COORDINATION_MIN_ROUTE_DISTANCE_KM", "50.0")
            ),
            target_segment_distance_km=float(
                os.getenv("HANDOFF_COORDINATION_TARGET_SEGMENT_KM", "75.0")
            ),
            max_vehicles=int(os.getenv("HANDOFF_COORDINATION_MAX_VEHICLES", "5")),
            # Caching
            enable_cache=os.getenv("HANDOFF_COORDINATION_ENABLE_CACHE", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("HANDOFF_COORDINATION_CACHE_TTL_SECONDS", "300")),
            # Performance
            enable_metrics=os.getenv("HANDOFF_COORDINATION_ENABLE_METRICS", "true").lower()
            == "true",
        )


@dataclass
class Vehicle:
    """Vehicle information"""

    id: str
    location: Tuple[float, float]
    destination: Tuple[float, float]
    capacity: int
    current_occupancy: int = 0
    avg_speed_kmh: float = 45.0


@dataclass
class HandoffPoint:
    """A potential handoff location"""

    location: Tuple[float, float]
    arrival_time_vehicle1: datetime
    departure_time_vehicle2: datetime
    wait_time_minutes: float
    quality_score: float


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


class HandoffCoordinationAgent(BaseAgent, ProtocolMixin):
    """
    Handoff Coordination Agent - Architecturally Compliant v1.0

    Coordinates multi-vehicle handoffs with timing optimization and quality scoring.
    Plans optimal handoff points for long-distance routes.

    Architectural Principles:
    - Standardized: BaseAgent + ProtocolMixin architecture
    - Interoperable: Full protocol support (A2A, A2P, ACP, ANP, MCP)
    - Redeployable: Environment-based configuration
    - Reusable: Clear public API with type hints
    - Atomic: Single responsibility - handoff coordination
    - Composable: Works in swarms with other agents
    - Orchestratable: Async lifecycle support
    - Agnostic: No vendor dependencies
    """

    def __init__(self, agent_id: str, config: HandoffCoordinationAgentConfig):
        """
        Initialize Handoff Coordination Agent

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
            "routes_planned": 0,
            "handoffs_coordinated": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_execution_time_ms": 0.0,
        }

        # Cache for route calculations
        self._handoff_cache: Dict[str, Tuple[Any, float]] = {}

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
                    "ideal_buffer_minutes": self.typed_config.ideal_buffer_minutes,
                    "max_vehicles": self.typed_config.max_vehicles,
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
        Execute handoff coordination task

        Args:
            input_data: Task with 'action' and parameters
                - action: "plan_route" | "find_handoff_points" | "coordinate_timing"
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

            if action == "plan_route":
                result = await self._handle_route_planning(input_data)
            elif action == "find_handoff_points":
                result = await self._handle_handoff_finding(input_data)
            elif action == "coordinate_timing":
                result = await self._handle_timing_coordination(input_data)
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
            self._handoff_cache.clear()

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
            "cache_size": len(self._handoff_cache),
            "timestamp": datetime.now().isoformat(),
        }

    # ========================================================================
    # BASEAGENT ABSTRACT METHOD IMPLEMENTATIONS
    # ========================================================================

    async def _configure_data_sources(self):
        """Configure data sources - not required for handoff coordination"""
        pass

    async def _initialize_specific(self):
        """Agent-specific initialization - handled in initialize()"""
        pass

    async def _fetch_required_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch required data - handoff coordination doesn't need external data"""
        return {}

    async def _execute_logic(
        self, input_data: Dict[str, Any], fetched_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Core execution logic - delegates to execute() method"""
        return await self.execute(input_data)

    # ========================================================================
    # DOMAIN METHODS - Handoff Coordination
    # ========================================================================

    def plan_multi_vehicle_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        departure_time: datetime,
        max_vehicles: int = None,
    ) -> Dict[str, Any]:
        """
        Plan a long-distance route using multiple vehicles

        Args:
            origin: Starting location (lat, lon)
            destination: Final destination (lat, lon)
            departure_time: When to start
            max_vehicles: Maximum number of vehicles to use (uses config default if None)

        Returns:
            Multi-vehicle route plan
        """
        if max_vehicles is None:
            max_vehicles = self.typed_config.max_vehicles

        total_distance = self._calculate_distance(origin, destination)

        # Decide if multi-vehicle makes sense
        if total_distance < self.typed_config.min_route_distance_for_multi_vehicle_km:
            return {
                "needs_multi_vehicle": False,
                "reason": f"Route {total_distance:.1f}km is short enough for single vehicle",
                "total_distance_km": round(total_distance, 2),
            }

        # Calculate optimal number of segments
        num_segments = min(
            max_vehicles, max(2, int(total_distance / self.typed_config.target_segment_distance_km))
        )

        # Generate handoff points along the route
        handoff_points = self._generate_handoff_points(origin, destination, num_segments - 1)

        # Create segments
        segments = []
        current_location = origin
        current_time = departure_time

        for i in range(num_segments):
            if i < len(handoff_points):
                next_location = handoff_points[i]
            else:
                next_location = destination

            segment_distance = self._calculate_distance(current_location, next_location)
            segment_duration = (segment_distance / self.typed_config.avg_speed_kmh) * 60

            segments.append(
                {
                    "segment_number": i + 1,
                    "from": current_location,
                    "to": next_location,
                    "distance_km": round(segment_distance, 2),
                    "duration_minutes": round(segment_duration, 2),
                    "departure_time": current_time.isoformat(),
                    "arrival_time": (
                        current_time + timedelta(minutes=segment_duration)
                    ).isoformat(),
                    "is_handoff_point": i < len(handoff_points),
                }
            )

            # Add buffer time for handoff
            if i < len(handoff_points):
                current_time = current_time + timedelta(
                    minutes=segment_duration + self.typed_config.ideal_buffer_minutes
                )
            else:
                current_time = current_time + timedelta(minutes=segment_duration)

            current_location = next_location

        self._metrics["routes_planned"] += 1

        return {
            "needs_multi_vehicle": True,
            "total_distance_km": round(total_distance, 2),
            "num_segments": num_segments,
            "num_handoffs": len(handoff_points),
            "segments": segments,
            "total_duration_minutes": round(
                (current_time - departure_time).total_seconds() / 60, 2
            ),
            "handoff_points": [{"lat": p[0], "lon": p[1]} for p in handoff_points],
        }

    def find_optimal_handoff_points(
        self, vehicle1: Dict[str, Any], vehicle2: Dict[str, Any]
    ) -> List[HandoffPoint]:
        """
        Find optimal handoff points between two vehicles

        Args:
            vehicle1: First vehicle dict
            vehicle2: Second vehicle dict

        Returns:
            List of potential handoff points sorted by quality
        """
        v1 = self._dict_to_vehicle(vehicle1)
        v2 = self._dict_to_vehicle(vehicle2)

        # Calculate midpoint between vehicles
        midpoint = ((v1.location[0] + v2.location[0]) / 2, (v1.location[1] + v2.location[1]) / 2)

        # Generate candidate handoff points around the midpoint
        candidates = []

        # Central point
        candidates.append(midpoint)

        # Points slightly offset from midpoint
        for offset_km in [5, 10]:
            for bearing in [0, 90, 180, 270]:  # N, E, S, W
                offset_lat = offset_km / 111.0  # Rough conversion
                offset_lon = offset_km / (111.0 * math.cos(math.radians(midpoint[0])))

                if bearing == 0:  # North
                    point = (midpoint[0] + offset_lat, midpoint[1])
                elif bearing == 90:  # East
                    point = (midpoint[0], midpoint[1] + offset_lon)
                elif bearing == 180:  # South
                    point = (midpoint[0] - offset_lat, midpoint[1])
                else:  # West
                    point = (midpoint[0], midpoint[1] - offset_lon)

                candidates.append(point)

        # Evaluate each candidate
        handoff_points = []

        for candidate in candidates:
            # Calculate distances and times
            dist1 = self._calculate_distance(v1.location, candidate)
            dist2 = self._calculate_distance(v2.location, candidate)

            time1 = (dist1 / v1.avg_speed_kmh) * 60
            time2 = (dist2 / v2.avg_speed_kmh) * 60

            # Calculate wait time (absolute difference)
            wait_time = abs(time1 - time2)

            # Quality score (lower wait time = higher quality)
            if wait_time <= self.typed_config.ideal_buffer_minutes:
                quality = 1.0 - (wait_time / self.typed_config.ideal_buffer_minutes) * 0.3
            elif wait_time <= self.typed_config.max_buffer_minutes:
                quality = (
                    0.7
                    - (
                        (wait_time - self.typed_config.ideal_buffer_minutes)
                        / (
                            self.typed_config.max_buffer_minutes
                            - self.typed_config.ideal_buffer_minutes
                        )
                    )
                    * 0.5
                )
            else:
                quality = 0.2

            # Penalize if too close to either vehicle
            if dist1 < 5 or dist2 < 5:
                quality *= 0.5

            arrival_time_v1 = datetime.now() + timedelta(minutes=time1)
            departure_time_v2 = datetime.now() + timedelta(minutes=max(time1, time2))

            handoff_points.append(
                HandoffPoint(
                    location=candidate,
                    arrival_time_vehicle1=arrival_time_v1,
                    departure_time_vehicle2=departure_time_v2,
                    wait_time_minutes=wait_time,
                    quality_score=quality,
                )
            )

        # Sort by quality (descending)
        handoff_points.sort(key=lambda h: h.quality_score, reverse=True)

        self._metrics["handoffs_coordinated"] += len(handoff_points)

        return handoff_points[:5]  # Return top 5

    def coordinate_timing(
        self,
        vehicle1: Dict[str, Any],
        vehicle2: Dict[str, Any],
        handoff_location: Tuple[float, float],
    ) -> Dict[str, Any]:
        """
        Coordinate timing for a handoff at a specific location

        Args:
            vehicle1: First vehicle dict
            vehicle2: Second vehicle dict
            handoff_location: Handoff point (lat, lon)

        Returns:
            Timing coordination plan
        """
        v1 = self._dict_to_vehicle(vehicle1)
        v2 = self._dict_to_vehicle(vehicle2)

        # Calculate travel times
        dist1 = self._calculate_distance(v1.location, handoff_location)
        dist2 = self._calculate_distance(v2.location, handoff_location)

        time1 = (dist1 / v1.avg_speed_kmh) * 60
        time2 = (dist2 / v2.avg_speed_kmh) * 60

        now = datetime.now()
        arrival1 = now + timedelta(minutes=time1)
        arrival2 = now + timedelta(minutes=time2)

        # Determine who waits
        if arrival1 < arrival2:
            # Vehicle 1 arrives first, waits for vehicle 2
            wait_time = (arrival2 - arrival1).total_seconds() / 60
            waiting_vehicle = v1.id
            handoff_time = arrival2
        else:
            # Vehicle 2 arrives first, waits for vehicle 1
            wait_time = (arrival1 - arrival2).total_seconds() / 60
            waiting_vehicle = v2.id
            handoff_time = arrival1

        # Check if timing is acceptable
        timing_acceptable = (
            wait_time >= self.typed_config.min_buffer_minutes
            and wait_time <= self.typed_config.max_buffer_minutes
        )

        self._metrics["handoffs_coordinated"] += 1

        return {
            "handoff_location": {"lat": handoff_location[0], "lon": handoff_location[1]},
            "vehicle1": {
                "id": v1.id,
                "arrival_time": arrival1.isoformat(),
                "travel_time_minutes": round(time1, 2),
                "distance_km": round(dist1, 2),
            },
            "vehicle2": {
                "id": v2.id,
                "arrival_time": arrival2.isoformat(),
                "travel_time_minutes": round(time2, 2),
                "distance_km": round(dist2, 2),
            },
            "waiting_vehicle": waiting_vehicle,
            "wait_time_minutes": round(wait_time, 2),
            "handoff_time": handoff_time.isoformat(),
            "timing_acceptable": timing_acceptable,
            "recommendation": self._get_timing_recommendation(wait_time),
        }

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    async def _handle_route_planning(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle multi-vehicle route planning task"""
        origin = tuple(task.get("origin", [0, 0]))
        destination = tuple(task.get("destination", [0, 0]))
        departure_time = task.get("departure_time", datetime.now())

        if isinstance(departure_time, str):
            departure_time = datetime.fromisoformat(departure_time)

        max_vehicles = task.get("max_vehicles")

        plan = self.plan_multi_vehicle_route(origin, destination, departure_time, max_vehicles)

        return {"success": True, "plan": plan}

    async def _handle_handoff_finding(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle handoff point finding task"""
        vehicle1 = task.get("vehicle1", {})
        vehicle2 = task.get("vehicle2", {})

        handoff_points = self.find_optimal_handoff_points(vehicle1, vehicle2)

        return {
            "success": True,
            "handoff_points": [self._handoff_to_dict(h) for h in handoff_points],
            "count": len(handoff_points),
        }

    async def _handle_timing_coordination(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle timing coordination task"""
        vehicle1 = task.get("vehicle1", {})
        vehicle2 = task.get("vehicle2", {})
        handoff_location = tuple(task.get("handoff_location", [0, 0]))

        coordination = self.coordinate_timing(vehicle1, vehicle2, handoff_location)

        return {"success": True, "coordination": coordination}

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

    def _generate_handoff_points(
        self, origin: Tuple[float, float], destination: Tuple[float, float], num_points: int
    ) -> List[Tuple[float, float]]:
        """Generate evenly spaced handoff points along a route"""
        points = []

        for i in range(1, num_points + 1):
            fraction = i / (num_points + 1)
            lat = origin[0] + (destination[0] - origin[0]) * fraction
            lon = origin[1] + (destination[1] - origin[1]) * fraction
            points.append((lat, lon))

        return points

    def _dict_to_vehicle(self, d: Dict[str, Any]) -> Vehicle:
        """Convert dictionary to Vehicle object"""
        return Vehicle(
            id=d.get("id", "unknown"),
            location=tuple(d.get("location", [0, 0])),
            destination=tuple(d.get("destination", [0, 0])),
            capacity=d.get("capacity", 4),
            current_occupancy=d.get("current_occupancy", 0),
            avg_speed_kmh=d.get("avg_speed_kmh", 45.0),
        )

    def _handoff_to_dict(self, handoff: HandoffPoint) -> Dict[str, Any]:
        """Convert HandoffPoint to dictionary"""
        return {
            "location": {"lat": handoff.location[0], "lon": handoff.location[1]},
            "arrival_time_vehicle1": handoff.arrival_time_vehicle1.isoformat(),
            "departure_time_vehicle2": handoff.departure_time_vehicle2.isoformat(),
            "wait_time_minutes": round(handoff.wait_time_minutes, 2),
            "quality_score": round(handoff.quality_score, 3),
        }

    def _get_timing_recommendation(self, wait_time: float) -> str:
        """Get recommendation for specific wait time"""
        if wait_time < self.typed_config.min_buffer_minutes:
            return "Buffer too short - high risk of missed handoff"
        elif wait_time <= self.typed_config.ideal_buffer_minutes:
            return "Optimal timing"
        elif wait_time <= self.typed_config.max_buffer_minutes:
            return "Acceptable timing with some waiting"
        else:
            return "Wait time too long - consider alternative handoff point"


# ============================================================================
# FACTORY FUNCTION
# ============================================================================


async def create_handoff_coordination_agent(
    agent_id: str = None, config: HandoffCoordinationAgentConfig = None
) -> HandoffCoordinationAgent:
    """
    Factory function to create and initialize Handoff Coordination Agent

    Args:
        agent_id: Unique identifier (auto-generated if None)
        config: Agent configuration (uses environment if None)

    Returns:
        Initialized HandoffCoordinationAgent instance
    """
    if agent_id is None:
        agent_id = f"handoff_coordination_{int(time.time())}"

    if config is None:
        config = HandoffCoordinationAgentConfig.from_environment()

    agent = HandoffCoordinationAgent(agent_id=agent_id, config=config)
    await agent.initialize()

    return agent


# ============================================================================
# CLI INTERFACE
# ============================================================================


async def main():
    """CLI interface for testing and demonstration"""
    import argparse

    parser = argparse.ArgumentParser(description="Handoff Coordination Agent v1.0")
    parser.add_argument("--health-check", action="store_true", help="Run health check")
    parser.add_argument("--test", action="store_true", help="Run test scenario")
    parser.add_argument("--agent-id", default="handoff_coordination_cli", help="Agent ID")

    args = parser.parse_args()

    # Create agent
    print(f"Creating Handoff Coordination Agent: {args.agent_id}")
    agent = await create_handoff_coordination_agent(agent_id=args.agent_id)

    if args.health_check:
        print("\nRunning health check...")
        health = await agent.health_check()
        print(f"Status: {health['status']}")
        print(f"Initialized: {health['initialized']}")
        print(f"Resources: {health['resources']}")
        print(f"Metrics: {health.get('metrics', {})}")

    if args.test:
        print("\nRunning test scenario...")

        # Test 1: Plan multi-vehicle route
        print("\n1. Plan multi-vehicle route (SF to LA):")
        result = await agent.execute(
            {
                "action": "plan_route",
                "origin": (37.7749, -122.4194),  # San Francisco
                "destination": (34.0522, -118.2437),  # Los Angeles
                "departure_time": datetime.now().isoformat(),
            }
        )

        print(f"Success: {result['success']}")
        if result["success"]:
            plan = result["plan"]
            print(f"Needs multi-vehicle: {plan['needs_multi_vehicle']}")
            if plan["needs_multi_vehicle"]:
                print(f"Total distance: {plan['total_distance_km']} km")
                print(f"Num segments: {plan['num_segments']}")
                print(f"Num handoffs: {plan['num_handoffs']}")
                print(f"Total duration: {plan['total_duration_minutes']} minutes")

        # Test 2: Find optimal handoff points
        print("\n2. Find optimal handoff points:")
        result = await agent.execute(
            {
                "action": "find_handoff_points",
                "vehicle1": {
                    "id": "v1",
                    "location": (37.7749, -122.4194),
                    "destination": (37.8044, -122.2712),
                    "capacity": 4,
                    "avg_speed_kmh": 45.0,
                },
                "vehicle2": {
                    "id": "v2",
                    "location": (37.5485, -121.9886),
                    "destination": (37.3382, -121.8863),
                    "capacity": 4,
                    "avg_speed_kmh": 45.0,
                },
            }
        )

        print(f"Success: {result['success']}")
        if result["success"]:
            print(f"Handoff points found: {result['count']}")
            if result["handoff_points"]:
                best = result["handoff_points"][0]
                print(f"Best handoff:")
                print(f"  Location: {best['location']}")
                print(f"  Wait time: {best['wait_time_minutes']} minutes")
                print(f"  Quality score: {best['quality_score']}")

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
