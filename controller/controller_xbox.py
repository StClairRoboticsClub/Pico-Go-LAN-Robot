#!/usr/bin/env python3
"""
Pico-Go LAN Robot - Xbox Controller Application
===============================================
Reads Xbox controller input and sends control commands to robot via WebSocket/TCP.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT

Requirements:
    - Python 3.11+
    - pygame >= 2.5
    - asyncio (built-in)

Usage:
    python3 controller_xbox.py [robot_ip]
"""

import asyncio
import json
import time
import sys
from typing import Optional

import pygame


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_ROBOT_IP = "10.42.0.123"  # Default robot IP (update as needed)
ROBOT_PORT = 8765
CONTROL_RATE_HZ = 30
DEAD_ZONE = 0.08
RECONNECT_DELAY = 1.0

# Xbox controller axis mappings (SDL2)
AXIS_LEFT_X = 0  # Left stick horizontal
AXIS_LEFT_Y = 1  # Left stick vertical
AXIS_RIGHT_X = 2  # Right stick horizontal
AXIS_RIGHT_Y = 3  # Right stick vertical
AXIS_LEFT_TRIGGER = 4
AXIS_RIGHT_TRIGGER = 5

# Button mappings
BUTTON_A = 0
BUTTON_B = 1
BUTTON_X = 2
BUTTON_Y = 3
BUTTON_LB = 4
BUTTON_RB = 5
BUTTON_BACK = 6
BUTTON_START = 7


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def apply_deadzone(value: float, threshold: float = DEAD_ZONE) -> float:
    """
    Apply deadzone to joystick input.
    
    Args:
        value: Input value (-1.0 to 1.0)
        threshold: Deadzone threshold
    
    Returns:
        Value with deadzone applied
    """
    if abs(value) < threshold:
        return 0.0
    
    # Scale remaining range to full 0-1
    sign = 1 if value > 0 else -1
    scaled = (abs(value) - threshold) / (1.0 - threshold)
    return sign * scaled


def clamp(value: float, min_val: float = -1.0, max_val: float = 1.0) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


# ============================================================================
# CONTROLLER INPUT HANDLER
# ============================================================================

class XboxController:
    """
    Xbox controller input handler using pygame.
    """
    
    def __init__(self):
        """Initialize Xbox controller."""
        pygame.init()
        pygame.joystick.init()
        
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.connected = False
        self.reverse_mode = False  # False = Forward, True = Reverse
        self.lb_pressed_last = False  # Track LB button state for toggle
        
        self._initialize_controller()
    
    def _initialize_controller(self):
        """Initialize the first available joystick."""
        joystick_count = pygame.joystick.get_count()
        
        if joystick_count == 0:
            print("⚠️  No controller detected!")
            print("   Please connect an Xbox controller and restart.")
            return
        
        # Use first controller
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.connected = True
        
        print(f"✅ Controller connected: {self.joystick.get_name()}")
        print(f"   Axes: {self.joystick.get_numaxes()}")
        print(f"   Buttons: {self.joystick.get_numbuttons()}")
    
    def get_throttle_steer(self) -> tuple[float, float]:
        """
        Get throttle and steering values from controller.
        
        Uses:
        - Left Bumper (LB): Toggle forward/reverse mode
        - Right trigger (axis 5): Throttle (0 to 1)
        - Left stick X (axis 0): Steering (-1 to 1)
        
        Returns:
            (throttle, steer) tuple, each in range -1.0 to 1.0
        """
        if not self.connected:
            return 0.0, 0.0
        
        # Update pygame events to get latest joystick state
        pygame.event.pump()
        
        # Check for LB button toggle
        lb_pressed = self.joystick.get_button(BUTTON_LB)
        if lb_pressed and not self.lb_pressed_last:
            # Button just pressed - toggle mode
            self.reverse_mode = not self.reverse_mode
            mode_str = "REVERSE" if self.reverse_mode else "FORWARD"
            print(f"\n🔄 Mode: {mode_str}")
        self.lb_pressed_last = lb_pressed
        
        # Get right trigger for throttle
        # Trigger ranges from -1.0 (not pressed) to +1.0 (fully pressed)
        trigger_raw = self.joystick.get_axis(AXIS_RIGHT_TRIGGER)  # Axis 5
        
        # Convert from -1..1 to 0..1 range
        trigger = max(0.0, (trigger_raw + 1.0) / 2.0)
        
        # Apply threshold - only register trigger press above 15%
        trigger = 0.0 if trigger < 0.15 else (trigger - 0.15) / 0.85
        
        # Apply mode: reverse_mode False = forward (negative), True = reverse (positive)
        throttle_raw = -trigger if not self.reverse_mode else trigger
        
        # Get steering from left stick X (inverted and reduced sensitivity)
        steer_raw = -self.joystick.get_axis(AXIS_LEFT_X) * 0.6  # Axis 0, inverted, 60% sensitivity
        
        # Apply deadzones
        throttle = apply_deadzone(throttle_raw, 0.05)
        steer = apply_deadzone(steer_raw)
        
        # Clamp values
        throttle = clamp(throttle)
        steer = clamp(steer)
        
        return throttle, steer
    
    def get_button(self, button_id: int) -> bool:
        """
        Check if button is pressed.
        
        Args:
            button_id: Button ID to check
        
        Returns:
            True if pressed, False otherwise
        """
        if not self.connected:
            return False
        
        pygame.event.pump()
        return self.joystick.get_button(button_id)
    
    def is_connected(self) -> bool:
        """Check if controller is connected."""
        return self.connected


