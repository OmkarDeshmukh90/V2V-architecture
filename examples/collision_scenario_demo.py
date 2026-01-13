"""
Example V2V System Demo - Multiple Vehicles with Collision Scenario

This example demonstrates V2V communication between multiple vehicles
and collision detection/avoidance.
"""
import time
import sys
import os
import threading
import math

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.v2v.v2v_system import V2VSystem


def simulate_vehicle(vehicle_id, start_lat, start_lon, direction, duration=30):
    """
    Simulate a single vehicle.
    
    Args:
        vehicle_id: Vehicle identifier
        start_lat: Starting latitude
        start_lon: Starting longitude
        direction: Direction of travel (0-360 degrees)
        duration: Simulation duration in seconds
    """
    # Initialize V2V system
    vehicle = V2VSystem(vehicle_id=vehicle_id)
    vehicle.start()
    
    print(f"[{vehicle_id}] Started at ({start_lat:.6f}, {start_lon:.6f}), heading {direction}°")
    
    latitude = start_lat
    longitude = start_lon
    speed = 60  # km/h
    
    try:
        start_time = time.time()
        iteration = 0
        
        while time.time() - start_time < duration:
            # Update position based on direction
            # Move approximately 1.67 meters per iteration (60 km/h = 16.67 m/s)
            heading_rad = math.radians(90 - direction)
            lat_change = 1.67 * math.sin(math.radians(direction)) / 111000.0
            lon_change = 1.67 * math.cos(math.radians(direction)) / (111000.0 * math.cos(math.radians(latitude)))
            
            latitude += lat_change
            longitude += lon_change
            
            # Update vehicle data
            vehicle.update_gps(latitude, longitude)
            vehicle.update_speed(speed)
            vehicle.update_heading(direction)
            
            # Check for warnings
            if iteration % 10 == 0:  # Check every 10 iterations
                warnings = vehicle.get_active_warnings()
                nearby = vehicle.get_nearby_vehicles()
                
                if warnings:
                    print(f"\n[{vehicle_id}] ⚠️  COLLISION WARNING!")
                    for warning in warnings:
                        print(f"  Risk: {warning.risk_level.name}")
                        print(f"  Target: {warning.target_vehicle_id}")
                        print(f"  TTC: {warning.time_to_collision:.2f}s")
                        print(f"  Distance: {warning.distance:.1f}m")
                        print(f"  Recommendation: {warning.recommendation}")
                
                if nearby:
                    print(f"[{vehicle_id}] Detected {len(nearby)} nearby vehicles")
            
            iteration += 1
            time.sleep(0.1)
    
    except Exception as e:
        print(f"[{vehicle_id}] Error: {e}")
    
    finally:
        vehicle.stop()
        print(f"[{vehicle_id}] Stopped")


def collision_scenario():
    """Simulate a collision scenario with multiple vehicles"""
    
    print("=" * 70)
    print("V2V System Demo - Multiple Vehicles Collision Scenario")
    print("=" * 70)
    print("\nScenario: Two vehicles approaching intersection from perpendicular directions")
    print("Press Ctrl+C to stop\n")
    
    # Vehicle 1: Moving north from the south
    # Vehicle 2: Moving east from the west
    # They should detect potential collision at intersection
    
    base_lat = 37.7749
    base_lon = -122.4194
    
    # Create threads for each vehicle
    vehicle1_thread = threading.Thread(
        target=simulate_vehicle,
        args=("VEHICLE_001", base_lat - 0.002, base_lon, 0, 30),  # Moving north
        daemon=True
    )
    
    vehicle2_thread = threading.Thread(
        target=simulate_vehicle,
        args=("VEHICLE_002", base_lat, base_lon - 0.002, 90, 30),  # Moving east
        daemon=True
    )
    
    try:
        # Start vehicles
        vehicle1_thread.start()
        time.sleep(0.5)  # Slight delay
        vehicle2_thread.start()
        
        # Wait for vehicles to complete
        vehicle1_thread.join()
        vehicle2_thread.join()
        
    except KeyboardInterrupt:
        print("\n\nStopping simulation...")
    
    print("\n" + "=" * 70)
    print("Collision scenario demo completed.")
    print("=" * 70)


if __name__ == "__main__":
    collision_scenario()
