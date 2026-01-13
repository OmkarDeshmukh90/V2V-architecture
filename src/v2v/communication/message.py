"""
Message handling for V2V communication
"""
import json
import time
from typing import Dict, Any
from ..obu.vehicle_data import VehicleData


class V2VMessage:
    """V2V communication message wrapper"""
    
    MESSAGE_TYPE_BROADCAST = "broadcast"
    MESSAGE_TYPE_EMERGENCY = "emergency"
    MESSAGE_TYPE_ACK = "acknowledgment"
    
    def __init__(self, message_type: str, vehicle_data: VehicleData, 
                 sequence_number: int = 0, broadcast_radius: float = 100.0):
        """
        Initialize V2V message.
        
        Args:
            message_type: Type of message (broadcast, emergency, acknowledgment)
            vehicle_data: Vehicle data to send
            sequence_number: Message sequence number for ordering
            broadcast_radius: Intended broadcast radius in meters
        """
        self.message_type = message_type
        self.vehicle_data = vehicle_data
        self.sequence_number = sequence_number
        self.broadcast_radius = broadcast_radius
        self.creation_time = time.time()
    
    def serialize(self) -> bytes:
        """
        Serialize message to bytes for transmission.
        
        Returns:
            Serialized message as bytes
        """
        message_dict = {
            'type': self.message_type,
            'sequence': self.sequence_number,
            'radius': self.broadcast_radius,
            'creation_time': self.creation_time,
            'data': self.vehicle_data.to_dict()
        }
        json_str = json.dumps(message_dict)
        return json_str.encode('utf-8')
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'V2VMessage':
        """
        Deserialize message from bytes.
        
        Args:
            data: Serialized message bytes
        
        Returns:
            V2VMessage object
        """
        json_str = data.decode('utf-8')
        message_dict = json.loads(json_str)
        
        vehicle_data = VehicleData.from_dict(message_dict['data'])
        
        message = cls(
            message_type=message_dict['type'],
            vehicle_data=vehicle_data,
            sequence_number=message_dict.get('sequence', 0),
            broadcast_radius=message_dict.get('radius', 100.0)
        )
        message.creation_time = message_dict.get('creation_time', time.time())
        
        return message
    
    def is_valid(self, max_age: float = 5.0) -> bool:
        """
        Check if message is still valid (not too old).
        
        Args:
            max_age: Maximum message age in seconds
        
        Returns:
            True if message is valid, False otherwise
        """
        age = time.time() - self.creation_time
        return age <= max_age
    
    def __repr__(self):
        return (f"V2VMessage(type={self.message_type}, "
                f"vehicle={self.vehicle_data.vehicle_id}, "
                f"seq={self.sequence_number})")


class MessageValidator:
    """Validates incoming V2V messages"""
    
    @staticmethod
    def validate_message(message: V2VMessage, max_age: float = 5.0) -> tuple[bool, str]:
        """
        Validate a V2V message.
        
        Args:
            message: Message to validate
            max_age: Maximum allowed message age in seconds
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check message age
        if not message.is_valid(max_age):
            return False, "Message too old"
        
        # Check vehicle data completeness
        if not message.vehicle_data.vehicle_id:
            return False, "Missing vehicle ID"
        
        # Check GPS coordinates are valid
        if not (-90 <= message.vehicle_data.latitude <= 90):
            return False, "Invalid latitude"
        
        if not (-180 <= message.vehicle_data.longitude <= 180):
            return False, "Invalid longitude"
        
        # Check speed is non-negative
        if message.vehicle_data.speed < 0:
            return False, "Invalid speed"
        
        # Check heading is valid
        if not (0 <= message.vehicle_data.heading < 360):
            return False, "Invalid heading"
        
        return True, ""
    
    @staticmethod
    def validate_data_integrity(data: bytes, max_size: int = 1024) -> tuple[bool, str]:
        """
        Validate data integrity before deserialization.
        
        Args:
            data: Raw message data
            max_size: Maximum allowed message size in bytes
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check size
        if len(data) > max_size:
            return False, f"Message too large: {len(data)} > {max_size}"
        
        # Try to decode and parse JSON
        try:
            json_str = data.decode('utf-8')
            message_dict = json.loads(json_str)
            
            # Check required fields
            required_fields = ['type', 'data']
            for field in required_fields:
                if field not in message_dict:
                    return False, f"Missing required field: {field}"
            
            # Check data structure
            data_dict = message_dict['data']
            required_data_fields = ['vehicle_id', 'latitude', 'longitude', 'speed', 'heading']
            for field in required_data_fields:
                if field not in data_dict:
                    return False, f"Missing required data field: {field}"
            
            return True, ""
        
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
