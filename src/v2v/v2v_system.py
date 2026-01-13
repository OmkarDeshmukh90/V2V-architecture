"""
Main V2V System - Integrates all components
"""
import time
from typing import Optional, Callable
from .obu.obu import OBU
from .obu.vehicle_data import VehicleData
from .communication.broadcaster import V2VBroadcaster
from .communication.receiver import V2VReceiver
from .collision_detection.detector import CollisionDetector, CollisionAvoidanceSystem, CollisionWarning
from .utils.config import Config
from .utils.logger import setup_logger, get_logger


class V2VSystem:
    """
    Complete Vehicle-to-Vehicle Communication System.
    
    Integrates:
    - On-Board Unit (OBU) for data collection
    - Broadcasting for sending data to nearby vehicles
    - Receiving for getting data from nearby vehicles
    - Collision detection and avoidance
    """
    
    def __init__(self, vehicle_id: Optional[str] = None, 
                 config_file: Optional[str] = None):
        """
        Initialize V2V System.
        
        Args:
            vehicle_id: Unique vehicle identifier
            config_file: Path to configuration file
        """
        # Load configuration
        self.config = Config(config_file)
        
        # Setup logger
        self.logger = setup_logger(
            name=f"v2v_system_{vehicle_id or 'default'}",
            log_file=self.config.get('system.log_file'),
            debug=self.config.get('system.debug', False)
        )
        
        # Initialize OBU
        self.obu = OBU(vehicle_id)
        self.logger.info(f"Initialized OBU with vehicle ID: {self.obu.vehicle_id}")
        
        # Initialize broadcaster
        self.broadcaster = V2VBroadcaster(
            obu=self.obu,
            port=self.config.get('communication.udp_port', 5555),
            broadcast_frequency=self.config.get('communication.broadcast_frequency', 10),
            base_radius=self.config.get('communication.base_radius', 100.0),
            max_radius=self.config.get('communication.max_radius', 500.0),
            speed_factor=self.config.get('communication.speed_radius_factor', 5.0)
        )
        
        # Initialize receiver
        self.receiver = V2VReceiver(
            own_vehicle_id=self.obu.vehicle_id,
            port=self.config.get('communication.udp_port', 5555),
            max_message_age=5.0,
            vehicle_timeout=10.0
        )
        
        # Initialize collision detector
        self.collision_detector = CollisionDetector(
            ttc_threshold=self.config.get('collision_detection.ttc_threshold', 3.0),
            critical_ttc_threshold=self.config.get('collision_detection.critical_ttc_threshold', 1.5),
            min_safe_distance=self.config.get('collision_detection.min_safe_distance', 5.0),
            prediction_horizon=self.config.get('collision_detection.prediction_horizon', 5.0)
        )
        
        # Initialize collision avoidance system
        self.collision_avoidance = CollisionAvoidanceSystem(
            own_vehicle=self.obu.get_current_data(),
            detector=self.collision_detector
        )
        
        # Setup default callbacks
        self._setup_callbacks()
        
        # System state
        self.is_running = False
        
        self.logger.info("V2V System initialized successfully")
    
    def _setup_callbacks(self):
        """Setup default system callbacks"""
        # Log new vehicles
        self.receiver.register_vehicle_update_callback(self._on_vehicle_update)
        
        # Log vehicle timeouts
        self.receiver.register_vehicle_timeout_callback(self._on_vehicle_timeout)
        
        # Log collision warnings
        self.collision_avoidance.register_warning_callback(self._on_collision_warning)
        self.collision_avoidance.register_critical_warning_callback(self._on_critical_warning)
    
    def _on_vehicle_update(self, vehicle_data: VehicleData, is_new: bool):
        """Callback for vehicle updates"""
        if is_new:
            self.logger.info(f"New vehicle detected: {vehicle_data.vehicle_id} "
                           f"at {vehicle_data.speed:.1f} km/h")
        
        # Update collision avoidance system
        nearby_vehicles = self.receiver.get_nearby_vehicles()
        self.collision_avoidance.update(self.obu.get_current_data(), nearby_vehicles)
    
    def _on_vehicle_timeout(self, vehicle_id: str):
        """Callback for vehicle timeout"""
        self.logger.info(f"Vehicle {vehicle_id} is no longer in range")
    
    def _on_collision_warning(self, warning: CollisionWarning):
        """Callback for collision warnings"""
        self.logger.warning(
            f"Collision warning: {warning.risk_level.name} risk with {warning.target_vehicle_id}, "
            f"TTC: {warning.time_to_collision:.2f}s, Distance: {warning.distance:.1f}m - "
            f"{warning.recommendation}"
        )
    
    def _on_critical_warning(self, warning: CollisionWarning):
        """Callback for critical collision warnings"""
        self.logger.critical(
            f"CRITICAL COLLISION WARNING with {warning.target_vehicle_id}! "
            f"TTC: {warning.time_to_collision:.2f}s - {warning.recommendation}"
        )
    
    def start(self):
        """Start the V2V system"""
        if self.is_running:
            self.logger.warning("System already running")
            return
        
        self.logger.info("Starting V2V System...")
        
        # Start receiver first
        self.receiver.start()
        
        # Start broadcaster
        self.broadcaster.start()
        
        self.is_running = True
        self.logger.info("V2V System started successfully")
    
    def stop(self):
        """Stop the V2V system"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping V2V System...")
        
        # Stop broadcaster
        self.broadcaster.stop()
        
        # Stop receiver
        self.receiver.stop()
        
        self.is_running = False
        self.logger.info("V2V System stopped")
    
    # OBU Interface Methods
    def update_gps(self, latitude: float, longitude: float, altitude: float = 0.0):
        """Update GPS location"""
        self.obu.update_gps(latitude, longitude, altitude)
    
    def update_speed(self, speed: float):
        """Update vehicle speed in km/h"""
        self.obu.update_speed(speed)
    
    def update_heading(self, heading: float):
        """Update vehicle heading in degrees"""
        self.obu.update_heading(heading)
    
    def update_braking(self, is_braking: bool, braking_force: float = 0.0):
        """Update braking status"""
        self.obu.update_braking(is_braking, braking_force)
    
    def update_adas_data(self, adas_data: dict):
        """Update ADAS sensor data"""
        self.obu.update_adas_data(adas_data)
    
    # Status and Information Methods
    def get_nearby_vehicles(self):
        """Get all nearby vehicles"""
        return self.receiver.get_nearby_vehicles()
    
    def get_active_warnings(self):
        """Get active collision warnings"""
        return self.collision_avoidance.get_active_warnings()
    
    def get_statistics(self) -> dict:
        """Get system statistics"""
        return {
            'vehicle_id': self.obu.vehicle_id,
            'is_running': self.is_running,
            'broadcaster': self.broadcaster.get_statistics(),
            'receiver': self.receiver.get_statistics(),
            'nearby_vehicles': self.receiver.get_vehicle_count(),
            'active_warnings': len(self.collision_avoidance.get_active_warnings()),
        }
    
    def send_emergency_broadcast(self):
        """Send emergency broadcast"""
        self.logger.critical("Sending emergency broadcast")
        self.broadcaster.send_emergency_message()
    
    def register_collision_warning_callback(self, callback: Callable[[CollisionWarning], None]):
        """Register custom callback for collision warnings"""
        self.collision_avoidance.register_warning_callback(callback)
    
    def register_critical_warning_callback(self, callback: Callable[[CollisionWarning], None]):
        """Register custom callback for critical collision warnings"""
        self.collision_avoidance.register_critical_warning_callback(callback)
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
    
    def __del__(self):
        """Cleanup"""
        self.stop()
