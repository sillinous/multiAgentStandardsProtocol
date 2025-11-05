"""
Matching Optimization Agent for Mobility Routing Swarm

Optimizes rider-driver matching using wait time, distance, and vehicle occupancy.
"""

from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
import math

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from agents.base_agent import BaseAgent, AgentCapability


@dataclass
class Rider:
    """Rider information"""
    id: str
    location: Tuple[float, float]
    destination: Tuple[float, float]
    request_time: datetime
    max_wait_minutes: float = 10.0
    passengers: int = 1


@dataclass
class Driver:
    """Driver information"""
    id: str
    location: Tuple[float, float]
    capacity: int
    current_occupancy: int = 0
    available: bool = True
    current_route: Optional[List[Tuple[float, float]]] = None


@dataclass
class Match:
    """Rider-driver match"""
    rider_id: str
    driver_id: str
    quality_score: float
    wait_time_minutes: float
    pickup_distance_km: float
    details: Dict[str, Any]


class MatchingOptimizationAgent(BaseAgent):
    """
    Agent responsible for optimizing rider-driver matching.
    Uses weighted scoring: wait time (40%), distance (30%), occupancy (30%)
    """

    def __init__(self, agent_id: str = "matching_optimization_agent", workspace_path: str = "./autonomous-ecosystem/workspace"):
        super().__init__(
            agent_id=agent_id,
            agent_type="matching_optimization",
            capabilities=[AgentCapability.ORCHESTRATION],
            workspace_path=workspace_path
        )

        # Scoring weights
        self.weight_wait_time = 0.40
        self.weight_distance = 0.30
        self.weight_occupancy = 0.30

        # Average speed for ETA calculation (km/h)
        self.avg_speed = 35.0

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute matching optimization task

        Args:
            task: Task with 'action' and parameters

        Returns:
            Task execution result
        """
        action = task.get("action")

        if action == "find_matches":
            return await self._handle_find_matches(task)
        elif action == "optimize_multi_rider":
            return await self._handle_multi_rider_optimization(task)
        elif action == "calculate_match_quality":
            return await self._handle_match_quality(task)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }

    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze matching patterns and efficiency

        Args:
            input_data: Matching data to analyze

        Returns:
            Analysis results with metrics and recommendations
        """
        matches = input_data.get("matches", [])

        if not matches:
            return {
                "timestamp": datetime.now().isoformat(),
                "total_matches": 0,
                "average_quality": 0.0,
                "recommendations": ["No matches to analyze"]
            }

        # Calculate metrics
        total_quality = sum(m.get("quality_score", 0) for m in matches)
        avg_quality = total_quality / len(matches)
        avg_wait = sum(m.get("wait_time_minutes", 0) for m in matches) / len(matches)
        avg_distance = sum(m.get("pickup_distance_km", 0) for m in matches) / len(matches)

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_matches": len(matches),
            "average_quality": round(avg_quality, 3),
            "average_wait_minutes": round(avg_wait, 2),
            "average_pickup_distance_km": round(avg_distance, 2),
            "efficiency_rating": self._calculate_efficiency_rating(avg_quality),
            "recommendations": self._generate_matching_recommendations(avg_quality, avg_wait, avg_distance)
        }

        return analysis

    def find_best_matches(
        self,
        riders: List[Dict[str, Any]],
        drivers: List[Dict[str, Any]]
    ) -> List[Match]:
        """
        Find optimal rider-driver matches

        Args:
            riders: List of rider dictionaries
            drivers: List of driver dictionaries

        Returns:
            List of Match objects sorted by quality score
        """
        # Convert dicts to objects
        rider_objects = [self._dict_to_rider(r) for r in riders]
        driver_objects = [self._dict_to_driver(d) for d in drivers]

        all_matches = []

        # Calculate quality for all possible pairings
        for rider in rider_objects:
            for driver in driver_objects:
                if not driver.available:
                    continue

                if driver.current_occupancy + rider.passengers > driver.capacity:
                    continue

                quality_score, details = self.calculate_match_quality(rider, driver)

                if quality_score > 0:
                    match = Match(
                        rider_id=rider.id,
                        driver_id=driver.id,
                        quality_score=quality_score,
                        wait_time_minutes=details["wait_time_minutes"],
                        pickup_distance_km=details["pickup_distance_km"],
                        details=details
                    )
                    all_matches.append(match)

        # Sort by quality score (descending)
        all_matches.sort(key=lambda m: m.quality_score, reverse=True)

        # Select best matches without duplicates
        selected_matches = []
        matched_riders = set()
        matched_drivers = set()

        for match in all_matches:
            if match.rider_id not in matched_riders and match.driver_id not in matched_drivers:
                selected_matches.append(match)
                matched_riders.add(match.rider_id)
                matched_drivers.add(match.driver_id)

        return selected_matches

    def calculate_match_quality(
        self,
        rider: Rider,
        driver: Driver
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate quality score for a rider-driver match

        Args:
            rider: Rider object
            driver: Driver object

        Returns:
            Tuple of (quality_score, details_dict)
        """
        # Calculate pickup distance
        pickup_distance = self._calculate_distance(driver.location, rider.location)

        # Calculate wait time
        wait_time_minutes = (pickup_distance / self.avg_speed) * 60

        # Score components (0-1 scale, higher is better)

        # Wait time score: penalize long waits
        max_acceptable_wait = rider.max_wait_minutes
        if wait_time_minutes > max_acceptable_wait:
            wait_score = 0.0
        else:
            wait_score = 1.0 - (wait_time_minutes / max_acceptable_wait)

        # Distance score: penalize long pickup distances
        max_acceptable_distance = 5.0  # km
        if pickup_distance > max_acceptable_distance:
            distance_score = 0.0
        else:
            distance_score = 1.0 - (pickup_distance / max_acceptable_distance)

        # Occupancy score: prefer efficient vehicle utilization
        remaining_capacity = driver.capacity - driver.current_occupancy
        if remaining_capacity >= rider.passengers:
            # Higher score if we're filling the vehicle efficiently
            utilization = (driver.current_occupancy + rider.passengers) / driver.capacity
            occupancy_score = utilization
        else:
            occupancy_score = 0.0

        # Weighted total score
        total_score = (
            self.weight_wait_time * wait_score +
            self.weight_distance * distance_score +
            self.weight_occupancy * occupancy_score
        )

        details = {
            "wait_time_minutes": round(wait_time_minutes, 2),
            "pickup_distance_km": round(pickup_distance, 2),
            "wait_score": round(wait_score, 3),
            "distance_score": round(distance_score, 3),
            "occupancy_score": round(occupancy_score, 3),
            "vehicle_utilization": round((driver.current_occupancy + rider.passengers) / driver.capacity, 2),
            "total_score": round(total_score, 3)
        }

        return total_score, details

    def optimize_multi_rider_routes(
        self,
        driver: Dict[str, Any],
        riders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Optimize route for picking up multiple riders

        Args:
            driver: Driver dictionary
            riders: List of rider dictionaries to pick up

        Returns:
            Optimized route plan
        """
        driver_obj = self._dict_to_driver(driver)
        rider_objects = [self._dict_to_rider(r) for r in riders]

        # Check capacity
        total_passengers = sum(r.passengers for r in rider_objects)
        if total_passengers > driver_obj.capacity:
            return {
                "success": False,
                "error": "Capacity exceeded",
                "capacity": driver_obj.capacity,
                "requested": total_passengers
            }

        # Simple greedy approach: pick up closest riders first
        current_location = driver_obj.location
        route = [current_location]
        pickup_sequence = []
        remaining_riders = rider_objects.copy()
        total_distance = 0.0
        total_time = 0.0

        while remaining_riders:
            # Find closest rider
            closest_rider = min(
                remaining_riders,
                key=lambda r: self._calculate_distance(current_location, r.location)
            )

            pickup_distance = self._calculate_distance(current_location, closest_rider.location)
            pickup_time = (pickup_distance / self.avg_speed) * 60

            route.append(closest_rider.location)
            pickup_sequence.append({
                "rider_id": closest_rider.id,
                "pickup_location": closest_rider.location,
                "distance_from_previous": round(pickup_distance, 2),
                "time_from_previous_minutes": round(pickup_time, 2)
            })

            total_distance += pickup_distance
            total_time += pickup_time

            current_location = closest_rider.location
            remaining_riders.remove(closest_rider)

        return {
            "success": True,
            "driver_id": driver_obj.id,
            "pickup_sequence": pickup_sequence,
            "total_pickup_distance_km": round(total_distance, 2),
            "total_pickup_time_minutes": round(total_time, 2),
            "total_riders": len(rider_objects),
            "route": route
        }

    async def _handle_find_matches(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle find best matches task"""
        riders = task.get("riders", [])
        drivers = task.get("drivers", [])

        matches = self.find_best_matches(riders, drivers)

        return {
            "success": True,
            "matches": [self._match_to_dict(m) for m in matches],
            "count": len(matches),
            "agent_id": self.agent_id
        }

    async def _handle_multi_rider_optimization(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle multi-rider route optimization task"""
        driver = task.get("driver", {})
        riders = task.get("riders", [])

        result = self.optimize_multi_rider_routes(driver, riders)
        result["agent_id"] = self.agent_id

        return result

    async def _handle_match_quality(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle match quality calculation task"""
        rider_dict = task.get("rider", {})
        driver_dict = task.get("driver", {})

        rider = self._dict_to_rider(rider_dict)
        driver = self._dict_to_driver(driver_dict)

        quality_score, details = self.calculate_match_quality(rider, driver)

        return {
            "success": True,
            "quality_score": quality_score,
            "details": details,
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

    def _dict_to_rider(self, d: Dict[str, Any]) -> Rider:
        """Convert dictionary to Rider object"""
        request_time = d.get("request_time", datetime.now())
        if isinstance(request_time, str):
            request_time = datetime.fromisoformat(request_time)

        return Rider(
            id=d["id"],
            location=tuple(d["location"]),
            destination=tuple(d["destination"]),
            request_time=request_time,
            max_wait_minutes=d.get("max_wait_minutes", 10.0),
            passengers=d.get("passengers", 1)
        )

    def _dict_to_driver(self, d: Dict[str, Any]) -> Driver:
        """Convert dictionary to Driver object"""
        return Driver(
            id=d["id"],
            location=tuple(d["location"]),
            capacity=d.get("capacity", 4),
            current_occupancy=d.get("current_occupancy", 0),
            available=d.get("available", True),
            current_route=d.get("current_route")
        )

    def _match_to_dict(self, match: Match) -> Dict[str, Any]:
        """Convert Match object to dictionary"""
        return {
            "rider_id": match.rider_id,
            "driver_id": match.driver_id,
            "quality_score": match.quality_score,
            "wait_time_minutes": match.wait_time_minutes,
            "pickup_distance_km": match.pickup_distance_km,
            "details": match.details
        }

    def _calculate_efficiency_rating(self, avg_quality: float) -> str:
        """Calculate efficiency rating from average quality"""
        if avg_quality >= 0.8:
            return "Excellent"
        elif avg_quality >= 0.6:
            return "Good"
        elif avg_quality >= 0.4:
            return "Fair"
        else:
            return "Poor"

    def _generate_matching_recommendations(
        self,
        avg_quality: float,
        avg_wait: float,
        avg_distance: float
    ) -> List[str]:
        """Generate recommendations for matching optimization"""
        recommendations = []

        if avg_quality < 0.5:
            recommendations.append("Consider expanding driver pool or reducing service area")

        if avg_wait > 8.0:
            recommendations.append("Wait times are high - increase driver availability in busy areas")

        if avg_distance > 3.0:
            recommendations.append("Pickup distances are long - optimize driver positioning")

        if not recommendations:
            recommendations.append("Matching efficiency is optimal")

        return recommendations
