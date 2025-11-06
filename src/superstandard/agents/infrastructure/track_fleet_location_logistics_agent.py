"""
TrackFleetLocationLogisticsAgent - APQC 4.5.5
Real-time Fleet Tracking and Geospatial Analytics
APQC ID: apqc_4_5_t1r2a3c4

GPS tracking, geofencing, and location analytics for ride-sharing fleets.
"""

import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from math import radians, sin, cos, sqrt, atan2

from library.core.base_agent import BaseAgent
from library.core.protocols import ProtocolMixin


@dataclass
class TrackFleetLocationLogisticsAgentConfig:
    apqc_agent_id: str = "apqc_4_5_t1r2a3c4"
    apqc_process_id: str = "4.5.5"
    agent_name: str = "track_fleet_location_logistics_agent"
    agent_type: str = "operational"
    version: str = "1.0.0"


class TrackFleetLocationLogisticsAgent(BaseAgent, ProtocolMixin):
    """
    APQC 4.5.5 - Track Fleet Locations

    Skills:
    - geospatial_analytics: 0.93 (location intelligence)
    - proximity_detection: 0.90 (nearby vehicle identification)
    - path_tracking: 0.88 (route adherence monitoring)
    - geofencing: 0.86 (boundary violation detection)
    """

    VERSION = "1.0.0"
    APQC_PROCESS_ID = "4.5.5"

    def __init__(self, config: TrackFleetLocationLogisticsAgentConfig):
        super().__init__(
            agent_id=config.apqc_agent_id, agent_type=config.agent_type, version=config.version
        )
        self.config = config
        self.skills = {
            "geospatial_analytics": 0.93,
            "proximity_detection": 0.90,
            "path_tracking": 0.88,
            "geofencing": 0.86,
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track fleet locations and analyze geospatial patterns

        Input:
        {
            "vehicles": [
                {
                    "vehicle_id": "VEH001",
                    "driver_id": "DRV001",
                    "location": {"lat": 37.7749, "lng": -122.4194, "timestamp": "2025-10-18T14:30:00"},
                    "status": "on_trip",
                    "speed_kmh": 45,
                    "heading": 90
                }
            ],
            "geofences": [
                {
                    "zone_id": "ZONE_DOWNTOWN",
                    "center": {"lat": 37.7749, "lng": -122.4194},
                    "radius_km": 5,
                    "type": "service_area"
                }
            ],
            "tracking_period_minutes": 60
        }
        """
        vehicles = input_data.get("vehicles", [])
        geofences = input_data.get("geofences", [])
        tracking_period = input_data.get("tracking_period_minutes", 60)

        # Analyze fleet distribution
        distribution_analysis = self._analyze_fleet_distribution(vehicles, geofences)

        # Detect proximity clusters
        proximity_clusters = self._detect_proximity_clusters(vehicles)

        # Check geofence violations
        geofence_status = self._check_geofences(vehicles, geofences)

        # Calculate fleet coverage
        coverage_analysis = self._analyze_coverage(vehicles, geofences)

        # Generate heat map data
        heat_map = self._generate_heat_map(vehicles)

        return {
            "status": "completed",
            "apqc_process_id": self.APQC_PROCESS_ID,
            "timestamp": datetime.now().isoformat(),
            "output": {
                "fleet_distribution": distribution_analysis,
                "proximity_clusters": proximity_clusters,
                "geofence_status": geofence_status,
                "coverage_analysis": coverage_analysis,
                "heat_map_data": heat_map,
                "tracking_metrics": {
                    "total_vehicles_tracked": len(vehicles),
                    "active_vehicles": sum(1 for v in vehicles if v["status"] == "on_trip"),
                    "average_speed_kmh": round(
                        np.mean([v.get("speed_kmh", 0) for v in vehicles]), 1
                    ),
                    "tracking_period_minutes": tracking_period,
                },
            },
        }

    def _analyze_fleet_distribution(
        self, vehicles: List[Dict], geofences: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze how fleet is distributed across service areas"""
        distribution = {}

        for geofence in geofences:
            zone_id = geofence["zone_id"]
            vehicles_in_zone = 0

            for vehicle in vehicles:
                if self._is_in_geofence(vehicle["location"], geofence):
                    vehicles_in_zone += 1

            distribution[zone_id] = {
                "vehicle_count": vehicles_in_zone,
                "zone_type": geofence["type"],
                "coverage_percentage": (
                    round((vehicles_in_zone / len(vehicles) * 100), 1) if vehicles else 0
                ),
            }

        return distribution

    def _is_in_geofence(self, location: Dict, geofence: Dict) -> bool:
        """Check if location is within geofence"""
        distance = self._haversine_distance(
            location["lat"], location["lng"], geofence["center"]["lat"], geofence["center"]["lng"]
        )
        return distance <= geofence["radius_km"]

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in km"""
        R = 6371
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)
        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _detect_proximity_clusters(self, vehicles: List[Dict]) -> List[Dict[str, Any]]:
        """Detect clusters of nearby vehicles"""
        clusters = []
        cluster_threshold_km = 1.0  # Vehicles within 1km are in same cluster

        processed = set()

        for i, vehicle in enumerate(vehicles):
            if i in processed:
                continue

            cluster_vehicles = [vehicle["vehicle_id"]]
            cluster_center_lat = [vehicle["location"]["lat"]]
            cluster_center_lng = [vehicle["location"]["lng"]]

            for j, other_vehicle in enumerate(vehicles):
                if i == j or j in processed:
                    continue

                distance = self._haversine_distance(
                    vehicle["location"]["lat"],
                    vehicle["location"]["lng"],
                    other_vehicle["location"]["lat"],
                    other_vehicle["location"]["lng"],
                )

                if distance <= cluster_threshold_km:
                    cluster_vehicles.append(other_vehicle["vehicle_id"])
                    cluster_center_lat.append(other_vehicle["location"]["lat"])
                    cluster_center_lng.append(other_vehicle["location"]["lng"])
                    processed.add(j)

            if len(cluster_vehicles) >= 2:  # Only report clusters with 2+ vehicles
                clusters.append(
                    {
                        "cluster_id": f"CLUSTER_{len(clusters) + 1}",
                        "vehicle_count": len(cluster_vehicles),
                        "vehicle_ids": cluster_vehicles,
                        "center_location": {
                            "lat": round(np.mean(cluster_center_lat), 6),
                            "lng": round(np.mean(cluster_center_lng), 6),
                        },
                        "density": "high" if len(cluster_vehicles) > 5 else "medium",
                    }
                )

            processed.add(i)

        return clusters

    def _check_geofences(self, vehicles: List[Dict], geofences: List[Dict]) -> Dict[str, Any]:
        """Check geofence compliance"""
        violations = []
        compliant_count = 0

        for vehicle in vehicles:
            in_any_zone = False

            for geofence in geofences:
                if self._is_in_geofence(vehicle["location"], geofence):
                    in_any_zone = True
                    break

            if not in_any_zone and geofences:  # Outside all service areas
                violations.append(
                    {
                        "vehicle_id": vehicle["vehicle_id"],
                        "driver_id": vehicle.get("driver_id"),
                        "location": vehicle["location"],
                        "violation_type": "outside_service_area",
                        "detected_at": datetime.now().isoformat(),
                    }
                )
            else:
                compliant_count += 1

        return {
            "total_vehicles": len(vehicles),
            "compliant_vehicles": compliant_count,
            "violations": violations,
            "violation_count": len(violations),
            "compliance_rate": round(compliant_count / len(vehicles), 2) if vehicles else 1.0,
        }

    def _analyze_coverage(self, vehicles: List[Dict], geofences: List[Dict]) -> Dict[str, Any]:
        """Analyze service area coverage"""
        if not geofences:
            return {"coverage_status": "no_geofences_defined"}

        coverage_per_zone = {}

        for geofence in geofences:
            zone_id = geofence["zone_id"]
            vehicles_in_zone = sum(
                1 for v in vehicles if self._is_in_geofence(v["location"], geofence)
            )

            # Calculate coverage score (vehicles per km²)
            area_km2 = 3.14159 * (geofence["radius_km"] ** 2)
            density = vehicles_in_zone / area_km2 if area_km2 > 0 else 0

            if density >= 0.5:
                coverage_level = "excellent"
            elif density >= 0.3:
                coverage_level = "good"
            elif density >= 0.1:
                coverage_level = "fair"
            else:
                coverage_level = "poor"

            coverage_per_zone[zone_id] = {
                "vehicle_count": vehicles_in_zone,
                "area_km2": round(area_km2, 2),
                "density": round(density, 3),
                "coverage_level": coverage_level,
            }

        # Overall coverage score
        avg_density = np.mean([z["density"] for z in coverage_per_zone.values()])

        return {
            "zones": coverage_per_zone,
            "average_density": round(avg_density, 3),
            "coverage_status": "optimal" if avg_density >= 0.3 else "needs_improvement",
        }

    def _generate_heat_map(self, vehicles: List[Dict]) -> Dict[str, Any]:
        """Generate heat map data for visualization"""
        if not vehicles:
            return {"points": []}

        # Create heat map points
        heat_points = []

        for vehicle in vehicles:
            intensity = 1.0
            if vehicle["status"] == "on_trip":
                intensity = 1.5
            elif vehicle["status"] == "idle":
                intensity = 0.5

            heat_points.append(
                {
                    "lat": vehicle["location"]["lat"],
                    "lng": vehicle["location"]["lng"],
                    "intensity": intensity,
                    "timestamp": vehicle["location"].get("timestamp", datetime.now().isoformat()),
                }
            )

        # Calculate bounding box
        lats = [p["lat"] for p in heat_points]
        lngs = [p["lng"] for p in heat_points]

        return {
            "points": heat_points,
            "bounding_box": {
                "north": max(lats),
                "south": min(lats),
                "east": max(lngs),
                "west": min(lngs),
            },
            "point_count": len(heat_points),
        }

    def get_input_schema(self) -> Dict[str, Any]:
        """Return input schema"""
        return {
            "type": "object",
            "required": ["vehicles"],
            "properties": {
                "vehicles": {"type": "array"},
                "geofences": {"type": "array"},
                "tracking_period_minutes": {"type": "number"},
            },
        }

    def get_output_schema(self) -> Dict[str, Any]:
        """Return output schema"""
        return {
            "type": "object",
            "properties": {
                "fleet_distribution": {"type": "object"},
                "proximity_clusters": {"type": "array"},
                "geofence_status": {"type": "object"},
                "coverage_analysis": {"type": "object"},
                "heat_map_data": {"type": "object"},
            },
        }


def create_track_fleet_location_logistics_agent() -> TrackFleetLocationLogisticsAgent:
    """Factory function"""
    config = TrackFleetLocationLogisticsAgentConfig()
    return TrackFleetLocationLogisticsAgent(config)