# ============================================================================
# ROBOT COMMUNICATION
# ============================================================================

class RobotConnection:
    """
    UDP connection to robot for ultra-low latency control.
    """
    
    def __init__(self, robot_ip: str, robot_port: int):
        """
        Initialize robot connection.
        
        Args:
            robot_ip: Robot IP address
            robot_port: Robot UDP port
        """
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.sock = None
        self.connected = False
        self.seq_num = 0
    
    async def connect(self) -> bool:
        """
        Initialize UDP socket (no connection needed).
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            import socket
            
            print(f"🔌 Initializing UDP socket for robot at {self.robot_ip}:{self.robot_port}...")
            
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # No connection needed for UDP - just send!
            self.connected = True
            print(f"✅ UDP socket ready! (connectionless, low latency)")
            return True
        
        except Exception as e:
            print(f"❌ Socket initialization failed: {e}")
            self.connected = False
            return False
    
    async def send_drive_command(self, throttle: float, steer: float) -> bool:
        """
        Send drive command to robot via UDP (instant, fire-and-forget).
        
        Args:
            throttle: Throttle value (-1.0 to 1.0)
            steer: Steering value (-1.0 to 1.0)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected or not self.sock:
            return False
        
        try:
            # Build command packet with timestamp
            packet = {
                "ts": int(time.time() * 1000),  # Timestamp in milliseconds
                "seq": self.seq_num,
                "cmd": "drive",
                "axes": {
                    "throttle": round(throttle, 3),
                    "steer": round(steer, 3)
                }
            }
            
            # Send via UDP (instant, no connection overhead)
            message = json.dumps(packet).encode()
            self.sock.sendto(message, (self.robot_ip, self.robot_port))
            # NOTE: sendto() returns immediately - no blocking, no ACK wait
            # This is the fastest possible send operation!
            
            self.seq_num += 1
            return True
        
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False
    
    async def disconnect(self):
        """Close UDP socket."""
        if self.sock:
            self.sock.close()
        
        self.connected = False
        print("🔌 UDP socket closed")


# ============================================================================
# MAIN CONTROLLER APPLICATION
# ============================================================================

