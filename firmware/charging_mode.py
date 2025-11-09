"""
Pico-Go LAN Robot - Charging Mode
==================================
Low-power charging mode activated remotely via controller.
Suspends all operations until disabled.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

import machine
import time
from utils import debug_print


class ChargingMode:
    """
    Manages low-power charging mode.
    
    When activated:
    - All subsystems are disabled (motors, WiFi, LEDs)
    - Only LCD shows "CHARGING" status
    - Controller command required to resume operation
    """
    
    def __init__(self):
        """Initialize charging mode controller."""
        self.charging = False
    
    def is_charging(self):
        """Check if currently in charging mode."""
        return self.charging
    
    def enter_charging_mode(self, motor_controller, wifi_manager, underglow, lcd_display):
        """
        Enter charging mode - disable all subsystems.
        
        Args:
            motor_controller: Motor controller instance
            wifi_manager: WiFi manager instance
            underglow: Underglow LED controller
            lcd_display: LCD display instance
        """
        debug_print("=== ENTERING CHARGING MODE ===", force=True)
        self.charging = True
        
        # Disable motors
        if motor_controller:
            debug_print("Disabling motors...")
            motor_controller.stop()
            motor_controller.disable()
        
        # Disconnect WiFi to save power
        if wifi_manager:
            debug_print("Disconnecting WiFi...")
            wifi_manager.disconnect()
            wifi_manager.wlan.active(False)
        
        # Turn off underglow LEDs
        if underglow:
            debug_print("Turning off underglow...")
            underglow.set_color_all((0, 0, 0))  # Black = off
        
        # Show charging screen on LCD
        if lcd_display:
            debug_print("Displaying charging screen...")
            self._show_charging_screen(lcd_display)
        
        debug_print("Charging mode active - press BOOTSEL to resume", force=True)
    
    def exit_charging_mode(self):
        """Exit charging mode - robot will restart."""
        debug_print("=== EXITING CHARGING MODE ===", force=True)
        debug_print("Resetting to resume normal operation...", force=True)
        self.charging = False
        
        # Perform a soft reset to restart the robot cleanly
        time.sleep(0.5)
        machine.soft_reset()
    
    def _show_charging_screen(self, lcd_display):
        """Display charging mode screen on LCD."""
        if not lcd_display or not hasattr(lcd_display, 'display'):
            return
        
        try:
            # Clear screen to black
            lcd_display.display.fill(0x0000)  # Black
            
            # Yellow border
            yellow = 0x07FF
            green = 0xF800
            
            # Draw border
            for i in range(3):
                lcd_display.display.rect(i, i, 240-2*i, 135-2*i, yellow)
            
            # Title
            lcd_display.display.text("CHARGING MODE", 55, 20, yellow)
            lcd_display.display.text("CHARGING MODE", 56, 20, yellow)
            lcd_display.display.text("CHARGING MODE", 55, 21, yellow)
            
            # Battery icon (simple rectangle representation)
            # Battery body
            lcd_display.display.rect(80, 50, 80, 40, green)
            lcd_display.display.rect(81, 51, 78, 38, green)
            
            # Battery terminal
            lcd_display.display.fill_rect(160, 60, 5, 20, green)
            
            # Charging bars (animated look)
            lcd_display.display.fill_rect(85, 55, 15, 30, green)
            lcd_display.display.fill_rect(105, 55, 15, 30, green)
            lcd_display.display.fill_rect(125, 55, 15, 30, green)
            
            # Instructions
            lcd_display.display.text("All systems", 75, 105, yellow)
            lcd_display.display.text("suspended", 80, 115, yellow)
            
            # Update display
            lcd_display.display.show()
            
            debug_print("Charging screen displayed")
            
        except Exception as e:
            debug_print(f"Error showing charging screen: {e}")
    
    def monitor_loop(self, motor_controller, wifi_manager, underglow, lcd_display):
        """
        Blocking loop that monitors charging mode status.
        Returns when controller sends disable command.
        
        This is a simple blocking loop to minimize power consumption.
        """
        debug_print("Starting charging mode monitor loop...")
        
        # Import here to avoid circular dependency
        import ws_server
        
        while self.charging:
            # Check if controller requested exit
            if ws_server.charging_mode_requested == False:
                debug_print("Controller requested exit - disabling charging mode")
                ws_server.charging_mode_requested = None  # Clear flag
                self.exit_charging_mode()
                return
            
            time.sleep_ms(100)


def initialize():
    """
    Initialize charging mode controller.
    
    Returns:
        ChargingMode instance
    """
    return ChargingMode()
