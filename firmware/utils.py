"""
Pico-Go LAN Robot - Utilities Module
====================================
Helper functions for common operations.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

import time
from config import DEBUG_MODE


def clamp(value, min_val, max_val):
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def apply_deadzone(value, threshold=0.08):
    """
    Apply deadzone to joystick input.
    
    Args:
        value: Input value (typically -1.0 to 1.0)
        threshold: Deadzone threshold
    
    Returns:
        Value with deadzone applied
    """
    if abs(value) < threshold:
        return 0.0
    return value


def map_range(value, in_min, in_max, out_min, out_max):
    """
    Map a value from one range to another.
    
    Args:
        value: Input value
        in_min: Input range minimum
        in_max: Input range maximum
        out_min: Output range minimum
        out_max: Output range maximum
    
    Returns:
        Mapped value
    """
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def debug_print(message, force=False):
    """
    Print debug message if DEBUG_MODE is enabled.
    
    Args:
        message: Message to print
        force: Force print even if DEBUG_MODE is False
    """
    if DEBUG_MODE or force:
        timestamp = time.ticks_ms()
        print(f"[{timestamp}] {message}")


def format_ip(ip_tuple):
    """
    Format IP address tuple to string.
    
    Args:
        ip_tuple: IP address as tuple (e.g., (10, 42, 0, 123))
    
    Returns:
        IP address as string (e.g., "10.42.0.123")
    """
    return ".".join(str(x) for x in ip_tuple)


def get_uptime_ms():
    """
    Get system uptime in milliseconds.
    
    Returns:
        Uptime in milliseconds
    """
    return time.ticks_ms()


def time_diff_ms(start_ticks, end_ticks):
    """
    Calculate time difference accounting for tick rollover.
    
    Args:
        start_ticks: Start time from time.ticks_ms()
        end_ticks: End time from time.ticks_ms()
    
    Returns:
        Time difference in milliseconds
    """
    return time.ticks_diff(end_ticks, start_ticks)


class RateLimiter:
    """
    Simple rate limiter for periodic tasks.
    """
    
    def __init__(self, interval_ms):
        """
        Initialize rate limiter.
        
        Args:
            interval_ms: Minimum interval between calls in milliseconds
        """
        self.interval_ms = interval_ms
        self.last_call = 0
    
    def ready(self):
        """
        Check if enough time has passed since last call.
        
        Returns:
            True if ready to execute
        """
        now = time.ticks_ms()
        if time_diff_ms(self.last_call, now) >= self.interval_ms:
            self.last_call = now
            return True
        return False
    
    def reset(self):
        """Reset the rate limiter."""
        self.last_call = 0


class MovingAverage:
    """
    Calculate moving average for smoothing values.
    """
    
    def __init__(self, size=5):
        """
        Initialize moving average calculator.
        
        Args:
            size: Number of samples to average
        """
        self.size = size
        self.values = []
    
    def add(self, value):
        """
        Add a new value and return current average.
        
        Args:
            value: New value to add
        
        Returns:
            Current moving average
        """
        self.values.append(value)
        if len(self.values) > self.size:
            self.values.pop(0)
        return sum(self.values) / len(self.values)
    
    def reset(self):
        """Clear all stored values."""
        self.values = []
    
    def get_average(self):
        """
        Get current average without adding new value.
        
        Returns:
            Current moving average or 0 if no values
        """
        if not self.values:
            return 0
        return sum(self.values) / len(self.values)
