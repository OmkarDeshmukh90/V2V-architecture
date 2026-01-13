"""
V2V Communication Receiver - Handles receiving and processing vehicle data from nearby vehicles
"""
import socket
import threading
import time
from typing import Dict, Callable, Optional
from ..obu.vehicle_data import VehicleData
from .message import V2VMessage, MessageValidator


class V2VReceiver:
    """
    Receives and processes V2V messages from nearby vehicles.
    
    Maintains a registry of nearby vehicles and their latest data.
    """
    
    def __init__(self, own_vehicle_id: str, port: int = 5555,
                 max_message_age: float = 5.0,
                 vehicle_timeout: float = 10.0):
        """
        Initialize the V2V receiver.
        
        Args:
            own_vehicle_id: This vehicle's ID (to filter out own messages)
            port: UDP port to listen on
            max_message_age: Maximum age of messages to accept (seconds)
            vehicle_timeout: Time after which a vehicle is considered offline (seconds)
        """
        self.own_vehicle_id = own_vehicle_id
        self.port = port
        self.max_message_age = max_message_age
        self.vehicle_timeout = vehicle_timeout
        
        # Socket for receiving
        self.socket = None
        
        # Receiving state
        self.is_receiving = False
        self.receive_thread = None
        self.cleanup_thread = None
        
        # Nearby vehicles registry
        self.nearby_vehicles: Dict[str, VehicleData] = {}
        self.vehicle_last_seen: Dict[str, float] = {}
        self.vehicle_lock = threading.Lock()
        
        # Statistics
        self.messages_received = 0
        self.messages_dropped = 0
        self.messages_invalid = 0
        
        # Callbacks
        self.on_message_callbacks = []
        self.on_vehicle_update_callbacks = []
        self.on_vehicle_timeout_callbacks = []
        
        # Validator
        self.validator = MessageValidator()
    
    def start(self):
        """Start receiving V2V messages"""
        if self.is_receiving:
            return
        
        # Create UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind to all interfaces ('') to receive V2V broadcasts from any network interface
        # This is intentional for V2V communication where vehicles may be on different networks
        self.socket.bind(('', self.port))
        self.socket.settimeout(1.0)  # Non-blocking with timeout
        
        # Start receive thread
        self.is_receiving = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        print(f"V2V Receiver started on port {self.port}")
    
    def stop(self):
        """Stop receiving messages"""
        if not self.is_receiving:
            return
        
        self.is_receiving = False
        
        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)
        
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=2.0)
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        print("V2V Receiver stopped")
    
    def _receive_loop(self):
        """Main receive loop"""
        while self.is_receiving:
            try:
                # Receive data
                data, addr = self.socket.recvfrom(4096)
                
                # Process message
                self._process_message(data, addr)
                
            except socket.timeout:
                # Normal timeout, continue
                continue
            except Exception as e:
                if self.is_receiving:
                    print(f"Error in receive loop: {e}")
    
    def _process_message(self, data: bytes, addr: tuple):
        """Process received message"""
        try:
            # Validate data integrity
            is_valid, error = self.validator.validate_data_integrity(data)
            if not is_valid:
                self.messages_invalid += 1
                print(f"Invalid message from {addr}: {error}")
                return
            
            # Deserialize message
            message = V2VMessage.deserialize(data)
            
            # Ignore own messages
            if message.vehicle_data.vehicle_id == self.own_vehicle_id:
                self.messages_dropped += 1
                return
            
            # Validate message
            is_valid, error = self.validator.validate_message(message, self.max_message_age)
            if not is_valid:
                self.messages_invalid += 1
                print(f"Invalid message from {message.vehicle_data.vehicle_id}: {error}")
                return
            
            # Update statistics
            self.messages_received += 1
            
            # Update vehicle registry
            self._update_vehicle(message.vehicle_data)
            
            # Notify callbacks
            for callback in self.on_message_callbacks:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Error in message callback: {e}")
            
        except Exception as e:
            print(f"Error processing message: {e}")
            self.messages_invalid += 1
    
    def _update_vehicle(self, vehicle_data: VehicleData):
        """Update vehicle in registry"""
        vehicle_id = vehicle_data.vehicle_id
        
        with self.vehicle_lock:
            is_new = vehicle_id not in self.nearby_vehicles
            self.nearby_vehicles[vehicle_id] = vehicle_data
            self.vehicle_last_seen[vehicle_id] = time.time()
        
        # Notify callbacks
        for callback in self.on_vehicle_update_callbacks:
            try:
                callback(vehicle_data, is_new)
            except Exception as e:
                print(f"Error in vehicle update callback: {e}")
    
    def _cleanup_loop(self):
        """Cleanup timed-out vehicles"""
        while self.is_receiving:
            try:
                current_time = time.time()
                timed_out_vehicles = []
                
                with self.vehicle_lock:
                    for vehicle_id, last_seen in list(self.vehicle_last_seen.items()):
                        if current_time - last_seen > self.vehicle_timeout:
                            timed_out_vehicles.append(vehicle_id)
                            del self.nearby_vehicles[vehicle_id]
                            del self.vehicle_last_seen[vehicle_id]
                
                # Notify callbacks for timed-out vehicles
                for vehicle_id in timed_out_vehicles:
                    print(f"Vehicle {vehicle_id} timed out")
                    for callback in self.on_vehicle_timeout_callbacks:
                        try:
                            callback(vehicle_id)
                        except Exception as e:
                            print(f"Error in timeout callback: {e}")
                
                time.sleep(1.0)  # Check every second
                
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
    
    def get_nearby_vehicles(self) -> Dict[str, VehicleData]:
        """Get all nearby vehicles"""
        with self.vehicle_lock:
            return dict(self.nearby_vehicles)
    
    def get_vehicle(self, vehicle_id: str) -> Optional[VehicleData]:
        """Get specific vehicle data"""
        with self.vehicle_lock:
            return self.nearby_vehicles.get(vehicle_id)
    
    def get_vehicle_count(self) -> int:
        """Get count of nearby vehicles"""
        with self.vehicle_lock:
            return len(self.nearby_vehicles)
    
    def register_message_callback(self, callback: Callable[[V2VMessage], None]):
        """Register callback for each message received"""
        self.on_message_callbacks.append(callback)
    
    def register_vehicle_update_callback(self, callback: Callable[[VehicleData, bool], None]):
        """Register callback for vehicle updates (data, is_new)"""
        self.on_vehicle_update_callbacks.append(callback)
    
    def register_vehicle_timeout_callback(self, callback: Callable[[str], None]):
        """Register callback for vehicle timeouts (vehicle_id)"""
        self.on_vehicle_timeout_callbacks.append(callback)
    
    def get_statistics(self) -> dict:
        """Get receiver statistics"""
        return {
            'messages_received': self.messages_received,
            'messages_dropped': self.messages_dropped,
            'messages_invalid': self.messages_invalid,
            'nearby_vehicles': self.get_vehicle_count(),
            'is_receiving': self.is_receiving,
        }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop()
