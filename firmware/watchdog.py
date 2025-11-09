"""
Pico-Go LAN Robot - Watchdog Safety Module
==========================================
Monitors communication and enforces automatic motor stop on timeout.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

import time
import uasyncio as asyncio
from config import WATCHDOG_TIMEOUT_MS, STATE_LINK_LOST, STATE_DRIVING
from utils import debug_print, time_diff_ms


class Watchdog:
    """
    Communication watchdog timer.
    
    Automatically stops motors if no valid control packet received
    within the timeout period.
    """
    
    def __init__(self, motor_controller, lcd_display, underglow=None):
        """
        Initialize watchdog.
        
        Args:
            motor_controller: Motor controller instance to stop on timeout
            lcd_display: LCD display instance to show warnings
            underglow: Underglow LED controller instance (optional)
        """
        self.motor_controller = motor_controller
        self.lcd_display = lcd_display
        self.underglow = underglow
        self.last_packet_time = 0
        self.timeout_ms = WATCHDOG_TIMEOUT_MS
        self.enabled = False
        self.timed_out = False
        self.packet_count = 0
        
        debug_print(f"Watchdog initialized (timeout: {self.timeout_ms}ms)")
    
    def enable(self):
        """Enable watchdog monitoring."""
        self.enabled = True
        self.feed()  # Reset timer when enabling
        debug_print("Watchdog enabled")
    
    def disable(self):
        """Disable watchdog monitoring."""
        self.enabled = False
        self.timed_out = False
        debug_print("Watchdog disabled")
    
    def feed(self):
        """
        Feed the watchdog (update last packet time).
        
        Call this whenever a valid control packet is received.
        """
        self.last_packet_time = time.ticks_ms()
        self.packet_count += 1
        
        # If we were timed out, recover
        if self.timed_out:
            debug_print("Watchdog: Communication recovered", force=True)
            self.timed_out = False
            if self.lcd_display and self.motor_controller:
                self.lcd_display.set_state(STATE_DRIVING)
            # Update underglow back to driving state on recovery
            if self.underglow:
                self.underglow.set_state(STATE_DRIVING)
    
    def check_timeout(self):
        """
        Check if timeout has occurred.
        
        Returns:
            True if timed out, False otherwise
        """
        if not self.enabled:
            return False
        
        now = time.ticks_ms()
        elapsed = time_diff_ms(self.last_packet_time, now)
        
        if elapsed > self.timeout_ms and not self.timed_out:
            self._handle_timeout()
            return True
        
        return self.timed_out
    
    def _handle_timeout(self):
        """Handle timeout event - stop motors and update display."""
        debug_print("WATCHDOG TIMEOUT: Stopping motors", force=True)
        self.timed_out = True
        
        # Stop motors immediately
        if self.motor_controller:
            self.motor_controller.stop()
        
        # Update display
        if self.lcd_display:
            self.lcd_display.set_state(STATE_LINK_LOST)
        
        # Dim underglow
        if self.underglow:
            self.underglow.set_state(STATE_LINK_LOST)
    
    def get_status(self):
        """
        Get watchdog status.
        
        Returns:
            Dictionary with watchdog status
        """
        now = time.ticks_ms()
        elapsed = time_diff_ms(self.last_packet_time, now)
        
        return {
            "enabled": self.enabled,
            "timed_out": self.timed_out,
            "elapsed_ms": elapsed,
            "timeout_ms": self.timeout_ms,
            "packets_received": self.packet_count
        }
    
    def reset_statistics(self):
        """Reset packet count and statistics."""
        self.packet_count = 0
        debug_print("Watchdog statistics reset")
    
    async def monitor_loop(self):
        """
        Async monitoring loop.
        
        Continuously checks for timeout and handles safety.
        Run this as a background task.
        """
        debug_print("Watchdog monitor loop started")
        
        while True:
            if self.enabled:
                self.check_timeout()
            
            # Check every 50ms for responsive timeout detection
            await asyncio.sleep_ms(50)


class SafetyController:
    """
    Higher-level safety controller with multiple safety mechanisms.
    """
    
    def __init__(self, motor_controller, lcd_display, underglow=None):
        """
        Initialize safety controller.
        
        Args:
            motor_controller: Motor controller instance
            lcd_display: LCD display instance
            underglow: Underglow LED controller instance (optional)
        """
        self.motor_controller = motor_controller
        self.lcd_display = lcd_display
        self.underglow = underglow
        self.watchdog = Watchdog(motor_controller, lcd_display, underglow)
        self.e_stop_active = False
        self.startup_complete = False
        
        debug_print("Safety controller initialized")
    
    def startup_complete_ok(self):
        """Mark startup as complete and enable safety systems."""
        self.startup_complete = True
        self.motor_controller.enable()  # Enable motor controller (no STBY pin on Waveshare)
        self.watchdog.enable()
        debug_print("Safety systems armed - motors ready")
    
    def trigger_e_stop(self, reason="Manual trigger"):
        """
        Trigger emergency stop.
        
        Args:
            reason: Reason for E-stop
        """
        debug_print(f"E-STOP TRIGGERED: {reason}", force=True)
        self.e_stop_active = True
        
        # Stop motors immediately
        self.motor_controller.stop()
        self.motor_controller.disable()
        
        # Disable watchdog (we're already stopped)
        self.watchdog.disable()
        
        # Update display
        if self.lcd_display:
            self.lcd_display.set_state("E_STOP")
    
    def clear_e_stop(self):
        """Clear emergency stop and resume normal operation."""
        if not self.e_stop_active:
            return
        
        debug_print("E-stop cleared - resuming operation", force=True)
        self.e_stop_active = False
        
        # Re-enable systems
        self.motor_controller.enable()
        self.watchdog.enable()
        
        debug_print("Systems re-enabled")
    
    def feed_watchdog(self):
        """Feed the watchdog (wrapper for convenience)."""
        self.watchdog.feed()
    
    def check_safety(self):
        """
        Check all safety systems.
        
        Returns:
            True if all systems OK, False if any safety triggered
        """
        if self.e_stop_active:
            return False
        
        if self.watchdog.check_timeout():
            return False
        
        return True
    
    def get_status(self):
        """
        Get comprehensive safety status.
        
        Returns:
            Dictionary with all safety system states
        """
        return {
            "startup_complete": self.startup_complete,
            "e_stop_active": self.e_stop_active,
            "watchdog": self.watchdog.get_status(),
            "motor_enabled": self.motor_controller.enabled if self.motor_controller else False
        }


# Global safety controller instance
safety_controller = None


def initialize(motor_controller, lcd_display, underglow=None):
    """
    Initialize the global safety controller.
    
    Args:
        motor_controller: Motor controller instance
        lcd_display: LCD display instance
        underglow: Underglow LED controller instance (optional)
    
    Returns:
        SafetyController instance
    """
    global safety_controller
    safety_controller = SafetyController(motor_controller, lcd_display, underglow)
    return safety_controller


def get_controller():
    """
    Get the global safety controller instance.
    
    Returns:
        SafetyController instance or None
    """
    return safety_controller
