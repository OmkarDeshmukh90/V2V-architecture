"""
Movement prediction for nearby vehicles
"""
import math
from typing import Tuple, List, Optional
from ..obu.vehicle_data import VehicleData


class MovementPredictor:
    """
    Predicts future positions and trajectories of vehicles.
    """
    
    @staticmethod
    def predict_position(vehicle: VehicleData, time_ahead: float) -> Tuple[float, float]:
        """
        Predict vehicle position after given time.
        
        Uses constant velocity model: position = current_position + velocity * time
        
        Args:
            vehicle: Current vehicle data
            time_ahead: Time to predict ahead in seconds
        
        Returns:
            Tuple of (predicted_latitude, predicted_longitude)
        """
        # Convert speed from km/h to m/s
        speed_ms = vehicle.speed / 3.6
        
        # Calculate velocity components
        heading_rad = math.radians(90 - vehicle.heading)
        velocity_x = speed_ms * math.cos(heading_rad)
        velocity_y = speed_ms * math.sin(heading_rad)
        
        # Predict position in meters
        delta_x = velocity_x * time_ahead
        delta_y = velocity_y * time_ahead
        
        # Convert meter offsets to lat/lon
        # Approximate: 1 degree latitude ≈ 111,000 meters
        # 1 degree longitude ≈ 111,000 * cos(latitude) meters
        lat_offset = delta_y / 111000.0
        lon_offset = delta_x / (111000.0 * math.cos(math.radians(vehicle.latitude)))
        
        predicted_lat = vehicle.latitude + lat_offset
        predicted_lon = vehicle.longitude + lon_offset
        
        return predicted_lat, predicted_lon
    
    @staticmethod
    def predict_trajectory(vehicle: VehicleData, time_horizon: float, 
                          time_step: float = 0.5) -> List[Tuple[float, float, float]]:
        """
        Predict vehicle trajectory over time horizon.
        
        Args:
            vehicle: Current vehicle data
            time_horizon: Total time to predict (seconds)
            time_step: Time step for predictions (seconds)
        
        Returns:
            List of (time, latitude, longitude) tuples
        """
        trajectory = []
        current_time = 0.0
        
        while current_time <= time_horizon:
            lat, lon = MovementPredictor.predict_position(vehicle, current_time)
            trajectory.append((current_time, lat, lon))
            current_time += time_step
        
        return trajectory
    
    @staticmethod
    def predict_with_acceleration(vehicle: VehicleData, time_ahead: float) -> Tuple[float, float, float]:
        """
        Predict vehicle position considering acceleration.
        
        Uses: position = current_pos + velocity * time + 0.5 * acceleration * time^2
        
        Args:
            vehicle: Current vehicle data
            time_ahead: Time to predict ahead in seconds
        
        Returns:
            Tuple of (predicted_latitude, predicted_longitude, predicted_speed)
        """
        # Current velocity in m/s
        speed_ms = vehicle.speed / 3.6
        
        # Calculate velocity components
        heading_rad = math.radians(90 - vehicle.heading)
        velocity_x = speed_ms * math.cos(heading_rad)
        velocity_y = speed_ms * math.sin(heading_rad)
        
        # Calculate acceleration components (assuming acceleration is along heading)
        accel_x = vehicle.acceleration * math.cos(heading_rad)
        accel_y = vehicle.acceleration * math.sin(heading_rad)
        
        # Predict position with acceleration
        delta_x = velocity_x * time_ahead + 0.5 * accel_x * time_ahead ** 2
        delta_y = velocity_y * time_ahead + 0.5 * accel_y * time_ahead ** 2
        
        # Convert to lat/lon
        lat_offset = delta_y / 111000.0
        lon_offset = delta_x / (111000.0 * math.cos(math.radians(vehicle.latitude)))
        
        predicted_lat = vehicle.latitude + lat_offset
        predicted_lon = vehicle.longitude + lon_offset
        
        # Predict speed
        predicted_speed_ms = speed_ms + vehicle.acceleration * time_ahead
        predicted_speed_kmh = max(0, predicted_speed_ms * 3.6)  # Can't be negative
        
        return predicted_lat, predicted_lon, predicted_speed_kmh
    
    @staticmethod
    def calculate_relative_velocity(vehicle1: VehicleData, vehicle2: VehicleData) -> Tuple[float, float]:
        """
        Calculate relative velocity between two vehicles.
        
        Args:
            vehicle1: First vehicle
            vehicle2: Second vehicle
        
        Returns:
            Tuple of (relative_velocity_x, relative_velocity_y) in m/s
        """
        # Calculate velocity components for both vehicles
        speed1_ms = vehicle1.speed / 3.6
        heading1_rad = math.radians(90 - vehicle1.heading)
        v1_x = speed1_ms * math.cos(heading1_rad)
        v1_y = speed1_ms * math.sin(heading1_rad)
        
        speed2_ms = vehicle2.speed / 3.6
        heading2_rad = math.radians(90 - vehicle2.heading)
        v2_x = speed2_ms * math.cos(heading2_rad)
        v2_y = speed2_ms * math.sin(heading2_rad)
        
        # Relative velocity
        rel_v_x = v2_x - v1_x
        rel_v_y = v2_y - v1_y
        
        return rel_v_x, rel_v_y
    
    @staticmethod
    def are_paths_converging(vehicle1: VehicleData, vehicle2: VehicleData) -> bool:
        """
        Check if two vehicles' paths are converging (getting closer).
        
        Args:
            vehicle1: First vehicle
            vehicle2: Second vehicle
        
        Returns:
            True if paths are converging, False otherwise
        """
        # Calculate relative velocity
        rel_v_x, rel_v_y = MovementPredictor.calculate_relative_velocity(vehicle1, vehicle2)
        
        # Calculate position difference
        dx = (vehicle2.longitude - vehicle1.longitude) * 111000.0 * math.cos(math.radians(vehicle1.latitude))
        dy = (vehicle2.latitude - vehicle1.latitude) * 111000.0
        
        # Dot product of relative velocity and position difference
        # If negative, vehicles are getting closer
        dot_product = rel_v_x * dx + rel_v_y * dy
        
        return dot_product < 0
