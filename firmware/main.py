"""
Pico-Go LAN Robot - Main Entry Point
====================================
Orchestrates all subsystems and runs the main control loop.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

import uasyncio as asyncio
import time
from config import STATE_BOOT, MAIN_LOOP_MS
from utils import debug_print

# Import all subsystems
import wifi
import motor
import lcd_status
import watchdog as wd
import ws_server
import calibration


class RobotController:
    """
    Main robot controller - orchestrates all subsystems.
    """
    
    def __init__(self):
        """Initialize robot controller."""
        self.wifi_manager = None
        self.motor_controller = None
        self.lcd_display = None
        self.safety_controller = None
        self.ws_server = None
        self.calibration_manager = None
        self.running = False
        
        debug_print("=== Pico-Go LAN Robot ===", force=True)
        debug_print("Initializing...", force=True)
    
    async def initialize(self):
        """Initialize all subsystems in proper order."""
        try:
            # 1. Initialize LCD first for visual feedback
            debug_print("Initializing LCD...")
            self.lcd_display = lcd_status.initialize()
            if self.lcd_display:
                self.lcd_display.set_state(STATE_BOOT)
            
            # 2. Initialize motor controller
            debug_print("Initializing motor controller...")
            self.motor_controller = motor.initialize()
            
            # 3. Initialize safety controller
            debug_print("Initializing safety controller...")
            self.safety_controller = wd.initialize(self.motor_controller, self.lcd_display)
            
            # 4. Connect to Wi-Fi
            debug_print("Connecting to Wi-Fi...", force=True)
            self.wifi_manager = await wifi.initialize()
            
            if not self.wifi_manager or not self.wifi_manager.is_connected():
                raise Exception("Failed to connect to Wi-Fi")
            
            # Get robot ID from config or use default
            robot_id = "picogo1"  # TODO: Move to config file
            
            # 4.5. Initialize calibration manager
            debug_print("Initializing calibration...")
            self.calibration_manager = calibration.initialize(robot_id)
            
            # Apply motor balance from calibration
            self.motor_controller.set_motor_balance(
                self.calibration_manager.get("motor_left_scale", 1.0),
                self.calibration_manager.get("motor_right_scale", 1.0)
            )
            
            # Update LCD with network info
            if self.lcd_display:
                wifi_status = self.wifi_manager.get_status()
                self.lcd_display.set_state(
                    "NET_UP",
                    ip=wifi_status["ip"],
                    rssi=wifi_status["rssi"]
                )
            
            # 5. Initialize WebSocket server with calibration
            debug_print("Initializing WebSocket server...")
            self.ws_server = ws_server.initialize(
                self.motor_controller,
                self.safety_controller,
                self.lcd_display,
                self.calibration_manager
            )
            
            # 6. Mark startup complete and arm safety systems
            self.safety_controller.startup_complete_ok()
            
            debug_print("=== Initialization Complete ===", force=True)
            debug_print(f"IP Address: {self.wifi_manager.get_ip()}", force=True)
            debug_print("Waiting for controller connection...", force=True)
            
            return True
            
        except Exception as e:
            debug_print(f"Initialization error: {e}", force=True)
            if self.lcd_display:
                self.lcd_display.show_error(f"Init Error: {e}")
            return False
    
    async def run(self):
        """Main control loop."""
        self.running = True
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._watchdog_task()),
            asyncio.create_task(self._server_task()),
            asyncio.create_task(self._status_update_task())
        ]
        
        try:
            # Run main loop
            while self.running:
                # Check safety systems
                if not self.safety_controller.check_safety():
                    debug_print("Safety check failed")
                
                # Check Wi-Fi connection
                if not self.wifi_manager.is_connected():
                    debug_print("Wi-Fi disconnected - attempting reconnect", force=True)
                    await self.wifi_manager.reconnect()
                
                # Main loop delay
                await asyncio.sleep_ms(MAIN_LOOP_MS)
        
        except KeyboardInterrupt:
            debug_print("Keyboard interrupt received", force=True)
        
        except Exception as e:
            debug_print(f"Main loop error: {e}", force=True)
        
        finally:
            await self.shutdown()
    
    async def _watchdog_task(self):
        """Background watchdog monitoring task."""
        await self.safety_controller.watchdog.monitor_loop()
    
    async def _server_task(self):
        """Background UDP server task (low latency)."""
        # Use UDP for maximum performance and lowest latency
        await ws_server.udp_server(
            self.motor_controller,
            self.safety_controller,
            self.lcd_display,
            self.calibration_manager
        )
    
    async def _status_update_task(self):
        """Periodic status update task."""
        while self.running:
            # Update telemetry values only (no LCD refresh during driving)
            if self.lcd_display and self.wifi_manager:
                wifi_status = self.wifi_manager.get_status()
                if wifi_status["connected"]:
                    # update_telemetry() does NOT trigger display refresh anymore
                    self.lcd_display.update_telemetry(rssi=wifi_status["rssi"])
            
            # Status check every 1 second
            await asyncio.sleep(1)
    
    async def shutdown(self):
        """Gracefully shutdown all subsystems."""
        debug_print("=== Shutting Down ===", force=True)
        self.running = False
        
        # Stop motors
        if self.motor_controller:
            self.motor_controller.stop()
            self.motor_controller.disable()
        
        # Stop WebSocket server
        if self.ws_server:
            self.ws_server.stop()
        
        # Disconnect Wi-Fi
        if self.wifi_manager:
            self.wifi_manager.disconnect()
        
        # Turn off LCD backlight
        if self.lcd_display:
            self.lcd_display.backlight_off()
        
        debug_print("Shutdown complete", force=True)


async def main():
    """
    Main entry point.
    """
    # Create robot controller
    robot = RobotController()
    
    # Initialize all subsystems
    if await robot.initialize():
        # Run main control loop
        await robot.run()
    else:
        debug_print("Failed to initialize - exiting", force=True)


# Entry point
# Note: MicroPython always runs main.py, so __name__ is always "__main__"
try:
    # Run the async main function
    asyncio.run(main())
except Exception as e:
    debug_print(f"Fatal error: {e}", force=True)
finally:
    debug_print("Program terminated", force=True)
