# V2V Architecture - Vehicle-to-Vehicle Communication System

A comprehensive Vehicle-to-Vehicle (V2V) communication system with real-time data broadcasting, collision detection, and avoidance capabilities.

## Overview

This V2V system enables vehicles to communicate their position, speed, heading, and sensor data with nearby vehicles in real-time. The system includes:

- **On-Board Unit (OBU)**: Collects and manages vehicle data including GPS location, speed, acceleration, braking status, heading, and ADAS sensor data
- **Real-time Broadcasting**: Broadcasts vehicle data to nearby vehicles using UDP with dynamic radius based on speed
- **Message Reception & Processing**: Receives and validates messages from nearby vehicles with low latency
- **Collision Prediction**: Predicts vehicle movements and trajectories using constant velocity and acceleration models
- **Collision Avoidance**: Detects potential collisions and generates warnings with recommendations

## Features

### On-Board Unit (OBU)
- GPS location tracking (latitude, longitude, altitude)
- Speed and acceleration monitoring
- Heading calculation and tracking
- Braking status detection
- ADAS sensor data collection (radar, LiDAR, camera)
- Dynamic broadcast radius calculation based on vehicle speed

### Communication System
- UDP broadcast for low-latency communication
- Message serialization/deserialization with JSON
- Message validation and integrity checking
- Configurable broadcast frequency
- Emergency broadcast capability
- Automatic filtering of own messages

### Collision Detection & Avoidance
- Time-to-collision (TTC) calculation
- Risk level assessment (None, Low, Medium, High, Critical)
- Movement prediction with acceleration support
- Path convergence detection
- Multi-vehicle collision detection
- Actionable recommendations for drivers
- Real-time warning callbacks

## Architecture

```
V2V System
├── OBU (On-Board Unit)
│   ├── Vehicle Data Collection
│   ├── GPS Tracking
│   ├── Speed/Acceleration Monitoring
│   ├── ADAS Integration
│   └── Dynamic Radius Calculation
├── Communication Layer
│   ├── Broadcaster (UDP)
│   ├── Receiver (UDP)
│   ├── Message Handling
│   └── Validation
├── Collision Detection
│   ├── Movement Predictor
│   ├── Collision Detector
│   └── Avoidance System
└── Utilities
    ├── Configuration
    └── Logging
```

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Install from source

```bash
# Clone the repository
git clone https://github.com/OmkarDeshmukh90/V2V-architecture.git
cd V2V-architecture

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Usage

### Basic Usage

```python
from src.v2v.v2v_system import V2VSystem

# Initialize the V2V system
vehicle = V2VSystem(vehicle_id="CAR_001")

# Start the system
vehicle.start()

# Update vehicle data
vehicle.update_gps(latitude=37.7749, longitude=-122.4194)
vehicle.update_speed(60.0)  # km/h
vehicle.update_heading(45.0)  # degrees
vehicle.update_braking(is_braking=False, braking_force=0.0)

# Update ADAS data
adas_data = {
    'radar': [{'distance': 50, 'angle': 0}],
    'camera': [{'type': 'vehicle', 'distance': 45}]
}
vehicle.update_adas_data(adas_data)

# Get nearby vehicles
nearby_vehicles = vehicle.get_nearby_vehicles()

# Get collision warnings
warnings = vehicle.get_active_warnings()

# Stop the system
vehicle.stop()
```

### Using Context Manager

```python
from src.v2v.v2v_system import V2VSystem

with V2VSystem(vehicle_id="CAR_001") as vehicle:
    vehicle.update_gps(37.7749, -122.4194)
    vehicle.update_speed(60.0)
    # System automatically stops when exiting context
```

### Custom Callbacks

```python
def on_collision_warning(warning):
    print(f"Warning: {warning.risk_level.name} with {warning.target_vehicle_id}")
    print(f"TTC: {warning.time_to_collision:.2f}s")
    print(f"Recommendation: {warning.recommendation}")

vehicle = V2VSystem(vehicle_id="CAR_001")
vehicle.register_collision_warning_callback(on_collision_warning)
vehicle.start()
```

## Examples

### Single Vehicle Demo

Run a single vehicle simulation:

```bash
python examples/single_vehicle_demo.py
```

This demonstrates:
- Vehicle data collection and broadcasting
- Real-time data updates
- Statistics monitoring

### Collision Scenario Demo

Run a multi-vehicle collision scenario:

```bash
python examples/collision_scenario_demo.py
```

This demonstrates:
- Multiple vehicles communicating
- Collision detection between vehicles
- Warning generation and recommendations

## Configuration

The system can be configured using a YAML file:

```yaml
# config/v2v_config.yaml

