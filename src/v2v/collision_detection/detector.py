"""
Collision detection and avoidance system
"""
import math
import time
from typing import Dict, List, Tuple, Optional, Callable
from enum import Enum
from ..obu.vehicle_data import VehicleData
from .predictor import MovementPredictor


class CollisionRiskLevel(Enum):
    """Risk levels for collision scenarios"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class CollisionWarning:
    """Represents a collision warning for a specific vehicle"""
    
    def __init__(self, target_vehicle_id: str, risk_level: CollisionRiskLevel,
                 time_to_collision: float, distance: float,
                 relative_speed: float, recommendation: str):
        """
        Initialize collision warning.
        
        Args:
            target_vehicle_id: ID of the vehicle posing collision risk
            risk_level: Risk level of collision
            time_to_collision: Estimated time to collision in seconds
            distance: Current distance to target vehicle in meters
            relative_speed: Relative speed in m/s
            recommendation: Recommended action
        """
        self.target_vehicle_id = target_vehicle_id
        self.risk_level = risk_level
        self.time_to_collision = time_to_collision
        self.distance = distance
        self.relative_speed = relative_speed
        self.recommendation = recommendation
        self.timestamp = time.time()
    
    def __repr__(self):
        return (f"CollisionWarning(target={self.target_vehicle_id}, "
                f"risk={self.risk_level.name}, ttc={self.time_to_collision:.2f}s)")


class CollisionDetector:
    """
    Detects potential collisions and generates warnings.
    """
    
    def __init__(self, ttc_threshold: float = 3.0,
                 critical_ttc_threshold: float = 1.5,
                 min_safe_distance: float = 5.0,
                 prediction_horizon: float = 5.0):
        """
        Initialize collision detector.
        
        Args:
            ttc_threshold: Time-to-collision threshold for warnings (seconds)
            critical_ttc_threshold: Critical TTC threshold (seconds)
            min_safe_distance: Minimum safe distance (meters)
            prediction_horizon: How far ahead to predict (seconds)
        """
        self.ttc_threshold = ttc_threshold
        self.critical_ttc_threshold = critical_ttc_threshold
        self.min_safe_distance = min_safe_distance
        self.prediction_horizon = prediction_horizon
        
        self.predictor = MovementPredictor()
    
    def calculate_distance(self, vehicle1: VehicleData, vehicle2: VehicleData) -> float:
        """
        Calculate distance between two vehicles using Haversine formula.
        
        Args:
            vehicle1: First vehicle
            vehicle2: Second vehicle
        
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth's radius in meters
        
        lat1 = math.radians(vehicle1.latitude)
        lat2 = math.radians(vehicle2.latitude)
        dlat = lat2 - lat1
        dlon = math.radians(vehicle2.longitude - vehicle1.longitude)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def calculate_time_to_collision(self, own_vehicle: VehicleData, 
                                    other_vehicle: VehicleData) -> Optional[float]:
        """
        Calculate time to collision between two vehicles.
        
        Args:
            own_vehicle: Own vehicle data
            other_vehicle: Other vehicle data
        
        Returns:
            Time to collision in seconds, or None if no collision predicted
        """
        # Get current distance
        current_distance = self.calculate_distance(own_vehicle, other_vehicle)
        
        # Calculate relative velocity
        rel_v_x, rel_v_y = self.predictor.calculate_relative_velocity(own_vehicle, other_vehicle)
        relative_speed = math.sqrt(rel_v_x ** 2 + rel_v_y ** 2)
        
        # Check if paths are converging
        if not self.predictor.are_paths_converging(own_vehicle, other_vehicle):
            return None  # Paths are diverging
        
        # Calculate TTC
        if relative_speed > 0.1:  # Avoid division by very small numbers
            ttc = current_distance / relative_speed
            return ttc if ttc > 0 else None
        
        return None
    
    def assess_collision_risk(self, own_vehicle: VehicleData,
                             other_vehicle: VehicleData) -> Tuple[CollisionRiskLevel, Optional[float]]:
        """
        Assess collision risk with another vehicle.
        
        Args:
            own_vehicle: Own vehicle data
            other_vehicle: Other vehicle data
        
        Returns:
            Tuple of (risk_level, time_to_collision)
        """
        # Calculate current distance
        distance = self.calculate_distance(own_vehicle, other_vehicle)
        
        # Check minimum safe distance
        if distance < self.min_safe_distance:
            return CollisionRiskLevel.CRITICAL, 0.0
        
        # Calculate TTC
        ttc = self.calculate_time_to_collision(own_vehicle, other_vehicle)
        
        if ttc is None:
            return CollisionRiskLevel.NONE, None
        
        # Assess risk based on TTC
        if ttc <= self.critical_ttc_threshold:
            return CollisionRiskLevel.CRITICAL, ttc
        elif ttc <= self.ttc_threshold:
            if ttc <= 2.0:
                return CollisionRiskLevel.HIGH, ttc
            else:
                return CollisionRiskLevel.MEDIUM, ttc
        else:
            return CollisionRiskLevel.LOW, ttc
    
    def detect_collisions(self, own_vehicle: VehicleData,
                         nearby_vehicles: Dict[str, VehicleData]) -> List[CollisionWarning]:
        """
        Detect potential collisions with all nearby vehicles.
        
        Args:
            own_vehicle: Own vehicle data
            nearby_vehicles: Dictionary of nearby vehicles
        
        Returns:
            List of collision warnings
        """
        warnings = []
        
        for vehicle_id, other_vehicle in nearby_vehicles.items():
            risk_level, ttc = self.assess_collision_risk(own_vehicle, other_vehicle)
            
            if risk_level != CollisionRiskLevel.NONE and ttc is not None:
                distance = self.calculate_distance(own_vehicle, other_vehicle)
                
                # Calculate relative speed
                rel_v_x, rel_v_y = self.predictor.calculate_relative_velocity(
                    own_vehicle, other_vehicle
                )
                relative_speed = math.sqrt(rel_v_x ** 2 + rel_v_y ** 2)
                
                # Generate recommendation
                recommendation = self._generate_recommendation(risk_level, ttc, other_vehicle)
                
                warning = CollisionWarning(
                    target_vehicle_id=vehicle_id,
                    risk_level=risk_level,
                    time_to_collision=ttc,
                    distance=distance,
                    relative_speed=relative_speed,
                    recommendation=recommendation
                )
                
                warnings.append(warning)
        
        # Sort by risk level (highest first) and then by TTC
        warnings.sort(key=lambda w: (w.risk_level.value, w.time_to_collision), reverse=True)
        
        return warnings
    
    def _generate_recommendation(self, risk_level: CollisionRiskLevel,
                                ttc: float, other_vehicle: VehicleData) -> str:
        """Generate collision avoidance recommendation"""
        if risk_level == CollisionRiskLevel.CRITICAL:
            return "EMERGENCY BRAKE! Collision imminent!"
        elif risk_level == CollisionRiskLevel.HIGH:
            if other_vehicle.is_braking:
                return "Vehicle ahead braking! Reduce speed immediately!"
            else:
                return "High collision risk! Apply brakes and prepare to maneuver!"
        elif risk_level == CollisionRiskLevel.MEDIUM:
            return "Moderate collision risk. Reduce speed and increase following distance."
        else:
            return "Low collision risk. Monitor situation and maintain safe distance."


