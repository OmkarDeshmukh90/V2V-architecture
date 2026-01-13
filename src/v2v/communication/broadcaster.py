"""
V2V Communication Broadcaster - Handles sending vehicle data to nearby vehicles
"""
import socket
import threading
import time
from typing import Optional, Callable
from ..obu.obu import OBU
from .message import V2VMessage


class V2VBroadcaster:
    """
    Broadcasts vehicle data to nearby vehicles.
    
    Uses UDP broadcast for real-time, low-latency communication.
    """
    
    def __init__(self, obu: OBU, port: int = 5555, 
                 broadcast_frequency: float = 10.0,
                 base_radius: float = 100.0,
                 max_radius: float = 500.0,
                 speed_factor: float = 5.0):
        """
        Initialize the V2V broadcaster.
        
        Args:
            obu: On-Board Unit instance
            port: UDP port for broadcasting
            broadcast_frequency: Broadcast frequency in Hz
            base_radius: Base broadcast radius in meters
            max_radius: Maximum broadcast radius in meters
            speed_factor: Speed factor for dynamic radius calculation
        """
        self.obu = obu
        self.port = port
        self.broadcast_frequency = broadcast_frequency
        self.base_radius = base_radius
        self.max_radius = max_radius
        self.speed_factor = speed_factor
        
        # Socket for broadcasting
        self.socket = None
        
        # Broadcasting state
        self.is_broadcasting = False
        self.broadcast_thread = None
        self.sequence_number = 0
        
        # Statistics
        self.messages_sent = 0
        self.last_broadcast_time = 0
        
        # Callbacks
        self.on_broadcast_callbacks = []
    
    def start(self):
        """Start broadcasting vehicle data"""
        if self.is_broadcasting:
            return
        
        # Create UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Start broadcast thread
        self.is_broadcasting = True
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.broadcast_thread.start()
        
        print(f"V2V Broadcaster started on port {self.port}")
    
    def stop(self):
        """Stop broadcasting"""
        if not self.is_broadcasting:
            return
        
        self.is_broadcasting = False
        
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=2.0)
        
        if self.socket:
            self.socket.close()
            self.socket = None
        
        print("V2V Broadcaster stopped")
    
    def _broadcast_loop(self):
        """Main broadcast loop"""
        interval = 1.0 / self.broadcast_frequency
        
        while self.is_broadcasting:
            try:
                start_time = time.time()
                
                # Get current vehicle data
                vehicle_data = self.obu.get_current_data()
                
                # Calculate dynamic broadcast radius
                broadcast_radius = self.obu.get_broadcast_radius(
                    self.base_radius, self.max_radius, self.speed_factor
                )
                
                # Create and send message
                message = V2VMessage(
                    message_type=V2VMessage.MESSAGE_TYPE_BROADCAST,
                    vehicle_data=vehicle_data,
                    sequence_number=self.sequence_number,
                    broadcast_radius=broadcast_radius
                )
                
                self._send_message(message)
                
                # Update statistics
                self.sequence_number += 1
                self.messages_sent += 1
                self.last_broadcast_time = time.time()
                
                # Notify callbacks
                for callback in self.on_broadcast_callbacks:
                    try:
                        callback(message)
                    except Exception as e:
                        print(f"Error in broadcast callback: {e}")
                
                # Sleep for remaining interval time
                elapsed = time.time() - start_time
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Error in broadcast loop: {e}")
                time.sleep(interval)
    
    def _send_message(self, message: V2VMessage):
        """Send message via UDP broadcast"""
        try:
            data = message.serialize()
            # Broadcast to all on local network
            self.socket.sendto(data, ('<broadcast>', self.port))
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def send_emergency_message(self):
        """Send emergency broadcast with high priority"""
        vehicle_data = self.obu.get_current_data()
        broadcast_radius = self.max_radius  # Use max radius for emergency
        
        message = V2VMessage(
            message_type=V2VMessage.MESSAGE_TYPE_EMERGENCY,
            vehicle_data=vehicle_data,
            sequence_number=self.sequence_number,
            broadcast_radius=broadcast_radius
        )
        
        self._send_message(message)
        self.sequence_number += 1
        print(f"Emergency message sent from {self.obu.vehicle_id}")
    
    def register_broadcast_callback(self, callback: Callable[[V2VMessage], None]):
        """Register callback to be called after each broadcast"""
        self.on_broadcast_callbacks.append(callback)
    
    def get_statistics(self) -> dict:
        """Get broadcaster statistics"""
        return {
            'messages_sent': self.messages_sent,
            'last_broadcast_time': self.last_broadcast_time,
            'is_broadcasting': self.is_broadcasting,
            'sequence_number': self.sequence_number,
        }
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop()
