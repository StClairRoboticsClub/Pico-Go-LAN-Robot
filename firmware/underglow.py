"""
Pico-Go LAN Robot - Underglow LED Module
========================================
WS2812B RGB LED control for robot identification and status indication.
Uses PIO (Programmable I/O) state machine for WS2812 control.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT

Features:
- Unique color per robot ID for easy identification
- 100% brightness always
- Flashing animations based on connection state:
  - Disconnected: Flash between robot color and RED
  - Connected: Flash between robot color and YELLOW
  - Driving: Solid robot color
"""

from machine import Pin
import array
import time
import rp2
from config import (
    PIN_UNDERGLOW, UNDERGLOW_NUM_LEDS, UNDERGLOW_ENABLED,
    UNDERGLOW_BRIGHTNESS, ROBOT_COLOR, ROBOT_ID,
    STATE_BOOT, STATE_NET_UP, STATE_CLIENT_OK, STATE_DRIVING, STATE_LINK_LOST
)
from utils import debug_print


# PIO program for WS2812 (from Waveshare Pico-Go documentation)
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()


class UnderglowController:
    """Control WS2812B underglow LEDs with flashing animations."""
    
    def __init__(self):
        """Initialize underglow controller."""
        self.enabled = UNDERGLOW_ENABLED
        self.pin = PIN_UNDERGLOW
        self.num = UNDERGLOW_NUM_LEDS
        self.sm = None
        self.ar = None
        self.robot_color = ROBOT_COLOR  # RGB tuple (0-255, 0-255, 0-255)
        self.current_state = None
        self.flash_state = False
        self.last_flash_time = 0
        self.flash_interval_ms = 500  # Flash every 500ms
        
        if not self.enabled:
            debug_print("Underglow disabled in config", force=True)
            return
        
        try:
            # Initialize PIO state machine for WS2812 (Waveshare Pico-Go v2)
            self.sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(self.pin))
            self.sm.active(1)
            
            # Create LED array
            self.ar = array.array("I", [0 for _ in range(self.num)])
            
            # Set initial state - solid robot color
            self.set_color_all(self.robot_color)
            
            debug_print(f"Underglow initialized: {self.num} LEDs on GP{self.pin}", force=True)
            debug_print(f"Robot ID {ROBOT_ID} color: RGB{self.robot_color}", force=True)
            
        except Exception as e:
            debug_print(f"Underglow initialization error: {e}", force=True)
            self.enabled = False
    
    def set_color_all(self, color):
        """
        Set all LEDs to the same color at full brightness.
        
        Args:
            color: RGB tuple (0-255, 0-255, 0-255)
        """
        if not self.enabled or not self.sm:
            return
        
        try:
            r, g, b = color
            # WS2812 expects GRB format
            grb_value = (g << 16) | (r << 8) | b
            
            for i in range(self.num):
                self.ar[i] = grb_value
            
            # Send to LEDs
            self.sm.put(self.ar, 8)
            
        except Exception as e:
            debug_print(f"Underglow set_color error: {e}")
    
    def update_flash(self):
        """Update flashing animation based on time. Only flashes for disconnected states."""
        if not self.enabled or not self.sm:
            return
        
        # Only flash for BOOT and LINK_LOST states
        # CLIENT_OK, NET_UP, and DRIVING should stay solid
        if self.current_state not in [STATE_BOOT, STATE_LINK_LOST]:
            return
        
        current_time = time.ticks_ms()
        
        # Check if it's time to toggle flash state
        if time.ticks_diff(current_time, self.last_flash_time) >= self.flash_interval_ms:
            self.flash_state = not self.flash_state
            self.last_flash_time = current_time
            
            # Update color based on state - only flash for disconnected states
            if self.current_state in [STATE_LINK_LOST, STATE_BOOT]:
                # Flash between robot color and RED
                if self.flash_state:
                    self.set_color_all(self.robot_color)
                else:
                    self.set_color_all((255, 0, 0))  # RED
    
    def set_state(self, state):
        """
        Update underglow based on robot state.
        
        Args:
            state: Robot state (STATE_BOOT, STATE_NET_UP, etc.)
        """
        if not self.enabled or not self.sm:
            return
        
        try:
            self.current_state = state
            self.last_flash_time = time.ticks_ms()
            self.flash_state = False
            
            if state == STATE_DRIVING:
                # Solid robot color when driving
                self.set_color_all(self.robot_color)
                debug_print(f"Underglow: DRIVING - solid {self.robot_color}")
            elif state in [STATE_LINK_LOST, STATE_BOOT]:
                # Start flashing robot color / RED (disconnected)
                self.set_color_all(self.robot_color)
                debug_print(f"Underglow: {state} - flash robot/RED")
            elif state in [STATE_NET_UP, STATE_CLIENT_OK]:
                # Solid robot color when connected
                self.set_color_all(self.robot_color)
                debug_print(f"Underglow: {state} - solid {self.robot_color}")
        
        except Exception as e:
            debug_print(f"Underglow state update error: {e}")
    
    def off(self):
        """Turn off all LEDs."""
        if not self.enabled or not self.sm:
            return
        
        try:
            self.set_color_all((0, 0, 0))
        except Exception as e:
            debug_print(f"Underglow off error: {e}")


# Global underglow instance
underglow_controller = None


def initialize():
    """Initialize the global underglow controller."""
    global underglow_controller
    if underglow_controller is None:
        underglow_controller = UnderglowController()
    return underglow_controller


def get_controller():
    """Get the global underglow controller instance."""
    return underglow_controller
