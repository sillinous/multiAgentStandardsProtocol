"""
Handoff Coordination Agent for Mobility Routing Swarm

Plans multi-vehicle routes with optimal handoff points and timing coordination.
"""

import math
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from superstandard.agents.base.base_agent import BaseAgent, AgentCapability


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


class HandoffCoordinationAgent(BaseAgent):
    """
    Agent responsible for coordinating multi-vehicle handoffs.
    Plans optimal handoff points and timing for long-distance routes.
    """

    def __init__(self, agent_id: str = "handoff_coordination_agent", workspace_path: str = "./autonomous-ecosystem/workspace"):
        super().__init__(
            agent_id=agent_id,
            agent_type="handoff_coordination",
            capabilities=[AgentCapability.ORCHESTRATION],
            workspace_path=workspace_path
        )

        # Configuration
        self.min_buffer_minutes = 5.0
        self.max_buffer_minutes = 30.0
        self.ideal_buffer_minutes = 10.0
        self.avg_speed_kmh = 45.0

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute handoff coordination task

        Args:
            task: Task with 'action' and parameters

        Returns:
            Task execution result
        """
        action = task.get("action")

        if action == "plan_route":
            return await self._handle_route_planning(task)
        elif action == "find_handoff_points":
            return await self._handle_handoff_finding(task)
        elif action == "coordinate_timing":
            return await self._handle_timing_coordination(task)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze handoff coordination efficiency

        Args:
            input_data: Handoff data to analyze

        Returns:
            Analysis results with recommendations
        """
        handoffs = input_data.get("handoffs", [])

        if not handoffs:
            return {
                "timestamp": datetime.now().isoformat(),
                "total_handoffs": 0,
                "recommendations": ["No handoffs to analyze"]
            }

        # Calculate metrics
        avg_wait = sum(h.get("wait_time_minutes", 0) for h in handoffs) / len(handoffs)
        tight_handoffs = sum(1 for h in handoffs if h.get("wait_time_minutes", 0) < self.min_buffer_minutes)
        long_waits = sum(1 for h in handoffs if h.get("wait_time_minutes", 0) > self.max_buffer_minutes)

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_handoffs": len(handoffs),
            "average_wait_minutes": round(avg_wait, 2),
            "tight_handoffs": tight_handoffs,
            "long_waits": long_waits,
            "coordination_quality": self._calculate_coordination_quality(avg_wait, tight_handoffs, long_waits),
            "recommendations": self._generate_handoff_recommendations(avg_wait, tight_handoffs, long_waits)
        }

        return analysis

    def plan_multi_vehicle_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        departure_time: datetime,
        max_vehicles: int = 3
    ) -> Dict[str, Any]:
        """
        Plan a long-distance route using multiple vehicles

        Args:
            origin: Starting location (lat, lon)
            destination: Final destination (lat, lon)
            departure_time: When to start
            max_vehicles: Maximum number of vehicles to use

        Returns:
            Multi-vehicle route plan
        """
        total_distance = self._calculate_distance(origin, destination)

        # Decide if multi-vehicle makes sense
        if total_distance < 50:  # Less than 50km - single vehicle is better
            return {
                "needs_multi_vehicle": False,
                "reason": "Route is short enough for single vehicle",
                "total_distance_km": round(total_distance, 2)
            }

        # Calculate optimal number of segments
        avg_segment_distance = 75  # Target 75km per vehicle
        num_segments = min(max_vehicles, max(2, int(total_distance / avg_segment_distance)))

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
            segment_duration = (segment_distance / self.avg_speed_kmh) * 60

            segments.append({
                "segment_number": i + 1,
                "from": current_location,
                "to": next_location,
                "distance_km": round(segment_distance, 2),
                "duration_minutes": round(segment_duration, 2),
                "departure_time": current_time.isoformat(),
                "arrival_time": (current_time + timedelta(minutes=segment_duration)).isoformat(),
                "is_handoff_point": i < len(handoff_points)
            })

            # Add buffer time for handoff
            if i < len(handoff_points):
                current_time = current_time + timedelta(minutes=segment_duration + self.ideal_buffer_minutes)
            else:
                current_time = current_time + timedelta(minutes=segment_duration)

            current_location = next_location

        return {
            "needs_multi_vehicle": True,
            "total_distance_km": round(total_distance, 2),
            "num_segments": num_segments,
            "num_handoffs": len(handoff_points),
            "segments": segments,
            "total_duration_minutes": round((current_time - departure_time).total_seconds() / 60, 2),
            "handoff_points": [{"lat": p[0], "lon": p[1]} for p in handoff_points]
        }

    def find_optimal_handoff_points(
        self,
        vehicle1: Dict[str, Any],
        vehicle2: Dict[str, Any]
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
        midpoint = (
            (v1.location[0] + v2.location[0]) / 2,
            (v1.location[1] + v2.location[1]) / 2
        )

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
            if wait_time <= self.ideal_buffer_minutes:
                quality = 1.0 - (wait_time / self.ideal_buffer_minutes) * 0.3
            elif wait_time <= self.max_buffer_minutes:
                quality = 0.7 - ((wait_time - self.ideal_buffer_minutes) /
                               (self.max_buffer_minutes - self.ideal_buffer_minutes)) * 0.5
            else:
                quality = 0.2

            # Penalize if too close to either vehicle
            if dist1 < 5 or dist2 < 5:
                quality *= 0.5

            arrival_time_v1 = datetime.now() + timedelta(minutes=time1)
            departure_time_v2 = datetime.now() + timedelta(minutes=max(time1, time2))

            handoff_points.append(HandoffPoint(
                location=candidate,
                arrival_time_vehicle1=arrival_time_v1,
                departure_time_vehicle2=departure_time_v2,
                wait_time_minutes=wait_time,
                quality_score=quality
            ))

        # Sort by quality (descending)
        handoff_points.sort(key=lambda h: h.quality_score, reverse=True)

        return handoff_points[:5]  # Return top 5

    def coordinate_timing(
        self,
        vehicle1: Dict[str, Any],
        vehicle2: Dict[str, Any],
        handoff_location: Tuple[float, float]
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
            wait_time >= self.min_buffer_minutes and
            wait_time <= self.max_buffer_minutes
        )

        return {
            "handoff_location": {"lat": handoff_location[0], "lon": handoff_location[1]},
            "vehicle1": {
                "id": v1.id,
                "arrival_time": arrival1.isoformat(),
                "travel_time_minutes": round(time1, 2),
                "distance_km": round(dist1, 2)
            },
            "vehicle2": {
                "id": v2.id,
                "arrival_time": arrival2.isoformat(),
                "travel_time_minutes": round(time2, 2),
                "distance_km": round(dist2, 2)
            },
            "waiting_vehicle": waiting_vehicle,
            "wait_time_minutes": round(wait_time, 2),
            "handoff_time": handoff_time.isoformat(),
            "timing_acceptable": timing_acceptable,
            "recommendation": self._get_timing_recommendation(wait_time)
        }

    async def _handle_route_planning(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle multi-vehicle route planning task"""
        origin = tuple(task.get("origin", [0, 0]))
        destination = tuple(task.get("destination", [0, 0]))
        departure_time = task.get("departure_time", datetime.now())

        if isinstance(departure_time, str):
            departure_time = datetime.fromisoformat(departure_time)

        max_vehicles = task.get("max_vehicles", 3)

        plan = self.plan_multi_vehicle_route(origin, destination, departure_time, max_vehicles)

        return {
            "success": True,
            "plan": plan,
            "agent_id": self.agent_id
        }

    async def _handle_handoff_finding(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle handoff point finding task"""
        vehicle1 = task.get("vehicle1", {})
        vehicle2 = task.get("vehicle2", {})

        handoff_points = self.find_optimal_handoff_points(vehicle1, vehicle2)

        return {
            "success": True,
            "handoff_points": [self._handoff_to_dict(h) for h in handoff_points],
            "count": len(handoff_points),
            "agent_id": self.agent_id
        }

    async def _handle_timing_coordination(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle timing coordination task"""
        vehicle1 = task.get("vehicle1", {})
        vehicle2 = task.get("vehicle2", {})
        handoff_location = tuple(task.get("handoff_location", [0, 0]))

        coordination = self.coordinate_timing(vehicle1, vehicle2, handoff_location)

        return {
            "success": True,
            "coordination": coordination,
            "agent_id": self.agent_id
        }

    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance using Haversine formula"""
        lat1, lon1 = point1
        lat2, lon2 = point2

        R = 6371  # Earth radius in km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def _generate_handoff_points(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        num_points: int
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
            avg_speed_kmh=d.get("avg_speed_kmh", 45.0)
        )

    def _handoff_to_dict(self, handoff: HandoffPoint) -> Dict[str, Any]:
        """Convert HandoffPoint to dictionary"""
        return {
            "location": {"lat": handoff.location[0], "lon": handoff.location[1]},
            "arrival_time_vehicle1": handoff.arrival_time_vehicle1.isoformat(),
            "departure_time_vehicle2": handoff.departure_time_vehicle2.isoformat(),
            "wait_time_minutes": round(handoff.wait_time_minutes, 2),
            "quality_score": round(handoff.quality_score, 3)
        }

    def _calculate_coordination_quality(
        self,
        avg_wait: float,
        tight_handoffs: int,
        long_waits: int
    ) -> str:
        """Calculate overall coordination quality"""
        if tight_handoffs > 0 or long_waits > 2:
            return "Poor"
        elif avg_wait > 20 or long_waits > 0:
            return "Fair"
        elif avg_wait <= self.ideal_buffer_minutes:
            return "Excellent"
        else:
            return "Good"

    def _generate_handoff_recommendations(
        self,
        avg_wait: float,
        tight_handoffs: int,
        long_waits: int
    ) -> List[str]:
        """Generate handoff recommendations"""
        recommendations = []

        if tight_handoffs > 0:
            recommendations.append(f"Found {tight_handoffs} tight handoffs - increase buffer times")

        if long_waits > 0:
            recommendations.append(f"Found {long_waits} long waits - optimize vehicle scheduling")

        if avg_wait < self.min_buffer_minutes:
            recommendations.append("Average wait time too short - risk of missed connections")
        elif avg_wait > self.max_buffer_minutes:
            recommendations.append("Average wait time too long - inefficient routing")
        else:
            recommendations.append("Handoff timing is well coordinated")

        return recommendations

    def _get_timing_recommendation(self, wait_time: float) -> str:
        """Get recommendation for specific wait time"""
        if wait_time < self.min_buffer_minutes:
            return "Buffer too short - high risk of missed handoff"
        elif wait_time <= self.ideal_buffer_minutes:
            return "Optimal timing"
        elif wait_time <= self.max_buffer_minutes:
            return "Acceptable timing with some waiting"
        else:
            return "Wait time too long - consider alternative handoff point"
