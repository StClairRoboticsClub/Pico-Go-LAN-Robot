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
- Dim brightness when disconnected (always-on indicator)
- Bright brightness when connected to controller
- Smooth brightness transitions
"""

from machine import Pin
import array
import time
import rp2
from config import (
    PIN_UNDERGLOW, UNDERGLOW_NUM_LEDS, UNDERGLOW_ENABLED,
    UNDERGLOW_BRIGHTNESS_DIM, UNDERGLOW_BRIGHTNESS_BRIGHT,
    ROBOT_COLOR, ROBOT_ID,
    STATE_BOOT, STATE_NET_UP, STATE_CLIENT_OK, STATE_DRIVING, STATE_LINK_LOST
)
from utils import debug_print


# PIO program for WS2812 (from Waveshare demo)
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
    """Control WS2812B underglow LEDs with brightness management using PIO."""
    
    def __init__(self):
        """Initialize underglow controller."""
        self.enabled = UNDERGLOW_ENABLED
        self.pin = PIN_UNDERGLOW
        self.num = UNDERGLOW_NUM_LEDS
        self.brightness = UNDERGLOW_BRIGHTNESS_DIM / 255.0  # Normalize to 0.0-1.0
        self.sm = None
        self.ar = None
        self.base_color = ROBOT_COLOR  # RGB tuple (0-255, 0-255, 0-255)
        
        if not self.enabled:
            debug_print("Underglow disabled in config", force=True)
            return
        
        try:
            # Initialize PIO state machine for WS2812 (exactly like Waveshare)
            self.sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(self.pin))
            self.sm.active(1)
            
            # Create LED array
            self.ar = array.array("I", [0 for _ in range(self.num)])
            
            # Set initial dim state
            self.set_brightness(UNDERGLOW_BRIGHTNESS_DIM)
            self.pixels_show()
            
            debug_print(f"Underglow initialized: {self.num} LEDs on GP{self.pin}", force=True)
            debug_print(f"Robot ID {ROBOT_ID} color: RGB{self.base_color}", force=True)
            
        except Exception as e:
            debug_print(f"Underglow initialization error: {e}", force=True)
            self.enabled = False
    
    def set_brightness(self, brightness):
        """
        Set target brightness level (0-255).
        
        Args:
            brightness: Target brightness (0-255)
        """
        if not self.enabled or not self.sm:
            return
        
        # Normalize to 0.0-1.0 range (like Waveshare)
        self.brightness = max(0.0, min(1.0, brightness / 255.0))
    
    def set_color(self, r, g, b):
        """
        Set base color (overrides robot ID color).
        
        Args:
            r, g, b: RGB values (0-255)
        """
        if not self.enabled or not self.sm:
            return
        
        self.base_color = (r, g, b)
    
    def pixels_set(self, i, color):
        """Set a single LED color (Waveshare compatible)."""
        # Store as (G<<16) + (R<<8) + B like Waveshare
        self.ar[i] = (color[1] << 16) + (color[0] << 8) + color[2]
    
    def pixels_fill(self, color):
        """Fill all LEDs with the same color (Waveshare compatible)."""
        for i in range(self.num):
            self.pixels_set(i, color)
    
    def pixels_show(self):
        """Update the LEDs with brightness applied (exactly like Waveshare)."""
        if not self.enabled or not self.sm:
            return
        
        try:
            # Apply brightness scaling (Waveshare method)
            dimmer_ar = array.array("I", [0 for _ in range(self.num)])
            for i, c in enumerate(self.ar):
                r = int(((c >> 8) & 0xFF) * self.brightness)
                g = int(((c >> 16) & 0xFF) * self.brightness)
                b = int((c & 0xFF) * self.brightness)
                dimmer_ar[i] = (g << 16) + (r << 8) + b
            
            # Send to PIO state machine
            self.sm.put(dimmer_ar, 8)
            
        except Exception as e:
            debug_print(f"Underglow update error: {e}")
    
    def update(self):
        """Update LED colors with robot's base color."""
        if not self.enabled or not self.sm:
            return
        
        # Fill all LEDs with robot color
        self.pixels_fill(self.base_color)
        self.pixels_show()
    
    def set_state(self, state):
        """
        Update underglow based on robot state.
        
        Args:
            state: Robot state (STATE_BOOT, STATE_NET_UP, etc.)
        """
        if not self.enabled or not self.sm:
            return
        
        try:
            # Determine brightness based on state
            if state in [STATE_CLIENT_OK, STATE_DRIVING]:
                # Connected - bright
                new_brightness = UNDERGLOW_BRIGHTNESS_BRIGHT
            elif state == STATE_BOOT:
                # Booting - very dim
                new_brightness = UNDERGLOW_BRIGHTNESS_DIM // 2
            else:
                # Disconnected/waiting - dim
                new_brightness = UNDERGLOW_BRIGHTNESS_DIM
            
            # Update brightness if changed
            new_brightness_normalized = new_brightness / 255.0
            if abs(new_brightness_normalized - self.brightness) > 0.01:
                self.set_brightness(new_brightness)
                self.update()
                debug_print(f"Underglow brightness: {new_brightness} (state: {state})")
        
        except Exception as e:
            debug_print(f"Underglow state update error: {e}")
    
    def pulse(self, duration_ms=1000):
        """
        Pulse effect - fade from dim to bright and back.
        Useful for boot/connection events.
        
        Args:
            duration_ms: Total pulse duration in milliseconds
        """
        if not self.enabled or not self.sm:
            return
        
        try:
            steps = 20
            step_delay = duration_ms // (steps * 2)
            
            # Fade up
            for i in range(steps):
                brightness = UNDERGLOW_BRIGHTNESS_DIM + (
                    (UNDERGLOW_BRIGHTNESS_BRIGHT - UNDERGLOW_BRIGHTNESS_DIM) * i // steps
                )
                self.set_brightness(brightness)
                self.update()
                time.sleep_ms(step_delay)
            
            # Fade down
            for i in range(steps):
                brightness = UNDERGLOW_BRIGHTNESS_BRIGHT - (
                    (UNDERGLOW_BRIGHTNESS_BRIGHT - UNDERGLOW_BRIGHTNESS_DIM) * i // steps
                )
                self.set_brightness(brightness)
                self.update()
                time.sleep_ms(step_delay)
        
        except Exception as e:
            debug_print(f"Underglow pulse error: {e}")
    
    def off(self):
        """Turn off all LEDs."""
        if not self.enabled or not self.sm:
            return
        
        try:
            # Set all LEDs to black (off) using Waveshare method
            self.pixels_fill((0, 0, 0))
            self.pixels_show()
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
