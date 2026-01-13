"""
Example V2V System Demo - Single Vehicle

This example demonstrates how to use the V2V system for a single vehicle.
"""
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.v2v.v2v_system import V2VSystem


def simulate_vehicle_journey():
    """Simulate a vehicle journey with V2V communication"""
    
    print("=" * 60)
    print("V2V System Demo - Single Vehicle")
    print("=" * 60)
    
    # Initialize V2V system
    vehicle = V2VSystem(vehicle_id="DEMO_CAR_001")
    
    # Start the system
    vehicle.start()
    
    print("\nV2V System started. Simulating vehicle journey...")
    print("Press Ctrl+C to stop\n")
    
    try:
        # Simulate initial position (San Francisco area)
        latitude = 37.7749
        longitude = -122.4194
        
        # Simulate a moving vehicle
        for i in range(100):
            # Update GPS (moving north)
            latitude += 0.0001  # ~11 meters north
            vehicle.update_gps(latitude, longitude)
            
            # Update speed (accelerating then cruising)
            if i < 20:
                speed = i * 5  # Accelerating to 100 km/h
            elif i < 80:
                speed = 100  # Cruising
            else:
                speed = 100 - (i - 80) * 5  # Decelerating
            
            vehicle.update_speed(speed)
            
            # Update heading (mostly north with slight variation)
            heading = 0 + (i % 10) * 2  # North with slight oscillation
            vehicle.update_heading(heading)
            
            # Update braking status
            is_braking = i >= 80  # Braking when decelerating
            braking_force = (i - 80) / 20.0 if is_braking else 0.0
            vehicle.update_braking(is_braking, braking_force)
            
            # Simulate ADAS data
            adas_data = {
                'radar': [{'distance': 50 + i, 'angle': 0}],
                'camera': [{'type': 'vehicle', 'distance': 45 + i}],
            }
            vehicle.update_adas_data(adas_data)
            
            # Print status every 10 iterations
            if i % 10 == 0:
                stats = vehicle.get_statistics()
                nearby = vehicle.get_nearby_vehicles()
                warnings = vehicle.get_active_warnings()
                
                print(f"\n--- Update {i} ---")
                print(f"Position: ({latitude:.6f}, {longitude:.6f})")
                print(f"Speed: {speed:.1f} km/h, Heading: {heading:.1f}°")
                print(f"Braking: {is_braking}, Force: {braking_force:.2f}")
                print(f"Messages sent: {stats['broadcaster']['messages_sent']}")
                print(f"Messages received: {stats['receiver']['messages_received']}")
                print(f"Nearby vehicles: {len(nearby)}")
                
                if nearby:
                    print("\nNearby vehicles:")
                    for vid, vdata in nearby.items():
                        print(f"  - {vid}: {vdata.speed:.1f} km/h at ({vdata.latitude:.6f}, {vdata.longitude:.6f})")
                
                if warnings:
                    print(f"\nActive warnings: {len(warnings)}")
                    for warning in warnings:
                        print(f"  - {warning}")
            
            time.sleep(0.1)  # Update every 100ms
        
    except KeyboardInterrupt:
        print("\n\nStopping simulation...")
    
    finally:
        # Stop the system
        vehicle.stop()
        
        # Print final statistics
        print("\n" + "=" * 60)
        print("Final Statistics")
        print("=" * 60)
        stats = vehicle.get_statistics()
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                print(f"{key}: {value}")
        
        print("\nV2V System demo completed.")


if __name__ == "__main__":
    simulate_vehicle_journey()
