"""
On-Board Unit (OBU) - Main class for vehicle data collection and management
"""
import time
import uuid
import math
from typing import Optional, Callable
from .vehicle_data import VehicleData, ADASData


class OBU:
    """
    On-Board Unit (OBU) for collecting and managing vehicle data.
    
    This class is responsible for:
    - Collecting GPS location data
    - Monitoring speed and acceleration
    - Tracking braking status
    - Calculating heading
    - Collecting ADAS sensor data
    - Providing current vehicle state
    """
    
    def __init__(self, vehicle_id: Optional[str] = None):
        """
        Initialize the OBU.
        
        Args:
            vehicle_id: Unique identifier for the vehicle. Auto-generated if not provided.
        """
        self.vehicle_id = vehicle_id or f"V2V_{uuid.uuid4().hex[:8]}"
        
        # Current vehicle data
        self._current_data = VehicleData(
            vehicle_id=self.vehicle_id,
            latitude=0.0,
            longitude=0.0,
        )
        
        # Previous data for calculating acceleration
        self._previous_speed = 0.0
        self._previous_timestamp = time.time()
        
        # ADAS data
        self._adas_data = ADASData()
        
        # Data update callbacks
        self._data_callbacks = []
    
    def update_gps(self, latitude: float, longitude: float, altitude: float = 0.0):
        """
        Update GPS location data.
        
        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            altitude: Altitude in meters (default: 0.0)
        """
        self._current_data.latitude = latitude
        self._current_data.longitude = longitude
        self._current_data.altitude = altitude
        self._current_data.timestamp = time.time()
    
    def update_speed(self, speed: float):
        """
        Update vehicle speed.
        
        Args:
            speed: Speed in km/h
        """
        current_time = time.time()
        time_diff = current_time - self._previous_timestamp
        
        # Calculate acceleration (change in speed / time)
        if time_diff > 0:
            # Convert speed from km/h to m/s for acceleration calculation
            speed_ms = speed / 3.6
            prev_speed_ms = self._previous_speed / 3.6
            self._current_data.acceleration = (speed_ms - prev_speed_ms) / time_diff
        
        self._current_data.speed = speed
        self._previous_speed = speed
        self._previous_timestamp = current_time
        self._current_data.timestamp = current_time
        
        # Update velocity components
        self._current_data.calculate_velocity_components()
    
    def update_heading(self, heading: float):
        """
        Update vehicle heading.
        
        Args:
            heading: Heading in degrees (0-360, North = 0, clockwise)
        """
        # Normalize heading to 0-360 range
        self._current_data.heading = heading % 360
        self._current_data.timestamp = time.time()
        
        # Update velocity components when heading changes
        self._current_data.calculate_velocity_components()
    
    def update_braking(self, is_braking: bool, braking_force: float = 0.0):
        """
        Update braking status.
        
        Args:
            is_braking: True if brakes are applied
            braking_force: Braking force from 0.0 to 1.0
        """
        self._current_data.is_braking = is_braking
        self._current_data.braking_force = max(0.0, min(1.0, braking_force))
        self._current_data.timestamp = time.time()
    
    def update_adas_data(self, adas_data: dict):
        """
        Update ADAS sensor data.
        
        Args:
            adas_data: Dictionary containing ADAS sensor data
        """
        self._current_data.adas_data = adas_data
        self._current_data.timestamp = time.time()
    
    def set_adas_radar(self, radar_objects: list):
        """Set radar detected objects"""
        self._adas_data.radar_objects = radar_objects
        self._current_data.adas_data['radar'] = radar_objects
    
    def set_adas_lidar(self, lidar_points: list):
        """Set LiDAR point cloud data"""
        self._adas_data.lidar_points = lidar_points
        self._current_data.adas_data['lidar'] = len(lidar_points)  # Store count to reduce data size
    
    def set_adas_camera(self, camera_objects: list):
        """Set camera detected objects"""
        self._adas_data.camera_objects = camera_objects
        self._current_data.adas_data['camera'] = camera_objects
    
    def set_forward_collision_warning(self, active: bool, distance: Optional[float] = None):
        """Set forward collision warning status"""
        self._adas_data.fcw_active = active
        self._adas_data.fcw_distance = distance
        self._current_data.adas_data['fcw'] = {
            'active': active,
            'distance': distance
        }
    
    def get_current_data(self) -> VehicleData:
        """
        Get current vehicle data.
        
        Returns:
            VehicleData object with current vehicle state
        """
        return self._current_data
    
    def get_broadcast_radius(self, base_radius: float = 100.0, 
                            max_radius: float = 500.0,
                            speed_factor: float = 5.0) -> float:
        """
        Calculate dynamic broadcast radius based on vehicle speed.
        
        Higher speeds require larger broadcast radius for early warning.
        
        Args:
            base_radius: Base radius in meters (default: 100.0)
            max_radius: Maximum radius in meters (default: 500.0)
            speed_factor: Speed factor for radius calculation (default: 5.0)
        
        Returns:
            Broadcast radius in meters
        """
        # radius = base_radius + (speed_kmh / speed_factor)
        dynamic_radius = base_radius + (self._current_data.speed / speed_factor)
        return min(dynamic_radius, max_radius)
    
    def register_data_callback(self, callback: Callable[[VehicleData], None]):
        """
        Register a callback to be called when data is updated.
        
        Args:
            callback: Function to call with VehicleData when updated
        """
        self._data_callbacks.append(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks of data update"""
        for callback in self._data_callbacks:
            try:
                callback(self._current_data)
            except Exception as e:
                print(f"Error in data callback: {e}")
    
    def calculate_distance_to(self, other_vehicle: VehicleData) -> float:
        """
        Calculate distance to another vehicle using Haversine formula.
        
        Args:
            other_vehicle: VehicleData of another vehicle
        
        Returns:
            Distance in meters
        """
        # Haversine formula for distance between two GPS coordinates
        R = 6371000  # Earth's radius in meters
        
        lat1 = math.radians(self._current_data.latitude)
        lat2 = math.radians(other_vehicle.latitude)
        dlat = lat2 - lat1
        dlon = math.radians(other_vehicle.longitude - self._current_data.longitude)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def __repr__(self):
        return (f"OBU(vehicle_id={self.vehicle_id}, "
                f"speed={self._current_data.speed:.1f} km/h, "
                f"heading={self._current_data.heading:.1f}°)")
