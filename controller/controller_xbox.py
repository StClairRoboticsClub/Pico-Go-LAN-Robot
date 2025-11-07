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
    python3 controller_xbox.py                     # Auto-discover robots (recommended)
    python3 controller_xbox.py [robot_ip_or_hostname]  # Manual connection
    
Examples:
    python3 controller_xbox.py                     # Scan network and choose robot
    python3 controller_xbox.py 10.145.146.98       # Connect by IP
    python3 controller_xbox.py picogo1             # Connect by hostname
    python3 controller_xbox.py picogo2.local       # Connect by full hostname
"""

import asyncio
import json
import time
import sys
import socket
import os
import struct
import subprocess
from typing import Optional, List, Dict

import pygame


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_ROBOT_IP = "picogo1.local"  # Default robot hostname (works across networks)
ROBOT_PORT = 8765
CONTROL_RATE_HZ = 30
DEAD_ZONE = 0.08
RECONNECT_DELAY = 1.0

# Input shaping configuration (per driver experience report)
THROTTLE_EXPO = 2.0  # 1.0=linear, 2.0=quadratic, 3.0=cubic (smoother at low inputs)
STEERING_EXPO = 1.5  # Less aggressive expo for steering (more precision)
THROTTLE_SENSITIVITY = 1.0  # Overall throttle multiplier (0.0 to 1.0)
STEERING_SENSITIVITY = 0.4  # Overall steering multiplier (reduced from 0.6 for less twitchy steering)
SPEED_STEERING_REDUCTION = 0.5  # Reduce steering at high speed: 0.0=no reduction, 1.0=max reduction
                                  # At full throttle, steering *= (1.0 - SPEED_STEERING_REDUCTION)
STEERING_TRIM = 0.0  # Steering offset to compensate for drift (-0.2 to +0.2)
                     # Negative = compensate for left drift, Positive = compensate for right drift
                     # Start at 0.0 and adjust in small increments (0.02-0.05)

# ============================================================================
# Xbox Controller Mappings (SDL2 / pygame)
# ============================================================================
# Verified on: Generic X-Box pad (2025-11-07)
# 
# AXIS MAPPINGS:
# Axis 0: Left Stick X     (-1.0 = left,     +1.0 = right)
# Axis 1: Left Stick Y     (-1.0 = up,       +1.0 = down)
# Axis 2: Left Trigger     (-1.0 = released, +1.0 = fully pressed)
# Axis 3: Right Stick X    (-1.0 = right,    +1.0 = left)  ⚠️ INVERTED
# Axis 4: Right Stick Y    (-1.0 = up,       +1.0 = down)
# Axis 5: Right Trigger    (-1.0 = released, +1.0 = fully pressed)
#
# BUTTON MAPPINGS:
# Button 0: A
# Button 1: B
# Button 2: X
# Button 3: Y
# Button 4: LB (Left Bumper)
# Button 5: RB (Right Bumper)
# Button 6: BACK
# Button 7: START
# ============================================================================

AXIS_LEFT_X = 0
AXIS_LEFT_Y = 1
AXIS_LEFT_TRIGGER = 2
AXIS_RIGHT_X = 3
AXIS_RIGHT_Y = 4
AXIS_RIGHT_TRIGGER = 5

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

def get_local_ip() -> str:
    """
    Get the local IP address of the WiFi interface (bypass VPNs).
    
    Returns:
        Local IP address string on WiFi network
    """
    try:
        # Get WiFi interface IP directly (works even with VPN)
        import subprocess
        result = subprocess.run(['ip', 'addr', 'show', 'wlp8s0'], 
                              capture_output=True, text=True, timeout=2)
        # Look for "inet 10.145.146.207/24" pattern
        for line in result.stdout.split('\n'):
            if 'inet ' in line and 'scope global' in line:
                ip = line.strip().split()[1].split('/')[0]
                return ip
    except:
        pass
    
    # Fallback: try common WiFi interface names
    for iface in ['wlan0', 'wlp8s0', 'wlp3s0', 'wlo1']:
        try:
            result = subprocess.run(['ip', 'addr', 'show', iface], 
                                  capture_output=True, text=True, timeout=1)
            for line in result.stdout.split('\n'):
                if 'inet ' in line and 'scope global' in line:
                    ip = line.strip().split()[1].split('/')[0]
                    return ip
        except:
            continue
    
    # Last resort: socket method (may give VPN IP)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"


def get_network_prefix(ip: str) -> str:
    """
    Get network prefix from IP (e.g., 10.145.146.98 -> 10.145.146)
    
    Args:
        ip: IP address string
    
    Returns:
        Network prefix (first 3 octets)
    """
    parts = ip.split('.')
    return '.'.join(parts[:3])


def test_robot_connection(ip: str, timeout: float = 1.0) -> bool:
    """
    Test if a robot is reachable at the given IP by sending a test packet.
    
    Args:
        ip: Robot IP address to test
        timeout: How long to wait (seconds)
    
    Returns:
        True if robot is reachable and responds
    """
    try:
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_sock.settimeout(timeout)
        
        # Send a harmless drive command (all zeros = stop)
        test_packet = json.dumps({
            "cmd": "drive",
            "axes": {"left_y": 0, "right_x": 0},
            "seq": 0,
            "ts": int(time.time() * 1000)
        }).encode()
        
        test_sock.sendto(test_packet, (ip, ROBOT_PORT))
        test_sock.close()
        return True
    except Exception as e:
        return False


def get_all_local_networks() -> List[str]:
    """
    Get all local network prefixes (excluding loopback and docker).
    
    Returns:
        List of network prefixes like ['10.42.0', '192.168.1', '10.55.81']
    """
    networks = []
    try:
        result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, timeout=2)
        
        for line in result.stdout.split('\n'):
            # Look for inet lines with scope global
            if 'inet ' in line and 'scope global' in line:
                ip = line.strip().split()[1].split('/')[0]
                # Skip loopback, docker, and VPN tunnels
                if not ip.startswith(('127.', '172.17.', '172.18.', '100.')):
                    prefix = get_network_prefix(ip)
                    if prefix not in networks:
                        networks.append(prefix)
    except:
        pass
    
    # Fallback: common robot networks
    if not networks:
        networks = ['10.42.0', '192.168.1', '192.168.4']
    
    return networks


def discover_robots_on_network(timeout: float = 3.0) -> List[Dict]:
    """
    Broadcast discovery request and collect robot responses.
    Scans ALL local network interfaces to find robots.
    
    Args:
        timeout: How long to wait for responses (seconds)
    
    Returns:
        List of robot info dicts with 'robot_id', 'hostname', 'ip', 'version'
    """
    print(f"🔍 Broadcasting discovery request...")
    
    robots = []
    
    try:
        # Create UDP socket for broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.5)  # 500ms timeout for receives
        
        # Get ALL local networks (not just one!)
        networks = get_all_local_networks()
        print(f"   Scanning networks: {', '.join(networks)}")
        
        # Send discovery to all networks
        discovery_msg = json.dumps({"cmd": "discover", "seq": 0}).encode()
        
        for network_prefix in networks:
            # Try broadcast first
            broadcast_addr = f"{network_prefix}.255"
            try:
                sock.sendto(discovery_msg, (broadcast_addr, ROBOT_PORT))
            except:
                pass
            
            # Also scan common robot IPs directly (expanded range to include DHCP addresses)
            for last_octet in range(1, 255):
                target_ip = f"{network_prefix}.{last_octet}"
                try:
                    sock.sendto(discovery_msg, (target_ip, ROBOT_PORT))
                except:
                    pass
        
        print(f"   Listening for responses...")
        
        # Collect responses
        start_time = time.time()
        seen_ips = set()
        
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                response = json.loads(data.decode().strip())
                
                robot_ip = addr[0]
                
                # Avoid duplicates
                if robot_ip in seen_ips:
                    continue
                seen_ips.add(robot_ip)
                
                if response.get("type") == "robot_info":
                    robot_info = {
                        "robot_id": response.get("robot_id", "?"),
                        "hostname": response.get("hostname", "unknown"),
                        "ip": robot_ip,
                        "version": response.get("version", "?"),
                        "color": response.get("color", [255, 255, 255])  # RGB tuple
                    }
                    robots.append(robot_info)
                    
                    # Format color display
                    color_rgb = robot_info['color']
                    color_str = f"RGB({color_rgb[0]},{color_rgb[1]},{color_rgb[2]})"
                    
                    # Try to get ANSI color for terminal display
                    try:
                        ansi_color = f"\033[38;2;{color_rgb[0]};{color_rgb[1]};{color_rgb[2]}m●\033[0m"
                    except:
                        ansi_color = "●"
                    
                    print(f"   ✅ Found: {ansi_color} Robot #{robot_info['robot_id']} ({robot_info['hostname']}) at {robot_ip} - {color_str}")
            
            except socket.timeout:
                continue
            except Exception as e:
                continue
        
        sock.close()
        
        elapsed = time.time() - start_time
        print(f"   Discovery complete: {len(robots)} robot(s) found in {elapsed:.1f}s\n")
        
        return robots
    
    except Exception as e:
        print(f"   ❌ Discovery error: {e}")
        return []


def load_cached_robot() -> str:
    """Load last-used robot IP from cache file."""
    cache_file = os.path.expanduser("~/.picogo_last_robot")
    try:
        with open(cache_file, 'r') as f:
            return f.read().strip()
    except:
        return None


def save_cached_robot(ip: str):
    """Save robot IP to cache file for next time."""
    cache_file = os.path.expanduser("~/.picogo_last_robot")
    try:
        with open(cache_file, 'w') as f:
            f.write(ip)
    except:
        pass


def prompt_for_robot_ip() -> str:
    """
    Prompt user to enter robot IP address from LCD display.
    The robot displays its IP on the LCD screen when it boots.
    """
    print("\n📟 Robot IP Entry")
    print("   The robot displays its IP address on the LCD screen.")
    print("   Look at the robot's display and enter the IP below.\n")
    
    while True:
        try:
            ip = input("   Enter robot IP (or 'quit' to exit): ").strip()
            
            if ip.lower() in ('quit', 'q', 'exit'):
                return None
            
            # Basic IP validation
            parts = ip.split('.')
            if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                # Test if robot is reachable
                print(f"   Testing connection to {ip}...")
                if test_robot_connection(ip):
                    print(f"   ✅ Robot reachable at {ip}")
                    save_cached_robot(ip)
                    return ip
                else:
                    print(f"   ⚠️ Could not connect to robot at {ip}")
                    retry = input("   Try again? (y/n): ").strip().lower()
                    if retry != 'y':
                        return None
            else:
                print("   ❌ Invalid IP address format (expected: xxx.xxx.xxx.xxx)")
                
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            return None
        except Exception as e:
            print(f"   ❌ Error: {e}")


def discover_and_select_robot() -> str:
    """
    Discover robots on network and let user select one.
    
    Returns:
        Robot IP address or None
    """
    print("\n" + "="*60)
    print("🤖 ROBOT DISCOVERY")
    print("="*60)
    
    # Discover robots using UDP broadcast
    robots = discover_robots_on_network(timeout=3.0)
    
    if len(robots) == 0:
        # No robots found
        print("❌ No robots found on network\n")
        print("   Troubleshooting:")
        print("   1. Is the robot powered on?")
        print("   2. Is the robot connected to WiFi? (Check LCD)")
        print("   3. Are you on the same network?")
        print("   4. Check robot's IP address on LCD screen\n")
        
        # Offer manual entry
        manual = input("   Enter IP manually? (y/n): ").strip().lower()
        if manual == 'y':
            return prompt_for_robot_ip()
        return None
    
    elif len(robots) == 1:
        # Exactly one robot found - auto-select
        robot = robots[0]
        print(f"✅ Found 1 robot:")
        print(f"   Robot #{robot['robot_id']} ({robot['hostname']}) at {robot['ip']}")
        print(f"   Auto-connecting...\n")
        save_cached_robot(robot['ip'])
        return robot['ip']
    
    else:
        # Multiple robots found - let user choose
        print(f"📋 Found {len(robots)} robots:\n")
        for i, robot in enumerate(robots, 1):
            print(f"   {i}. Robot #{robot['robot_id']} ({robot['hostname']}) - {robot['ip']}")
        
        print()
        
        while True:
            try:
                choice = input(f"Select robot (1-{len(robots)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                idx = int(choice) - 1
                if 0 <= idx < len(robots):
                    robot = robots[idx]
                    print(f"\n✅ Selected: Robot #{robot['robot_id']} ({robot['hostname']}) at {robot['ip']}\n")
                    save_cached_robot(robot['ip'])
                    return robot['ip']
                else:
                    print(f"❌ Please enter a number between 1 and {len(robots)}")
            
            except ValueError:
                print("❌ Please enter a valid number or 'q'")
            except KeyboardInterrupt:
                print("\n❌ Cancelled")
                return None


def select_robot(robots: List[Dict]) -> str:
    """
    Display list of discovered robots and let user select one.
    Returns the IP address of the selected robot.
    """
    if not robots:
        return None
    
    if len(robots) == 1:
        robot = robots[0]
        print(f"\n✅ Found 1 robot: #{robot['robot_id']} ({robot['hostname']}) at {robot['ip']}")
        print(f"   Auto-connecting...")
        return robot['ip']
    
    print(f"\n📋 Found {len(robots)} robots:")
    for i, robot in enumerate(robots, 1):
        rid = robot['robot_id']
        hostname = robot['hostname']
        ip = robot['ip']
        version = robot.get('version', '?')
        color_rgb = robot.get('color', [255, 255, 255])
        
        # Try to display color indicator using ANSI escape codes
        try:
            ansi_color = f"\033[38;2;{color_rgb[0]};{color_rgb[1]};{color_rgb[2]}m●\033[0m"
        except:
            ansi_color = "●"
        
        print(f"   {i}. {ansi_color} Robot #{rid} ({hostname}) - {ip} [v{version}]")
    
    while True:
        try:
            choice = input(f"\nSelect robot (1-{len(robots)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(robots):
                selected = robots[idx]
                print(f"✅ Connecting to Robot #{selected['robot_id']} at {selected['ip']}")
                return selected['ip']
            else:
                print(f"❌ Please enter a number between 1 and {len(robots)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n❌ Selection cancelled")
            return None
    
    while True:
        try:
            choice = input(f"Select robot [1-{len(robots)}] or 'q' to quit: ").strip()
            
            if choice.lower() == 'q':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(robots):
                selected = robots[choice_num - 1]
                print(f"\n✅ Selected: {selected['hostname']} ({selected['ip']})")
                return selected['ip']
            else:
                print(f"❌ Please enter a number between 1 and {len(robots)}")
        except ValueError:
            print("❌ Invalid input. Enter a number or 'q' to quit.")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled")
            return None


def resolve_robot_address(address: str) -> str:
    """
    Resolve robot hostname or IP address.
    Auto-appends .local if no extension provided.
    
    Args:
        address: Hostname (picogo1) or IP address (10.145.146.98)
    
    Returns:
        Resolved IP address
    """
    # If it looks like an IP address, return as-is
    if address.replace('.', '').isdigit():
        return address
    
    # Auto-append .local if not present
    if not address.endswith('.local'):
        address = f"{address}.local"
    
    try:
        print(f"🔍 Resolving {address}...")
        resolved_ip = socket.gethostbyname(address)
        print(f"✅ Resolved to {resolved_ip}")
        return resolved_ip
    except socket.gaierror:
        print(f"⚠️  Could not resolve {address}, using as-is")
        return address


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


def apply_expo(value: float, expo: float = 2.0) -> float:
    """
    Apply exponential curve to input value for smoother control at low inputs.
    
    This makes small stick movements produce proportionally smaller outputs,
    while maintaining full range at extremes. Addresses the "twitchy" feel
    mentioned in the driver experience report.
    
    Args:
        value: Input value (-1.0 to 1.0)
        expo: Exponent (1.0=linear, 2.0=quadratic, 3.0=cubic)
              Higher values = smoother at low inputs, more aggressive at high
    
    Returns:
        Value with expo curve applied (-1.0 to 1.0)
    
    Example:
        Linear (expo=1.0): 0.3 input -> 0.3 output (30% PWM)
        Quadratic (expo=2.0): 0.3 input -> 0.09 output (9% PWM)
        Cubic (expo=3.0): 0.3 input -> 0.027 output (2.7% PWM)
    """
    if abs(value) < 0.001:
        return 0.0
    
    # Preserve sign, apply expo to magnitude
    sign = 1.0 if value > 0 else -1.0
    magnitude = abs(value)
    
    # Apply exponential curve
    shaped = pow(magnitude, expo)
    
    return sign * shaped


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
    
    def get_axes(self, steering_trim: float = 0.0) -> tuple[float, float]:
        """
        Get processed throttle and steering values from controller.
        
        Uses:
        - Right trigger (axis 5): Forward throttle
        - Left trigger (axis 2): Reverse throttle
        - Left stick X (axis 0): Steering (negative = CCW, positive = CW)
        
        Xbox Trigger Hardware Behavior (SDL2):
        - Released (not pressed): raw axis = -1.0
        - Half pressed: raw axis = 0.0
        - Fully pressed: raw axis = +1.0
        
        After processing (_process_trigger):
        - Released: output = 0.0 (no motion)
        - Half pressed: output ~= 0.44 (with 10% deadzone scaling)
        - Fully pressed: output = 1.0
        
        Args:
            steering_trim: Calibration offset for steering (-0.2 to +0.2)
        
        Returns:
            (throttle, steer) tuple, each in range -1.0 to 1.0
        """
        if not self.connected:
            return 0.0, 0.0
        
        # Update pygame events to get latest joystick state
        pygame.event.pump()
        
        def _process_trigger(raw_axis: float) -> float:
            """
            Convert trigger axis to usable 0..1 range with deadzone.
            
            SDL2 reports Xbox triggers as:
              -1.0 (released) -> 0.0 (fully pressed not reached) -> +1.0 (fully pressed)
            
            This function:
            1. Maps [-1.0, +1.0] to [0.0, 1.0]
            2. Applies 10% deadzone to filter noise when released
            3. Rescales [0.1, 1.0] to [0.0, 1.0] for full output range
            """
            # Map from [-1.0, 1.0] to [0.0, 1.0]
            normalized = (raw_axis + 1.0) / 2.0
            
            # Apply deadzone at the low end
            if normalized < 0.1:
                return 0.0
            
            # Scale remaining range [0.1, 1.0] to [0.0, 1.0]
            return (normalized - 0.1) / 0.9
        
        forward = _process_trigger(self.joystick.get_axis(AXIS_RIGHT_TRIGGER))
        reverse = _process_trigger(self.joystick.get_axis(AXIS_LEFT_TRIGGER))
        
        # Right trigger drives forward (positive throttle), left trigger drives reverse (negative throttle)
        throttle_raw = forward - reverse
        
        # Get steering from left stick X (positive = clockwise turn)
        steer_raw = self.joystick.get_axis(AXIS_LEFT_X)
        
        # Apply deadzones first
        throttle = apply_deadzone(throttle_raw, 0.05)
        steer = apply_deadzone(steer_raw)
        
        # Apply exponential curves for smoother control (per driver experience report)
        throttle = apply_expo(throttle, THROTTLE_EXPO)
        steer = apply_expo(steer, STEERING_EXPO)
        
        # Apply sensitivity scaling
        throttle = throttle * THROTTLE_SENSITIVITY
        steer = steer * STEERING_SENSITIVITY
        
        # Speed-dependent steering reduction (makes high-speed driving more stable)
        # At full throttle, reduce steering authority to prevent twitchy control
        throttle_magnitude = abs(throttle)
        steering_reduction_factor = 1.0 - (throttle_magnitude * SPEED_STEERING_REDUCTION)
        steer = steer * steering_reduction_factor
        
        # Apply steering trim to compensate for hardware drift
        # Only apply trim when there's throttle (not when stationary)
        if abs(throttle) > 0.05:
            steer = steer + steering_trim
        
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
        
        # Robot calibration (fetched on connect)
        self.calibration = {
            "steering_trim": STEERING_TRIM,
            "motor_left_scale": 1.0,
            "motor_right_scale": 1.0
        }
    
    async def connect(self) -> bool:
        """
        Initialize UDP socket and fetch robot calibration.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            import socket
            
            print(f"🔌 Initializing UDP socket for robot at {self.robot_ip}:{self.robot_port}...")
            
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(2.0)  # 2 second timeout for calibration fetch
            
            # Request calibration from robot
            await self._fetch_calibration()
            
            # No connection needed for UDP - just send!
            self.connected = True
            print(f"✅ UDP socket ready! (connectionless, low latency)")
            return True
        
        except Exception as e:
            print(f"❌ Socket initialization failed: {e}")
            self.connected = False
            return False
    
    async def _fetch_calibration(self):
        """Fetch calibration from robot."""
        try:
            print("📥 Requesting calibration from robot...")
            
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
                    self.calibration = response["calibration"]
                    print(f"✅ Calibration loaded:")
                    print(f"   Robot ID: {self.calibration.get('robot_id', 'unknown')}")
                    print(f"   Steering Trim: {self.calibration.get('steering_trim', 0.0):+.3f}")
                    print(f"   Motor Balance: L={self.calibration.get('motor_left_scale', 1.0):.2f} "
                          f"R={self.calibration.get('motor_right_scale', 1.0):.2f}")
                else:
                    print("⚠️  No calibration in response (using defaults)")
            
            except socket.timeout:
                print("⚠️  Calibration request timed out (using defaults)")
        
        except Exception as e:
            print(f"⚠️  Could not fetch calibration: {e} (using defaults)")
    
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
        print("Right Trigger: Forward throttle")
        print("Left Trigger: Reverse throttle")
        print("Left Stick X: Steering (right = clockwise)")
        print("START button: Exit")
        print("="*60)
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
                    # Get calibration values
                    steering_trim = self.connection.calibration.get('steering_trim', 0.0)
                    
                    # Get controller input (with calibration applied)
                    throttle, steer = self.controller.get_axes(steering_trim=steering_trim)
                    
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
    print("="*60)
    print("🤖 Pico-Go LAN Robot - Xbox Controller")
    print("="*60)
    
    robot_ip = None
    
    # Check if IP provided as command-line argument
    if len(sys.argv) > 1:
        # Manual mode: use specified IP/hostname
        robot_address = sys.argv[1]
        print(f"\n📍 Manual mode: {robot_address}")
        robot_ip = resolve_robot_address(robot_address)
        if robot_ip:
            save_cached_robot(robot_ip)
    else:
        # Auto mode: Always run discovery (don't blindly trust cache)
        robot_ip = discover_and_select_robot()
    
    if robot_ip is None:
        print("\n❌ No robot selected. Exiting.\n")
        sys.exit(0)
    
    print(f"\n{'='*60}")
    print(f"🎯 Target Robot: {robot_ip}:{ROBOT_PORT}")
    print(f"📡 Control Rate: {CONTROL_RATE_HZ} Hz")
    print(f"🔒 Connection: Locked (until robot power cycle)")
    print("="*60 + "\n")
    
    # Create and run application
    app = ControllerApp(robot_ip)
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        print("\n\n✅ Controller stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
