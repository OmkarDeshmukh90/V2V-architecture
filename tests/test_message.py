"""
Tests for Message handling
"""
import pytest
import time
from src.v2v.obu.vehicle_data import VehicleData
from src.v2v.communication.message import V2VMessage, MessageValidator


def test_message_creation():
    """Test V2V message creation"""
    vehicle_data = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=60.0,
        heading=45.0
    )
    
    message = V2VMessage(
        message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
        vehicle_data=vehicle_data,
        sequence_number=1,
        broadcast_radius=150.0
    )
    
    assert message.message_type == V2VMessage.MESSAGE_TYPE_BROADCAST
    assert message.vehicle_data.vehicle_id == "TEST_001"
    assert message.sequence_number == 1
    assert message.broadcast_radius == 150.0


def test_message_serialization():
    """Test message serialization to bytes"""
    vehicle_data = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=60.0,
        heading=45.0
    )
    
    message = V2VMessage(
        message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
        vehicle_data=vehicle_data
    )
    
    serialized = message.serialize()
    assert isinstance(serialized, bytes)
    assert len(serialized) > 0


def test_message_deserialization():
    """Test message deserialization from bytes"""
    vehicle_data = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=60.0,
        heading=45.0
    )
    
    original_message = V2VMessage(
        message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
        vehicle_data=vehicle_data,
        sequence_number=5
    )
    
    serialized = original_message.serialize()
    deserialized = V2VMessage.deserialize(serialized)
    
    assert deserialized.message_type == original_message.message_type
    assert deserialized.vehicle_data.vehicle_id == original_message.vehicle_data.vehicle_id
    assert deserialized.vehicle_data.latitude == original_message.vehicle_data.latitude
    assert deserialized.vehicle_data.speed == original_message.vehicle_data.speed
    assert deserialized.sequence_number == original_message.sequence_number


def test_message_validity():
    """Test message validity check"""
    vehicle_data = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=60.0,
        heading=45.0
    )
    
    message = V2VMessage(
        message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
        vehicle_data=vehicle_data
    )
    
    # Fresh message should be valid
    assert message.is_valid(max_age=5.0) == True
    
    # Old message should be invalid
    message.creation_time = time.time() - 10.0
    assert message.is_valid(max_age=5.0) == False


def test_message_validator():
    """Test message validation"""
    vehicle_data = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=60.0,
        heading=45.0
    )
    
    message = V2VMessage(
        message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
        vehicle_data=vehicle_data
    )
    
    validator = MessageValidator()
    is_valid, error = validator.validate_message(message)
    assert is_valid == True
    assert error == ""


def test_invalid_latitude():
    """Test validation rejects invalid latitude"""
    vehicle_data = VehicleData(
        vehicle_id="TEST_001",
        latitude=100.0,  # Invalid (>90)
        longitude=-122.4194,
        speed=60.0,
        heading=45.0
    )
    
    message = V2VMessage(
        message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
        vehicle_data=vehicle_data
    )
    
    validator = MessageValidator()
    is_valid, error = validator.validate_message(message)
    assert is_valid == False
    assert "latitude" in error.lower()


def test_invalid_longitude():
    """Test validation rejects invalid longitude"""
    vehicle_data = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-200.0,  # Invalid (<-180)
        speed=60.0,
        heading=45.0
    )
    
    message = V2VMessage(
        message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
        vehicle_data=vehicle_data
    )
    
    validator = MessageValidator()
    is_valid, error = validator.validate_message(message)
    assert is_valid == False
    assert "longitude" in error.lower()


def test_invalid_speed():
    """Test validation rejects negative speed"""
    vehicle_data = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=-10.0,  # Invalid (negative)
        heading=45.0
    )
    
    message = V2VMessage(
        message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
        vehicle_data=vehicle_data
    )
    
    validator = MessageValidator()
    is_valid, error = validator.validate_message(message)
    assert is_valid == False
    assert "speed" in error.lower()


def test_data_integrity_validation():
    """Test data integrity validation"""
    vehicle_data = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=60.0,
        heading=45.0
    )
    
    message = V2VMessage(
        message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
        vehicle_data=vehicle_data
    )
    
    serialized = message.serialize()
    validator = MessageValidator()
    
    is_valid, error = validator.validate_data_integrity(serialized)
    assert is_valid == True
    assert error == ""


def test_data_integrity_too_large():
    """Test data integrity rejects oversized messages"""
    validator = MessageValidator()
    large_data = b"x" * 2000
    
    is_valid, error = validator.validate_data_integrity(large_data, max_size=1024)
    assert is_valid == False
    assert "too large" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
