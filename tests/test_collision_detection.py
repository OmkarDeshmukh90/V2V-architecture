"""
Tests for collision detection
"""
import pytest
from src.v2v.obu.vehicle_data import VehicleData
from src.v2v.collision_detection.detector import CollisionDetector, CollisionRiskLevel
from src.v2v.collision_detection.predictor import MovementPredictor


def test_predictor_position():
    """Test position prediction"""
    vehicle = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,  # 36 km/h = 10 m/s
        heading=0.0  # North
    )
    vehicle.calculate_velocity_components()
    
    predictor = MovementPredictor()
    
    # Predict position 1 second ahead
    lat, lon = predictor.predict_position(vehicle, 1.0)
    
    # Should move ~10 meters north
    # 10 meters ≈ 0.00009 degrees latitude
    assert lat > vehicle.latitude
    assert abs(lon - vehicle.longitude) < 0.00001  # Longitude shouldn't change much


def test_predictor_trajectory():
    """Test trajectory prediction"""
    vehicle = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0
    )
    
    predictor = MovementPredictor()
    trajectory = predictor.predict_trajectory(vehicle, time_horizon=2.0, time_step=0.5)
    
    # Should have predictions at t=0, 0.5, 1.0, 1.5, 2.0
    assert len(trajectory) == 5
    
    # Check increasing latitude (moving north)
    lats = [point[1] for point in trajectory]
    for i in range(1, len(lats)):
        assert lats[i] > lats[i-1]


def test_relative_velocity():
    """Test relative velocity calculation"""
    vehicle1 = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0  # North
    )
    
    vehicle2 = VehicleData(
        vehicle_id="TEST_002",
        latitude=37.7750,
        longitude=-122.4194,
        speed=36.0,
        heading=180.0  # South
    )
    
    predictor = MovementPredictor()
    rel_v_x, rel_v_y = predictor.calculate_relative_velocity(vehicle1, vehicle2)
    
    # Vehicles moving in opposite directions should have high relative velocity
    relative_speed = (rel_v_x**2 + rel_v_y**2)**0.5
    assert relative_speed > 15  # Should be ~20 m/s


def test_paths_converging():
    """Test path convergence detection"""
    vehicle1 = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0  # North
    )
    
    # Vehicle ahead moving slower
    vehicle2 = VehicleData(
        vehicle_id="TEST_002",
        latitude=37.7750,
        longitude=-122.4194,
        speed=18.0,
        heading=0.0  # North
    )
    
    predictor = MovementPredictor()
    assert predictor.are_paths_converging(vehicle1, vehicle2) == True


def test_paths_diverging():
    """Test path divergence detection"""
    vehicle1 = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0  # North
    )
    
    # Vehicle ahead moving faster
    vehicle2 = VehicleData(
        vehicle_id="TEST_002",
        latitude=37.7750,
        longitude=-122.4194,
        speed=72.0,
        heading=0.0  # North
    )
    
    predictor = MovementPredictor()
    assert predictor.are_paths_converging(vehicle1, vehicle2) == False


def test_distance_calculation():
    """Test distance calculation"""
    detector = CollisionDetector()
    
    vehicle1 = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0
    )
    
    # Vehicle 0.001 degrees north (~111 meters)
    vehicle2 = VehicleData(
        vehicle_id="TEST_002",
        latitude=37.7759,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0
    )
    
    distance = detector.calculate_distance(vehicle1, vehicle2)
    assert 100 < distance < 120  # Should be ~111 meters


def test_collision_risk_assessment():
    """Test collision risk assessment"""
    detector = CollisionDetector(
        ttc_threshold=3.0,
        critical_ttc_threshold=1.5
    )
    
    own_vehicle = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0  # North at 10 m/s
    )
    
    # Vehicle ahead, slower speed, same direction
    other_vehicle = VehicleData(
        vehicle_id="TEST_002",
        latitude=37.7750,  # ~11 meters ahead
        longitude=-122.4194,
        speed=18.0,  # 5 m/s
        heading=0.0
    )
    
    risk_level, ttc = detector.assess_collision_risk(own_vehicle, other_vehicle)
    
    # Should detect collision risk
    assert risk_level != CollisionRiskLevel.NONE
    assert ttc is not None
    assert ttc > 0


def test_critical_risk_close_distance():
    """Test critical risk for very close vehicles"""
    detector = CollisionDetector(min_safe_distance=5.0)
    
    own_vehicle = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0
    )
    
    # Very close vehicle
    other_vehicle = VehicleData(
        vehicle_id="TEST_002",
        latitude=37.774902,  # ~2 meters ahead
        longitude=-122.4194,
        speed=18.0,
        heading=0.0
    )
    
    risk_level, ttc = detector.assess_collision_risk(own_vehicle, other_vehicle)
    
    # Should be critical due to close distance
    assert risk_level == CollisionRiskLevel.CRITICAL


def test_no_collision_diverging():
    """Test no collision for diverging paths"""
    detector = CollisionDetector()
    
    own_vehicle = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0  # North
    )
    
    # Vehicle moving away (south)
    other_vehicle = VehicleData(
        vehicle_id="TEST_002",
        latitude=37.7748,
        longitude=-122.4194,
        speed=36.0,
        heading=180.0  # South
    )
    
    risk_level, ttc = detector.assess_collision_risk(own_vehicle, other_vehicle)
    
    # Should not detect collision (diverging)
    assert risk_level == CollisionRiskLevel.NONE
    assert ttc is None


def test_detect_multiple_collisions():
    """Test detecting collisions with multiple vehicles"""
    detector = CollisionDetector()
    
    own_vehicle = VehicleData(
        vehicle_id="TEST_001",
        latitude=37.7749,
        longitude=-122.4194,
        speed=36.0,
        heading=0.0
    )
    
    nearby_vehicles = {
        "TEST_002": VehicleData(
            vehicle_id="TEST_002",
            latitude=37.7750,
            longitude=-122.4194,
            speed=18.0,
            heading=0.0
        ),
        "TEST_003": VehicleData(
            vehicle_id="TEST_003",
            latitude=37.7748,
            longitude=-122.4194,
            speed=36.0,
            heading=180.0  # Moving away
        )
    }
    
    warnings = detector.detect_collisions(own_vehicle, nearby_vehicles)
    
    # Should detect at least one collision (with TEST_002)
    # TEST_003 is moving away so no collision
    assert len(warnings) >= 1
    
    # Warnings should be sorted by risk
    if len(warnings) > 1:
        for i in range(len(warnings) - 1):
            assert warnings[i].risk_level.value >= warnings[i+1].risk_level.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
