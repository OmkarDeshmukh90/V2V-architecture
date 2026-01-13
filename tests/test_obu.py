"""
Tests for OBU (On-Board Unit)
"""
import pytest
import time
from src.v2v.obu.obu import OBU
from src.v2v.obu.vehicle_data import VehicleData


def test_obu_initialization():
    """Test OBU initialization"""
    obu = OBU(vehicle_id="TEST_001")
    assert obu.vehicle_id == "TEST_001"
    assert obu.get_current_data().vehicle_id == "TEST_001"


def test_obu_auto_id():
    """Test automatic ID generation"""
    obu = OBU()
    assert obu.vehicle_id.startswith("V2V_")


def test_update_gps():
    """Test GPS update"""
    obu = OBU(vehicle_id="TEST_001")
    obu.update_gps(37.7749, -122.4194, 100.0)
    
    data = obu.get_current_data()
    assert data.latitude == 37.7749
    assert data.longitude == -122.4194
    assert data.altitude == 100.0


def test_update_speed():
    """Test speed update and acceleration calculation"""
    obu = OBU(vehicle_id="TEST_001")
    
    obu.update_speed(0.0)
    time.sleep(0.1)
    obu.update_speed(36.0)  # 36 km/h = 10 m/s
    
    data = obu.get_current_data()
    assert data.speed == 36.0
    assert data.acceleration > 0  # Should have positive acceleration


def test_update_heading():
    """Test heading update"""
    obu = OBU(vehicle_id="TEST_001")
    obu.update_heading(45.0)
    
    data = obu.get_current_data()
    assert data.heading == 45.0


def test_heading_normalization():
    """Test heading normalization to 0-360 range"""
    obu = OBU(vehicle_id="TEST_001")
    obu.update_heading(370.0)
    
    data = obu.get_current_data()
    assert data.heading == 10.0


def test_update_braking():
    """Test braking status update"""
    obu = OBU(vehicle_id="TEST_001")
    obu.update_braking(True, 0.8)
    
    data = obu.get_current_data()
    assert data.is_braking == True
    assert data.braking_force == 0.8


def test_braking_force_limits():
    """Test braking force is clamped to 0-1 range"""
    obu = OBU(vehicle_id="TEST_001")
    
    obu.update_braking(True, 1.5)
    assert obu.get_current_data().braking_force == 1.0
    
    obu.update_braking(True, -0.5)
    assert obu.get_current_data().braking_force == 0.0


def test_update_adas_data():
    """Test ADAS data update"""
    obu = OBU(vehicle_id="TEST_001")
    adas_data = {
        'radar': [{'distance': 50, 'angle': 0}],
        'camera': [{'type': 'vehicle'}]
    }
    obu.update_adas_data(adas_data)
    
    data = obu.get_current_data()
    assert 'radar' in data.adas_data
    assert 'camera' in data.adas_data


def test_broadcast_radius_calculation():
    """Test dynamic broadcast radius calculation"""
    obu = OBU(vehicle_id="TEST_001")
    
    # At 0 km/h
    obu.update_speed(0.0)
    radius = obu.get_broadcast_radius(base_radius=100.0, speed_factor=5.0)
    assert radius == 100.0
    
    # At 50 km/h
    obu.update_speed(50.0)
    radius = obu.get_broadcast_radius(base_radius=100.0, speed_factor=5.0)
    assert radius == 110.0  # 100 + 50/5
    
    # At 300 km/h: 100 + 300/5 = 160
    obu.update_speed(300.0)
    radius = obu.get_broadcast_radius(base_radius=100.0, max_radius=200.0, speed_factor=5.0)
    assert radius == 160.0
    
    # At 600 km/h (should be capped at max_radius)
    obu.update_speed(600.0)
    radius = obu.get_broadcast_radius(base_radius=100.0, max_radius=200.0, speed_factor=5.0)
    assert radius == 200.0


def test_velocity_components():
    """Test velocity component calculation"""
    obu = OBU(vehicle_id="TEST_001")
    
    # North at 36 km/h (10 m/s)
    obu.update_heading(0.0)
    obu.update_speed(36.0)
    
    data = obu.get_current_data()
    assert abs(data.velocity_x) < 0.1  # Should be ~0 (east-west)
    assert abs(data.velocity_y - 10.0) < 0.1  # Should be ~10 m/s (north)


def test_distance_calculation():
    """Test distance calculation between vehicles"""
    obu1 = OBU(vehicle_id="TEST_001")
    obu1.update_gps(37.7749, -122.4194)
    
    # Create another vehicle data
    vehicle2_data = VehicleData(
        vehicle_id="TEST_002",
        latitude=37.7750,
        longitude=-122.4194
    )
    
    distance = obu1.calculate_distance_to(vehicle2_data)
    # 0.0001 degrees latitude ≈ 11 meters
    assert 10 < distance < 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
