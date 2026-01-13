"""
Vehicle data models for V2V communication
"""
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class VehicleData:
    """Complete vehicle data structure for V2V communication"""
    
    # Vehicle identification
    vehicle_id: str
    
    # GPS data
    latitude: float  # degrees
    longitude: float  # degrees
    altitude: float = 0.0  # meters
    
    # Motion data
    speed: float = 0.0  # km/h
    acceleration: float = 0.0  # m/s^2
    heading: float = 0.0  # degrees (0-360, North = 0, clockwise)
    
    # Vehicle state
    is_braking: bool = False
    braking_force: float = 0.0  # 0.0 to 1.0
    
    # ADAS sensor data
    adas_data: Dict[str, any] = field(default_factory=dict)
    
    # Timestamp
    timestamp: float = field(default_factory=time.time)
    
    # Derived data
    velocity_x: float = 0.0  # m/s in x direction
    velocity_y: float = 0.0  # m/s in y direction
    
    def to_dict(self) -> dict:
        """Convert vehicle data to dictionary for serialization"""
        return {
            'vehicle_id': self.vehicle_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'speed': self.speed,
            'acceleration': self.acceleration,
            'heading': self.heading,
            'is_braking': self.is_braking,
            'braking_force': self.braking_force,
            'adas_data': self.adas_data,
            'timestamp': self.timestamp,
            'velocity_x': self.velocity_x,
            'velocity_y': self.velocity_y,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VehicleData':
        """Create VehicleData from dictionary"""
        return cls(
            vehicle_id=data['vehicle_id'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            altitude=data.get('altitude', 0.0),
            speed=data['speed'],
            acceleration=data['acceleration'],
            heading=data['heading'],
            is_braking=data['is_braking'],
            braking_force=data.get('braking_force', 0.0),
            adas_data=data.get('adas_data', {}),
            timestamp=data['timestamp'],
            velocity_x=data.get('velocity_x', 0.0),
            velocity_y=data.get('velocity_y', 0.0),
        )
    
    def calculate_velocity_components(self):
        """Calculate velocity components based on speed and heading"""
        import math
        # Convert speed from km/h to m/s
        speed_ms = self.speed / 3.6
        # Convert heading to radians (0 degrees = North, clockwise)
        # In standard coords: 0 degrees = East, counter-clockwise
        # So we need to convert: standard_angle = 90 - heading
        heading_rad = math.radians(90 - self.heading)
        self.velocity_x = speed_ms * math.cos(heading_rad)
        self.velocity_y = speed_ms * math.sin(heading_rad)


@dataclass
class ADASData:
    """ADAS (Advanced Driver Assistance Systems) sensor data"""
    
    # Radar data
    radar_objects: list = field(default_factory=list)  # Detected objects
    
    # LiDAR data
    lidar_points: list = field(default_factory=list)  # Point cloud data
    
    # Camera data
    camera_objects: list = field(default_factory=list)  # Detected objects from camera
    
    # Lane detection
    lane_departure_warning: bool = False
    
    # Forward collision warning
    fcw_active: bool = False
    fcw_distance: Optional[float] = None  # meters to object
    
    def to_dict(self) -> dict:
        """Convert ADAS data to dictionary"""
        return {
            'radar_objects': self.radar_objects,
            'lidar_points': self.lidar_points,
            'camera_objects': self.camera_objects,
            'lane_departure_warning': self.lane_departure_warning,
            'fcw_active': self.fcw_active,
            'fcw_distance': self.fcw_distance,
        }
