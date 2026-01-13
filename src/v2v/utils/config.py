"""
Configuration management for V2V system
"""
import yaml
import os
from typing import Any, Dict, Optional


class Config:
    """Configuration manager for V2V system"""
    
    DEFAULT_CONFIG = {
        'communication': {
            'base_radius': 100.0,
            'max_radius': 500.0,
            'speed_radius_factor': 5.0,
            'broadcast_frequency': 10,
            'udp_port': 5555,
            'max_message_size': 1024,
        },
        'obu': {
            'vehicle_id_prefix': 'V2V',
            'sensor_update_frequency': 20,
            'adas_sensors': ['radar', 'lidar', 'camera'],
        },
        'collision_detection': {
            'ttc_threshold': 3.0,
            'critical_ttc_threshold': 1.5,
            'min_safe_distance': 5.0,
            'prediction_horizon': 5.0,
            'risk_threshold': 0.7,
        },
        'system': {
            'debug': False,
            'log_file': 'v2v_system.log',
            'monitoring_interval': 1.0,
        },
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to YAML configuration file
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """Load configuration from YAML file"""
        try:
            with open(config_file, 'r') as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config:
                    self._deep_update(self.config, loaded_config)
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    def _deep_update(self, base: dict, update: dict):
        """Deep update dictionary"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by dot-separated key"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_all(self) -> Dict:
        """Get all configuration"""
        return self.config.copy()
