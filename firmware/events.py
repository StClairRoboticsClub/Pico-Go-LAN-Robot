"""
Pico-Go LAN Robot - Event System
=================================
Simple event system to replace polling and reduce coupling.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

from utils import debug_print


class EventBus:
    """
    Simple event bus for decoupled communication between modules.
    """
    
    def __init__(self):
        """Initialize event bus."""
        self._subscribers = {}
    
    def subscribe(self, event_type, callback):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Event type string (e.g., "charging_mode_requested")
            callback: Callback function to call when event occurs
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        debug_print(f"Subscribed to event: {event_type}")
    
    def publish(self, event_type, data=None):
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Event type string
            data: Optional data to pass to callbacks
        """
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    debug_print(f"Event callback error for {event_type}: {e}")
    
    def unsubscribe(self, event_type, callback):
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Event type string
            callback: Callback function to remove
        """
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)


# Global event bus instance
_event_bus = None


def get_event_bus():
    """
    Get the global event bus instance.
    
    Returns:
        EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Event type constants
EVENT_CHARGING_MODE_REQUESTED = "charging_mode_requested"
EVENT_WIFI_DISCONNECTED = "wifi_disconnected"
EVENT_CLIENT_CONNECTED = "client_connected"
EVENT_CLIENT_DISCONNECTED = "client_disconnected"
EVENT_SAFETY_TRIGGERED = "safety_triggered"

