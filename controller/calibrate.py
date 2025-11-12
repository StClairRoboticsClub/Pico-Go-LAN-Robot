#!/usr/bin/env python3
"""
Pico-Go LAN Robot - Interactive Calibration Tool
================================================
Calibrate robot steering trim and motor balance in real-time.

⚠️  THIS IS A SUBSIDIARY MODULE - DO NOT RUN DIRECTLY!
    Always launch through robot_master_gui.py

This module is launched as a subprocess by the Master GUI.
It should NOT be run standalone or built as a separate application.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

import asyncio
import json
import socket
import sys
import time
from typing import Optional

import pygame

# Protocol constants
ROBOT_PORT = 8765

# Import from controller_xbox
from controller_xbox import (
    XboxController, apply_deadzone, apply_expo, clamp,
    AXIS_LEFT_X, AXIS_RIGHT_TRIGGER, AXIS_LEFT_TRIGGER,
    BUTTON_A, BUTTON_B, BUTTON_START,
    THROTTLE_EXPO, STEERING_EXPO, THROTTLE_SENSITIVITY, STEERING_SENSITIVITY
)

# Calibration adjustment speeds
TRIM_ADJUST_STEP = 0.005  # Steering trim adjustment per button press (0.5% increments)
MOTOR_ADJUST_STEP = 0.01  # Motor balance adjustment per button press (1% increments)


class CalibrationTool:
    """Interactive robot calibration tool."""
    
    def __init__(self, robot_ip: str):
        """
        Initialize calibration tool.
        
        Args:
            robot_ip: Robot IP address
        """
        self.robot_ip = robot_ip
        self.robot_port = ROBOT_PORT
        self.controller = XboxController()
        self.sock = None
        self.seq_num = 0
        
        # Current calibration values
        self.steering_trim = 0.0
        self.motor_left_scale = 1.0
        self.motor_right_scale = 1.0
        
        # UI state
        self.last_button_state = {}
        self.calibration_saved = False
    
    async def connect(self) -> bool:
        """Initialize UDP connection to robot."""
        try:
            print(f"🔌 Connecting to robot at {self.robot_ip}:{self.robot_port}...")
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(1.0)
            
            # Request current calibration
            await self._request_calibration()
            
            print("✅ Connected! Ready to calibrate.")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def _request_calibration(self):
        """Request current calibration from robot."""
        try:
            packet = {
                "cmd": "get_calibration",
                "seq": self.seq_num,
                "ts": int(time.time() * 1000)
            }
            
            message = json.dumps(packet).encode()
            self.sock.sendto(message, (self.robot_ip, self.robot_port))
            self.seq_num += 1
            
            # Wait for response
            try:
                data, _ = self.sock.recvfrom(4096)
                response = json.loads(data.decode())
                
                if "calibration" in response:
                    cal = response["calibration"]
                    self.steering_trim = cal.get("steering_trim", 0.0)
                    self.motor_left_scale = cal.get("motor_left_scale", 1.0)
                    self.motor_right_scale = cal.get("motor_right_scale", 1.0)
                    
                    print(f"📥 Current calibration loaded:")
                    print(f"   Steering Trim: {self.steering_trim:+.3f}")
                    print(f"   Motor Balance: L={self.motor_left_scale:.2f} R={self.motor_right_scale:.2f}")
            except socket.timeout:
                print("⚠️  No calibration response (using defaults)")
                
        except Exception as e:
            print(f"⚠️  Could not fetch calibration: {e}")
    
    async def _send_drive_command(self, throttle: float, steer: float):
        """Send drive command with current calibration applied."""
        if not self.sock:
            return
        
        # Apply calibration
        if abs(throttle) > 0.05:
            steer += self.steering_trim
        
        steer = clamp(steer)
        
        packet = {
            "cmd": "drive",
            "seq": self.seq_num,
            "ts": int(time.time() * 1000),
            "axes": {
                "throttle": round(throttle, 3),
                "steer": round(steer, 3)
            }
        }
        
        message = json.dumps(packet).encode()
        self.sock.sendto(message, (self.robot_ip, self.robot_port))
        self.seq_num += 1
    
    async def _save_calibration(self):
        """Save current calibration to robot."""
        if not self.sock:
            return False
        
        try:
            packet = {
                "cmd": "set_calibration",
                "seq": self.seq_num,
                "ts": int(time.time() * 1000),
                "calibration": {
                    "steering_trim": self.steering_trim,
                    "motor_left_scale": self.motor_left_scale,
                    "motor_right_scale": self.motor_right_scale
                }
            }
            
            message = json.dumps(packet).encode()
            self.sock.sendto(message, (self.robot_ip, self.robot_port))
            self.seq_num += 1
            
            print("\n✅ Calibration saved to robot!")
            self.calibration_saved = True
            return True
            
        except Exception as e:
            print(f"\n❌ Failed to save calibration: {e}")
            return False
    
    def _button_pressed(self, button_id: int) -> bool:
        """Check if button was just pressed (rising edge detection)."""
        current = self.controller.get_button(button_id)
        previous = self.last_button_state.get(button_id, False)
        self.last_button_state[button_id] = current
        return current and not previous
    
    def _print_status(self, throttle: float, steer: float, applied_steer: float):
        """Print current calibration status."""
        print(f"\r🎮 T:{throttle:+.2f} S:{steer:+.2f}→{applied_steer:+.2f} | "
              f"Trim:{self.steering_trim:+.3f} | "
              f"Motors: L={self.motor_left_scale:.2f} R={self.motor_right_scale:.2f} | "
              f"{'💾 SAVED' if self.calibration_saved else '⚠️  UNSAVED'}   ",
              end='', flush=True)
    
    async def run(self):
        """Run calibration tool main loop."""
        if not self.controller.is_connected():
            print("❌ No controller connected!")
            return 1
        
        if not await self.connect():
            return 1
        
        print("\n" + "=" * 70)
        print("🔧 CALIBRATION MODE")
        print("=" * 70)
        print("📖 Instructions:")
        print("   1. Drive forward at medium speed")
        print("   2. Observe drift direction")
        print("   3. Adjust calibration:")
        print()
        print("      D-Pad ↑/↓    : Adjust steering trim")
        print("      D-Pad ←/→    : Adjust left motor balance")
        print("      LB/RB        : Adjust right motor balance")
        print()
        print("   4. Press A to SAVE calibration")
        print("   5. Press B to RESET to defaults")
        print("   6. Press START to EXIT")
        print("=" * 70)
        print()
        
        control_rate = 1.0 / 30.0  # 30 Hz
        last_update = time.time()
        
        try:
            while True:
                # Check for exit
                if self.controller.get_button(BUTTON_START):
                    break
                
                # Handle calibration adjustments (check every loop for responsiveness)
                pygame.event.pump()
                
                # D-Pad buttons (may vary by controller - using hat or buttons)
                # Try to get hat position
                if self.controller.joystick.get_numhats() > 0:
                    hat_x, hat_y = self.controller.joystick.get_hat(0)
                    
                    if hat_y > 0:  # Up
                        self.steering_trim += TRIM_ADJUST_STEP
                        self.calibration_saved = False
                        await asyncio.sleep(0.1)
                    elif hat_y < 0:  # Down
                        self.steering_trim -= TRIM_ADJUST_STEP
                        self.calibration_saved = False
                        await asyncio.sleep(0.1)
                    
                    if hat_x < 0:  # Left
                        self.motor_left_scale -= MOTOR_ADJUST_STEP
                        self.motor_left_scale = clamp(self.motor_left_scale, 0.5, 1.0)
                        self.calibration_saved = False
                        await asyncio.sleep(0.1)
                    elif hat_x > 0:  # Right
                        self.motor_left_scale += MOTOR_ADJUST_STEP
                        self.motor_left_scale = clamp(self.motor_left_scale, 0.5, 1.0)
                        self.calibration_saved = False
                        await asyncio.sleep(0.1)
                
                # Bumpers for right motor
                if self.controller.get_button(4):  # LB - reduce right motor
                    self.motor_right_scale -= MOTOR_ADJUST_STEP
                    self.motor_right_scale = clamp(self.motor_right_scale, 0.5, 1.0)
                    self.calibration_saved = False
                    await asyncio.sleep(0.1)
                elif self.controller.get_button(5):  # RB - increase right motor
                    self.motor_right_scale += MOTOR_ADJUST_STEP
                    self.motor_right_scale = clamp(self.motor_right_scale, 0.5, 1.0)
                    self.calibration_saved = False
                    await asyncio.sleep(0.1)
                
                # Save/Reset buttons
                if self._button_pressed(BUTTON_A):
                    await self._save_calibration()
                
                if self._button_pressed(BUTTON_B):
                    print("\n⚠️  Resetting to defaults...")
                    self.steering_trim = 0.0
                    self.motor_left_scale = 1.0
                    self.motor_right_scale = 1.0
                    self.calibration_saved = False
                
                # Rate-limited control updates
                now = time.time()
                if now - last_update >= control_rate:
                    throttle, steer = self.controller.get_axes()
                    
                    # Apply calibration for display
                    applied_steer = steer
                    if abs(throttle) > 0.05:
                        applied_steer += self.steering_trim
                    applied_steer = clamp(applied_steer)
                    
                    # Send command
                    await self._send_drive_command(throttle, steer)
                    
                    # Update display
                    self._print_status(throttle, steer, applied_steer)
                    
                    last_update = now
                
                await asyncio.sleep(0.01)  # 100 Hz loop for button responsiveness
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted")
        
        finally:
            # Check if unsaved changes
            if not self.calibration_saved:
                print("\n")
                print("⚠️  WARNING: You have unsaved calibration changes!")
                print(f"   Steering Trim: {self.steering_trim:+.3f}")
                print(f"   Motor Balance: L={self.motor_left_scale:.2f} R={self.motor_right_scale:.2f}")
                try:
                    response = input("\nSave before exiting? (y/n): ").strip().lower()
                    if response == 'y':
                        await self._save_calibration()
                except:
                    pass
            
            if self.sock:
                self.sock.close()
            
            print("\n✅ Calibration tool closed")
        
        return 0


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 controller/calibrate.py <robot_ip>")
        print("Example: python3 controller/calibrate.py 192.168.8.230")
        return 1
    
    robot_ip = sys.argv[1]
    
    tool = CalibrationTool(robot_ip)
    return asyncio.run(tool.run())


if __name__ == "__main__":
    # This module is a subsidiary of robot_master_gui.py
    # It should be launched via: python3 calibrate.py <robot_ip>
    # Always use the Master GUI to launch calibration!
    import sys
    if len(sys.argv) < 2:
        print("⚠️  ERROR: This module must be launched by robot_master_gui.py")
        print("   Do not run this directly. Use: python3 controller/robot_master_gui.py")
        sys.exit(1)
    sys.exit(main())