class CollisionAvoidanceSystem:
    """
    Complete collision avoidance system integrating detection and decision making.
    """
    
    def __init__(self, own_vehicle: VehicleData, detector: CollisionDetector):
        """
        Initialize collision avoidance system.
        
        Args:
            own_vehicle: Own vehicle data
            detector: Collision detector instance
        """
        self.own_vehicle = own_vehicle
        self.detector = detector
        
        # Active warnings
        self.active_warnings: List[CollisionWarning] = []
        
        # Callbacks
        self.on_warning_callbacks: List[Callable[[CollisionWarning], None]] = []
        self.on_critical_warning_callbacks: List[Callable[[CollisionWarning], None]] = []
    
    def update(self, own_vehicle: VehicleData, nearby_vehicles: Dict[str, VehicleData]):
        """
        Update collision avoidance system with latest data.
        
        Args:
            own_vehicle: Updated own vehicle data
            nearby_vehicles: Updated nearby vehicles data
        """
        self.own_vehicle = own_vehicle
        
        # Detect collisions
        new_warnings = self.detector.detect_collisions(own_vehicle, nearby_vehicles)
        
        # Process new warnings
        for warning in new_warnings:
            # Check if this is a new or escalated warning
            existing = self._find_warning(warning.target_vehicle_id)
            
            if existing is None or existing.risk_level.value < warning.risk_level.value:
                # New or escalated warning
                self._trigger_warning(warning)
        
        self.active_warnings = new_warnings
    
    def _find_warning(self, vehicle_id: str) -> Optional[CollisionWarning]:
        """Find existing warning for vehicle"""
        for warning in self.active_warnings:
            if warning.target_vehicle_id == vehicle_id:
                return warning
        return None
    
    def _trigger_warning(self, warning: CollisionWarning):
        """Trigger warning callbacks"""
        # General warning callbacks
        for callback in self.on_warning_callbacks:
            try:
                callback(warning)
            except Exception as e:
                print(f"Error in warning callback: {e}")
        
        # Critical warning callbacks
        if warning.risk_level == CollisionRiskLevel.CRITICAL:
            for callback in self.on_critical_warning_callbacks:
                try:
                    callback(warning)
                except Exception as e:
                    print(f"Error in critical warning callback: {e}")
    
    def register_warning_callback(self, callback: Callable[[CollisionWarning], None]):
        """Register callback for collision warnings"""
        self.on_warning_callbacks.append(callback)
    
    def register_critical_warning_callback(self, callback: Callable[[CollisionWarning], None]):
        """Register callback for critical collision warnings"""
        self.on_critical_warning_callbacks.append(callback)
    
    def get_active_warnings(self) -> List[CollisionWarning]:
        """Get all active collision warnings"""
        return list(self.active_warnings)
    
    def get_highest_risk_warning(self) -> Optional[CollisionWarning]:
        """Get the highest risk active warning"""
        if self.active_warnings:
            return self.active_warnings[0]  # Already sorted by risk
        return None