class ControllerApp:
    """
    Main controller application.
    """
    
    def __init__(self, robot_ip: str):
        """
        Initialize controller application.
        
        Args:
            robot_ip: Robot IP address
        """
        self.robot_ip = robot_ip
        self.controller = XboxController()
        self.connection = RobotConnection(robot_ip, ROBOT_PORT)
        self.running = False
        self.control_rate = 1.0 / CONTROL_RATE_HZ
        
        # Statistics
        self.packets_sent = 0
        self.start_time = time.time()
    
    async def run(self):
        """Run the controller application."""
        self.running = True
        
        # Check if controller is connected
        if not self.controller.is_connected():
            print("❌ No controller found. Exiting.")
            return
        
        # Connect to robot
        while self.running and not self.connection.connected:
            if not await self.connection.connect():
                print(f"⏳ Retrying in {RECONNECT_DELAY}s...")
                await asyncio.sleep(RECONNECT_DELAY)
        
        if not self.running:
            return
        
        print("\n" + "="*60)
        print("🎮 CONTROLLER ACTIVE")
        print("="*60)
        print("Left Bumper (LB): Toggle Forward/Reverse mode")
        print("Right Trigger: Throttle (0-100%)")
        print("Left Stick X: Steering")
        print("START button: Exit")
        print("="*60)
        print("📍 Current Mode: FORWARD")
        print("="*60 + "\n")
        
        # Main control loop
        last_update = time.time()
        
        try:
            while self.running:
                # Check for exit button
                if self.controller.get_button(BUTTON_START):
                    print("\n🛑 START button pressed - exiting...")
                    break
                
                # Rate limiting
                now = time.time()
                elapsed = now - last_update
                
                if elapsed >= self.control_rate:
                    # Get controller input
                    throttle, steer = self.controller.get_throttle_steer()
                    
                    # Send command
                    if await self.connection.send_drive_command(throttle, steer):
                        self.packets_sent += 1
                        
                        # Print status (every 30 packets = 1 second at 30 Hz)
                        if self.packets_sent % 30 == 0:
                            runtime = time.time() - self.start_time
                            rate = self.packets_sent / runtime if runtime > 0 else 0
                            print(f"📊 Packets: {self.packets_sent} | "
                                  f"Rate: {rate:.1f} Hz | "
                                  f"T: {throttle:+.2f} | S: {steer:+.2f}")
                    else:
                        # Connection lost - try to reconnect
                        print("⚠️  Connection lost - reconnecting...")
                        if not await self.connection.connect():
                            await asyncio.sleep(RECONNECT_DELAY)
                            continue
                    
                    last_update = now
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(0.001)
        
        except KeyboardInterrupt:
            print("\n⚠️  Keyboard interrupt")
        
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown the application."""
        print("\n🔄 Shutting down...")
        self.running = False
        
        # Send stop command
        if self.connection.connected:
            await self.connection.send_drive_command(0.0, 0.0)
            await asyncio.sleep(0.1)
        
        # Disconnect
        await self.connection.disconnect()
        
        # Quit pygame
        pygame.quit()
        
        # Print statistics
        runtime = time.time() - self.start_time
        avg_rate = self.packets_sent / runtime if runtime > 0 else 0
        print(f"\n📊 Final Statistics:")
        print(f"   Runtime: {runtime:.1f}s")
        print(f"   Packets sent: {self.packets_sent}")
        print(f"   Average rate: {avg_rate:.1f} Hz")
        print("\n✅ Shutdown complete")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    # Parse command line arguments
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ROBOT_IP
    
    print("="*60)
    print("🤖 Pico-Go LAN Robot - Xbox Controller")
    print("="*60)
    print(f"Target Robot IP: {robot_ip}:{ROBOT_PORT}")
    print(f"Control Rate: {CONTROL_RATE_HZ} Hz")
    print("="*60 + "\n")
    
    # Create and run application
    app = ControllerApp(robot_ip)
    
    try:
        asyncio.run(app.run())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