communication:
  base_radius: 100.0          # Base broadcast radius (meters)
  max_radius: 500.0           # Maximum broadcast radius (meters)
  speed_radius_factor: 5.0    # Speed factor for radius calculation
  broadcast_frequency: 10     # Broadcasts per second
  udp_port: 5555             # UDP port for communication

collision_detection:
  ttc_threshold: 3.0          # Time-to-collision warning threshold (seconds)
  critical_ttc_threshold: 1.5 # Critical TTC threshold (seconds)
  min_safe_distance: 5.0      # Minimum safe distance (meters)
  prediction_horizon: 5.0     # Prediction time horizon (seconds)

system:
  debug: false
  log_file: "v2v_system.log"
```

Load configuration:

```python
vehicle = V2VSystem(vehicle_id="CAR_001", config_file="config/v2v_config.yaml")
```

## API Reference

### V2VSystem

Main class integrating all V2V components.

**Methods:**
- `start()`: Start the V2V system
- `stop()`: Stop the V2V system
- `update_gps(latitude, longitude, altitude)`: Update GPS location
- `update_speed(speed)`: Update vehicle speed (km/h)
- `update_heading(heading)`: Update heading (degrees)
- `update_braking(is_braking, braking_force)`: Update braking status
- `update_adas_data(adas_data)`: Update ADAS sensor data
- `get_nearby_vehicles()`: Get all nearby vehicles
- `get_active_warnings()`: Get active collision warnings
- `get_statistics()`: Get system statistics
- `send_emergency_broadcast()`: Send emergency message

### OBU (On-Board Unit)

Manages vehicle data collection.

**Methods:**
- `update_gps(latitude, longitude, altitude)`: Update GPS data
- `update_speed(speed)`: Update speed
- `update_heading(heading)`: Update heading
- `update_braking(is_braking, braking_force)`: Update braking
- `get_current_data()`: Get current vehicle data
- `get_broadcast_radius()`: Calculate dynamic broadcast radius

### CollisionDetector

Detects potential collisions.

**Methods:**
- `calculate_distance(vehicle1, vehicle2)`: Calculate distance between vehicles
- `calculate_time_to_collision(own_vehicle, other_vehicle)`: Calculate TTC
- `assess_collision_risk(own_vehicle, other_vehicle)`: Assess risk level
- `detect_collisions(own_vehicle, nearby_vehicles)`: Detect all potential collisions

## Technical Details

### Dynamic Broadcast Radius

The broadcast radius dynamically adjusts based on vehicle speed:

```
radius = base_radius + (speed_kmh / speed_factor)
radius = min(radius, max_radius)
```

Example: At 100 km/h with speed_factor=5.0 and base_radius=100m:
- radius = 100 + (100 / 5) = 120 meters

### Time-to-Collision Calculation

TTC is calculated using relative velocity and distance:

```
TTC = distance / relative_speed
```

Where relative_speed considers both vehicles' velocities and directions.

### Risk Levels

- **CRITICAL**: TTC ≤ 1.5s or distance < min_safe_distance
- **HIGH**: TTC ≤ 2.0s
- **MEDIUM**: TTC ≤ 3.0s
- **LOW**: TTC > 3.0s
- **NONE**: No collision predicted

## Performance Considerations

- **Broadcast Frequency**: Default 10 Hz provides good balance between latency and bandwidth
- **Message Size**: Typical messages are ~300-500 bytes
- **Latency**: End-to-end latency typically < 100ms on local network
- **Processing**: Collision detection runs at each vehicle update (~20 Hz)

## Testing

Run tests (when available):

```bash
python -m pytest tests/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Enhancements

- [ ] Support for TCP communication option
- [ ] Multi-hop message forwarding
- [ ] Integration with real GPS hardware
- [ ] CAN bus integration for vehicle data
- [ ] Machine learning-based trajectory prediction
- [ ] Road geometry awareness
- [ ] Weather and road condition integration
- [ ] V2I (Vehicle-to-Infrastructure) communication
- [ ] Cybersecurity enhancements (message signing, encryption)

## Acknowledgments

This V2V system implements concepts from:
- IEEE 802.11p WAVE standard
- SAE J2735 message set
- Intelligent Transportation Systems (ITS) research