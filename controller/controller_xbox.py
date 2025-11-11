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
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # Suppress pygame message
import struct
import subprocess
from typing import Optional, List, Dict
import pygame
# Removed terminal/TUI imports - using pygame window instead


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


def discover_robots_on_network(timeout: float = 1.5) -> List[Dict]:
    """
    Broadcast discovery request and collect robot responses.
    Scans ALL local network interfaces to find robots.
    
    Args:
        timeout: How long to wait for responses (seconds)
    
    Returns:
        List of robot info dicts with 'robot_id', 'hostname', 'ip', 'version'
    """
    robots = []
    
    try:
        # Create UDP socket for broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.3)  # 300ms timeout for receives (faster)
        
        # Get ALL local networks (not just one!)
        networks = get_all_local_networks()
        
        # Send discovery to all networks (optimized - broadcast only, no individual IP scan)
        discovery_msg = json.dumps({"cmd": "discover", "seq": 0}).encode()
        
        for network_prefix in networks:
            # Broadcast only (much faster than scanning 254 IPs per network)
            broadcast_addr = f"{network_prefix}.255"
            try:
                sock.sendto(discovery_msg, (broadcast_addr, ROBOT_PORT))
            except:
                pass
        
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
                        "color": response.get("color", [255, 255, 255]),  # RGB tuple
                        "calibration": response.get("calibration", {})  # Calibration data
                    }
                    robots.append(robot_info)
                    
            except socket.timeout:
                continue
            except Exception as e:
                continue
        
        sock.close()
        
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


def discover_and_select_robot() -> tuple:
    """
    Discover robots on network and let user select one.
    
    Returns:
        (robot_ip, robot_id) tuple or (None, None) if no robot selected
    """
    print("🔍 Discovering robots...", end='', flush=True)
    
    # Discover robots using UDP broadcast (faster timeout)
    robots = discover_robots_on_network(timeout=1.5)
    
    print(f"\r{' ' * 50}\r", end='')  # Clear discovery line
    
    if len(robots) == 0:
        # No robots found
        print("❌ No robots found")
        print("   Troubleshooting: Check robot power, WiFi, and network connection")
        manual = input("   Enter IP manually? (y/n): ").strip().lower()
        if manual == 'y':
            robot_ip = prompt_for_robot_ip()
            return (robot_ip, None) if robot_ip else (None, None)
        return (None, None)
    
    elif len(robots) == 1:
        # Exactly one robot found - auto-select
        robot = robots[0]
        print(f"✅ Robot #{robot['robot_id']} ({robot['hostname']}) at {robot['ip']}")
        save_cached_robot(robot['ip'])
        return (robot['ip'], robot['robot_id'])
    
    else:
        # Multiple robots found - let user choose
        print(f"📋 Found {len(robots)} robots:")
        for i, robot in enumerate(robots, 1):
            print(f"   {i}. Robot #{robot['robot_id']} ({robot['hostname']}) - {robot['ip']}")
        
        while True:
            try:
                choice = input(f"\nSelect (1-{len(robots)}) or 'q': ").strip()
                
                if choice.lower() == 'q':
                    return (None, None)
                
                idx = int(choice) - 1
                if 0 <= idx < len(robots):
                    robot = robots[idx]
                    save_cached_robot(robot['ip'])
                    return (robot['ip'], robot['robot_id'])
                else:
                    print(f"❌ Enter 1-{len(robots)}")
            
            except ValueError:
                print("❌ Invalid input")
            except KeyboardInterrupt:
                print("\n❌ Cancelled")
                return (None, None)


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
        resolved_ip = socket.gethostbyname(address)
        return resolved_ip
    except socket.gaierror:
        return address  # Return as-is if can't resolve


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
# UNIFIED DISPLAY CONTROLLER
# ============================================================================

class DisplayController:
    """
    Unified pygame display window for all controller types.
    Shows debug info, control status, and Hz.
    """
    
    def __init__(self):
        """Initialize pygame display window."""
        pygame.init()
        
        # Window configuration
        self.window_width = 700
        self.window_height = 700  # Increased to fit profile dropdown
        self.bg_color = (20, 20, 30)  # Dark blue-gray
        self.accent_color = (100, 200, 255)  # Light blue
        self.text_color = (255, 255, 255)  # White
        self.success_color = (100, 255, 100)  # Green
        self.warning_color = (255, 200, 100)  # Orange
        self.error_color = (255, 100, 100)  # Red
        
        # Create window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("🤖 Pico-Go LAN Robot Controller")
        
        # Set up fonts
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 36)
        self.header_font = pygame.font.Font(None, 24)
        self.body_font = pygame.font.Font(None, 20)
        self.value_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 18)
        
        # Display state
        self.robot_ip = "Not connected"
        self.robot_id = None
        self.controller_type = "Unknown"
        self.throttle = 0.0
        self.steer = 0.0
        self.current_hz = 0.0
        self.packets_sent = 0
        self.runtime = 0.0
        self.connected = False
        
        # Profile dropdown state
        self.profiles = {}  # {id: {"name": str, "color": [r, g, b]}}
        self.current_profile_id = None
        self.dropdown_open = False
        self.dropdown_rect = None
        self.profile_callback = None  # Callback function when profile changes
        
        # Initial render
        self._draw_ui()
    
    def update(self, robot_ip=None, robot_id=None, controller_type=None, 
               throttle=None, steer=None, hz=None, packets_sent=None, 
               runtime=None, connected=None, profiles=None, current_profile_id=None):
        """Update display state."""
        if robot_ip is not None:
            self.robot_ip = robot_ip
        if robot_id is not None:
            self.robot_id = robot_id
        if controller_type is not None:
            self.controller_type = controller_type
        if throttle is not None:
            self.throttle = throttle
        if steer is not None:
            self.steer = steer
        if hz is not None:
            self.current_hz = hz
        if packets_sent is not None:
            self.packets_sent = packets_sent
        if runtime is not None:
            self.runtime = runtime
        if connected is not None:
            self.connected = connected
        if profiles is not None:
            self.profiles = profiles
        if current_profile_id is not None:
            self.current_profile_id = current_profile_id
    
    def set_profile_callback(self, callback):
        """Set callback function to call when profile is selected."""
        self.profile_callback = callback
    
    def _draw_ui(self):
        """Draw the UI in the pygame window."""
        # Clear screen
        self.screen.fill(self.bg_color)
        
        # Title bar
        title_rect = pygame.Rect(0, 0, self.window_width, 50)
        pygame.draw.rect(self.screen, (30, 30, 45), title_rect)
        title_text = self.title_font.render("🤖 Pico-Go LAN Robot", True, self.accent_color)
        self.screen.blit(title_text, (20, 12))
        subtitle_text = self.body_font.render("Controller", True, (200, 200, 200))
        self.screen.blit(subtitle_text, (20, 35))
        
        # Profile selection dropdown (top-right corner)
        dropdown_width = 250
        dropdown_height = 35
        dropdown_x = self.window_width - dropdown_width - 20  # Right side with 20px margin
        dropdown_y = 30  # Below title bar with room for label
        
        # Profile label (above dropdown)
        profile_label = self.small_font.render("Profile:", True, (200, 200, 200))
        self.screen.blit(profile_label, (dropdown_x, 10))  # At top of window
        
        y = 70
        
        # Connection status
        status_header = self.header_font.render("Connection", True, self.accent_color)
        self.screen.blit(status_header, (20, y))
        y += 30
        
        # Connection status indicator
        status_color = self.success_color if self.connected else self.error_color
        status_text = "Connected" if self.connected else "Disconnected"
        status_label = self.body_font.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status_label, (40, y))
        y += 25
        
        # Robot info
        robot_info = f"Robot: {self.robot_ip}"
        if self.robot_id:
            robot_info = f"Robot #{self.robot_id}: {self.robot_ip}"
        robot_text = self.body_font.render(robot_info, True, self.text_color)
        self.screen.blit(robot_text, (40, y))
        y += 25
        
        # Controller type
        ctrl_text = self.body_font.render(f"Controller: {self.controller_type}", True, self.text_color)
        self.screen.blit(ctrl_text, (40, y))
        y += 40
        
        # Get current profile name
        current_profile_name = "Select Profile"
        if self.current_profile_id and self.current_profile_id in self.profiles:
            current_profile_name = self.profiles[self.current_profile_id]['name']
        elif not self.profiles:
            current_profile_name = "No profiles available"
        
        # Draw dropdown button (fully opaque)
        button_color = (60, 60, 80) if not self.dropdown_open else (80, 80, 100)
        pygame.draw.rect(self.screen, button_color, (dropdown_x, dropdown_y, dropdown_width, dropdown_height))
        pygame.draw.rect(self.screen, self.accent_color, (dropdown_x, dropdown_y, dropdown_width, dropdown_height), 2)
        
        # Profile name text
        profile_text = self.body_font.render(current_profile_name, True, self.text_color)
        self.screen.blit(profile_text, (dropdown_x + 10, dropdown_y + 8))
        
        # Dropdown arrow
        arrow_points = [
            (dropdown_x + dropdown_width - 20, dropdown_y + 10),
            (dropdown_x + dropdown_width - 10, dropdown_y + 10),
            (dropdown_x + dropdown_width - 15, dropdown_y + 20)
        ]
        pygame.draw.polygon(self.screen, self.accent_color, arrow_points)
        
        # Store dropdown rect for click detection
        self.dropdown_rect = pygame.Rect(dropdown_x, dropdown_y, dropdown_width, dropdown_height)
        
        # Draw dropdown list if open (fully opaque)
        if self.dropdown_open and self.profiles:
            list_y = dropdown_y + dropdown_height + 2
            list_height = min(len(self.profiles) * 30, 240)  # Max 240px height
            
            # Fully opaque background for dropdown list (darker for contrast)
            pygame.draw.rect(self.screen, (30, 30, 40), (dropdown_x, list_y, dropdown_width, list_height))
            pygame.draw.rect(self.screen, self.accent_color, (dropdown_x, list_y, dropdown_width, list_height), 2)
            
            # Draw each profile option
            item_y = list_y + 5
            for profile_id, profile in sorted(self.profiles.items()):
                if item_y + 25 > list_y + list_height:
                    break  # Don't draw beyond list height
                
                # Highlight if this is the current profile (fully opaque)
                if profile_id == self.current_profile_id:
                    pygame.draw.rect(self.screen, (70, 70, 90), 
                                   (dropdown_x + 2, item_y - 2, dropdown_width - 4, 25))
                
                # Profile name
                profile_name_text = self.body_font.render(profile['name'], True, self.text_color)
                self.screen.blit(profile_name_text, (dropdown_x + 10, item_y))
                
                # Color indicator dot
                color = profile.get('color', [255, 255, 255])
                pygame.draw.circle(self.screen, color, (dropdown_x + dropdown_width - 20, item_y + 10), 8)
                
                item_y += 30
        
        # Controls section
        controls_header = self.header_font.render("Controls", True, self.accent_color)
        self.screen.blit(controls_header, (20, y))
        y += 30
        
        if self.controller_type == "Keyboard":
            controls = [
                ("W / S", "Throttle forward/reverse"),
                ("A / D", "Steer left/right"),
                ("SPACE", "Brake (rapid stop)"),
                ("ESC", "Exit")
            ]
        else:
            controls = [
                ("RT", "Forward throttle"),
                ("LT", "Reverse throttle"),
                ("LS X", "Steering"),
                ("START", "Exit")
            ]
        
        for key, desc in controls:
            key_text = self.body_font.render(key, True, self.warning_color)
            desc_text = self.body_font.render(desc, True, self.text_color)
            self.screen.blit(key_text, (40, y))
            self.screen.blit(desc_text, (120, y))
            y += 25
        
        y += 20
        
        # Status section with visual bars
        status_header = self.header_font.render("Status", True, self.accent_color)
        self.screen.blit(status_header, (20, y))
        y += 30
        
        # Throttle display
        throttle_label = self.body_font.render("Throttle:", True, self.text_color)
        self.screen.blit(throttle_label, (40, y))
        
        # Throttle bar
        bar_width = 300
        bar_height = 30
        bar_x = 150
        bar_y = y - 5
        
        # Background bar
        pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        
        # Throttle value bar (green for forward, red for reverse)
        throttle_width = int(abs(self.throttle) * bar_width / 2)
        if self.throttle > 0:
            bar_color = self.success_color  # Green for forward
        elif self.throttle < 0:
            bar_color = self.error_color  # Red for reverse
        else:
            bar_color = (60, 60, 60)  # Gray for neutral
        
        if throttle_width > 0:
            center_x = bar_x + bar_width // 2
            if self.throttle > 0:
                pygame.draw.rect(self.screen, bar_color, (center_x, bar_y, throttle_width, bar_height))
            else:
                pygame.draw.rect(self.screen, bar_color, (center_x - throttle_width, bar_y, throttle_width, bar_height))
        
        # Center line
        pygame.draw.line(self.screen, (100, 100, 100), (bar_x + bar_width // 2, bar_y), 
                        (bar_x + bar_width // 2, bar_y + bar_height), 2)
        
        # Throttle value text
        throttle_value = self.value_font.render(f"{self.throttle:+.2f}", True, self.text_color)
        self.screen.blit(throttle_value, (bar_x + bar_width + 10, y - 2))
        
        y += 50
        
        # Steering display
        steer_label = self.body_font.render("Steering:", True, self.text_color)
        self.screen.blit(steer_label, (40, y))
        
        # Steering bar
        bar_y = y - 5
        
        # Background bar
        pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        
        # Steering value bar (blue)
        steer_width = int(abs(self.steer) * bar_width)
        if steer_width > 0:
            if self.steer > 0:
                pygame.draw.rect(self.screen, self.accent_color, 
                               (bar_x + bar_width // 2, bar_y, steer_width // 2, bar_height))
            else:
                pygame.draw.rect(self.screen, self.accent_color, 
                               (bar_x + bar_width // 2 - steer_width // 2, bar_y, steer_width // 2, bar_height))
        
        # Center line
        pygame.draw.line(self.screen, (100, 100, 100), (bar_x + bar_width // 2, bar_y), 
                        (bar_x + bar_width // 2, bar_y + bar_height), 2)
        
        # Steering value text
        steer_value = self.value_font.render(f"{self.steer:+.2f}", True, self.text_color)
        self.screen.blit(steer_value, (bar_x + bar_width + 10, y - 2))
        
        y += 60
        
        # Statistics section
        stats_header = self.header_font.render("Statistics", True, self.accent_color)
        self.screen.blit(stats_header, (20, y))
        y += 30
        
        # Control rate display
        rate_label = self.body_font.render("Control Rate:", True, self.text_color)
        self.screen.blit(rate_label, (40, y))
        
        # Color code Hz: green if >= 28, yellow if >= 25, red if < 25
        if self.current_hz >= 28.0:
            hz_color = self.success_color  # Green
        elif self.current_hz >= 25.0:
            hz_color = self.warning_color  # Yellow
        else:
            hz_color = self.error_color  # Red
        
        hz_text = self.value_font.render(f"{self.current_hz:.1f} Hz", True, hz_color)
        self.screen.blit(hz_text, (150, y - 2))
        y += 35
        
        # Packets sent
        packets_label = self.body_font.render("Packets Sent:", True, self.text_color)
        self.screen.blit(packets_label, (40, y))
        packets_text = self.value_font.render(f"{self.packets_sent}", True, self.text_color)
        self.screen.blit(packets_text, (150, y - 2))
        y += 35
        
        # Runtime
        runtime_label = self.body_font.render("Runtime:", True, self.text_color)
        self.screen.blit(runtime_label, (40, y))
        runtime_text = self.value_font.render(f"{self.runtime:.1f}s", True, self.text_color)
        self.screen.blit(runtime_text, (150, y - 2))
        y += 40
        
        # Instructions
        info_text = self.small_font.render("Keep this window focused to control the robot", True, (150, 150, 150))
        self.screen.blit(info_text, (20, y))
        y += 20
        info_text2 = self.small_font.render("Click profile dropdown to change robot profile", True, (150, 150, 150))
        self.screen.blit(info_text2, (20, y))
        
        pygame.display.flip()
    
    def process_events(self):
        """Process pygame events. Returns True if window should close."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    mouse_pos = event.pos
                    
                    # Check if clicking on dropdown button
                    if self.dropdown_rect and self.dropdown_rect.collidepoint(mouse_pos):
                        self.dropdown_open = not self.dropdown_open
                    elif self.dropdown_open and self.profiles:
                        # Check if clicking on a profile option
                        dropdown_width = 250
                        list_height = min(len(self.profiles) * 30, 240)
                        dropdown_x = self.dropdown_rect.x
                        list_y = self.dropdown_rect.y + self.dropdown_rect.height + 2
                        
                        list_rect = pygame.Rect(dropdown_x, list_y, dropdown_width, list_height)
                        if list_rect.collidepoint(mouse_pos):
                            # Calculate which profile was clicked
                            relative_y = mouse_pos[1] - list_y
                            profile_index = (relative_y - 5) // 30  # Account for 5px padding
                            
                            sorted_profiles = sorted(self.profiles.items())
                            if 0 <= profile_index < len(sorted_profiles):
                                selected_profile_id, selected_profile = sorted_profiles[profile_index]
                                
                                # Call callback if set
                                if self.profile_callback:
                                    self.profile_callback(selected_profile_id, selected_profile)
                                
                                self.current_profile_id = selected_profile_id
                                self.dropdown_open = False
                    else:
                        # Click outside dropdown - close it
                        self.dropdown_open = False
        return False
    
    def cleanup(self):
        """Cleanup pygame resources."""
        pygame.quit()


# ============================================================================
# CONTROLLER INPUT HANDLERS
# ============================================================================

class KeyboardController:
    """
    Keyboard input handler (display handled by DisplayController).
    """
    
    def __init__(self):
        """Initialize keyboard controller."""
        # Ensure pygame is initialized (for keyboard input)
        if not pygame.get_init():
            pygame.init()
        
        self.connected = True
        
        # Current state
        self.throttle = 0.0
        self.steer = 0.0
        
        # Control parameters - tuned for responsiveness
        self.throttle_step = 0.15  # Throttle change per frame (increased for faster response)
        self.steer_step = 0.20     # Steering change per frame (increased for faster response)
        self.throttle_decay = 0.85  # Throttle decay when no input (faster decay)
        self.steer_decay = 0.80     # Steering decay when no input (faster decay)
    
    def get_axes(self, steering_trim: float = 0.0) -> tuple[float, float]:
        """
        Get processed throttle and steering values from keyboard.
        
        Args:
            steering_trim: Calibration offset for steering (-0.2 to +0.2)
        
        Returns:
            (throttle, steer) tuple, each in range -1.0 to 1.0
        """
        if not self.connected:
            return 0.0, 0.0
        
        # Process pygame events (required for input)
        pygame.event.pump()
        
        # Get current keyboard state
        keys = pygame.key.get_pressed()
        
        # Throttle control (W/S keys) - more responsive
        if keys[pygame.K_w]:
            self.throttle = min(1.0, self.throttle + self.throttle_step)
        elif keys[pygame.K_s]:
            self.throttle = max(-1.0, self.throttle - self.throttle_step)
        elif keys[pygame.K_SPACE]:
            # Brake - rapid stop (more aggressive)
            self.throttle *= 0.3
        else:
            # Decay throttle toward zero when no input (faster)
            self.throttle *= self.throttle_decay
            if abs(self.throttle) < 0.01:
                self.throttle = 0.0
        
        # Steering control (A/D keys) - more responsive
        if keys[pygame.K_d]:
            self.steer = min(1.0, self.steer + self.steer_step)
        elif keys[pygame.K_a]:
            self.steer = max(-1.0, self.steer - self.steer_step)
        else:
            # Decay steering toward zero when no input (faster)
            self.steer *= self.steer_decay
            if abs(self.steer) < 0.01:
                self.steer = 0.0
        
        # Apply steering trim when there's throttle
        steer_output = self.steer
        if abs(self.throttle) > 0.05:
            steer_output = steer_output + steering_trim
        
        # Clamp values
        throttle_output = clamp(self.throttle)
        steer_output = clamp(steer_output)
        
        return throttle_output, steer_output
    
    def get_button(self, button_id: int) -> bool:
        """
        Check if ESC is pressed (exit button).
        
        Args:
            button_id: Ignored for keyboard (always checks ESC)
        
        Returns:
            True if ESC pressed, False otherwise
        """
        if not self.connected:
            return False
        
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        return keys[pygame.K_ESCAPE]
    
    def is_connected(self) -> bool:
        """Check if keyboard is available."""
        return self.connected
    
    def cleanup(self):
        """Cleanup pygame resources."""
        # Don't quit pygame here - DisplayController will handle it
        pass


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
            return  # Silent - will fall back to keyboard
        
        # Use first controller
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        self.connected = True
        # Silent success
    
    def get_axes(self) -> tuple[float, float]:
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
        self.calibration = {
            "steering_trim": 0.0,
            "motor_left_scale": 1.0,
            "motor_right_scale": 1.0
        }
    
    async def connect(self) -> bool:
        """
        Initialize UDP socket and request calibration data.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        try:
            import socket
            
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(0.5)  # 500ms timeout for calibration request (faster)
            
            # No connection needed for UDP - just send!
            self.connected = True
            
            # Request calibration data during connection (non-blocking)
            await self._request_calibration()
            
            return True
        
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.connected = False
            return False
    
    async def _request_calibration(self):
        """Request calibration data from robot during connection."""
        if not self.sock:
            return
        
        try:
            packet = {
                "cmd": "get_calibration",
                "seq": self.seq_num,
                "ts": int(time.time() * 1000)
            }
            
            message = json.dumps(packet).encode()
            self.sock.sendto(message, (self.robot_ip, self.robot_port))
            self.seq_num += 1
            
            # Wait for response (short timeout)
            try:
                data, _ = self.sock.recvfrom(4096)
                response = json.loads(data.decode().strip())
                
                if "calibration" in response:
                    self.calibration = response["calibration"]
                # Silent success - calibration loaded
            except socket.timeout:
                pass  # Silent timeout - use defaults
            except Exception:
                pass  # Silent error - use defaults
            
            # Reset timeout for normal operation (UDP is connectionless)
            self.sock.settimeout(0)  # Non-blocking for normal operation
            
        except Exception:
            pass  # Silent error - use defaults
    
    async def send_drive_command(self, throttle: float, steer: float) -> bool:
        """
        Send drive command to robot via UDP (instant, fire-and-forget).
        Applies calibration before sending.
        
        Args:
            throttle: Throttle value (-1.0 to 1.0)
            steer: Steering value (-1.0 to 1.0)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected or not self.sock:
            return False
        
        try:
            # Apply calibration (steering trim only when there's throttle)
            calibrated_steer = steer
            if abs(throttle) > 0.05:
                calibrated_steer = steer + self.calibration.get("steering_trim", 0.0)
                calibrated_steer = clamp(calibrated_steer)
            
            # Build command packet with timestamp
            packet = {
                "ts": int(time.time() * 1000),  # Timestamp in milliseconds
                "seq": self.seq_num,
                "cmd": "drive",
                "axes": {
                    "throttle": round(throttle, 3),
                    "steer": round(calibrated_steer, 3)
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
    
    def set_calibration(self, calibration_data: dict):
        """
        Update calibration data (e.g., from discovery response).
        
        Args:
            calibration_data: Dictionary with calibration values
        """
        if calibration_data:
            self.calibration.update(calibration_data)
            # Silent update - no verbose output
    
    async def disconnect(self):
        """Close UDP socket."""
        if self.sock:
            self.sock.close()
        
        self.connected = False
        # Silent disconnect


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
        
        # Always create display window
        self.display = DisplayController()
        
        # Try Xbox controller first, fall back to keyboard
        self.controller = XboxController()
        self.controller_type = "Xbox"
        
        if not self.controller.is_connected():
            self.controller = KeyboardController()
            self.controller_type = "Keyboard"
        
        # Initialize robot_id first (will be set from discovery later)
        self.robot_id = None  # Will be set from discovery
        
        # Update display with controller type
        self.display.update(controller_type=self.controller_type, robot_ip=robot_ip)
        
        # Set up profile callback (wrapper to queue profile changes)
        def profile_callback(profile_id, profile):
            # Put profile change request in queue (non-blocking)
            try:
                self.profile_change_queue.put_nowait((profile_id, profile))
            except:
                pass  # Queue full - ignore
        self.display.set_profile_callback(profile_callback)
        
        # Update display with profiles (robot_id will be None initially, updated later)
        profiles = self._get_profiles()
        self.display.update(profiles=profiles, current_profile_id=self.robot_id)
        
        self.connection = RobotConnection(robot_ip, ROBOT_PORT)
        self.running = False
        self.control_rate = 1.0 / CONTROL_RATE_HZ
        
        # Statistics
        self.packets_sent = 0
        self.start_time = time.time()
        self.robot_calibration = None  # Will be set from discovery or connection
        
        # Hz tracking (rolling average over last 10 packets)
        self.hz_history = []
        self.hz_history_size = 10
        self.last_send_time = None
        
        # Terminal command handling
        self.command_queue = asyncio.Queue()
        
        # Profile change queue (for GUI dropdown selections)
        self.profile_change_queue = asyncio.Queue()
    
    async def _on_profile_selected(self, profile_id, profile):
        """Handle profile selection from dropdown menu."""
        if not self.robot_id:
            print("❌ Robot ID unknown - cannot change profile")
            return
        
        # Send profile configuration
        profile_name_upper = profile['name'].upper()
        success, message = await self._send_profile_config(self.robot_id, profile_name_upper, profile['color'])
        
        if success:
            print(f"✅ Changed to profile: {profile_name_upper}")
            # Update display with new current profile
            self.display.update(current_profile_id=profile_id)
        else:
            print(f"❌ Failed to change profile: {message}")
    
    def _get_profiles(self):
        """Get robot profiles dictionary."""
        return {
            1: {"name": "THUNDER", "color": [255, 140, 0]},   # Orange
            2: {"name": "BLITZ", "color": [255, 255, 0]},      # Yellow
            3: {"name": "NITRO", "color": [255, 0, 0]},        # Red (changed from Magenta)
            4: {"name": "TURBO", "color": [0, 255, 0]},       # Green
            5: {"name": "SPEED", "color": [255, 255, 255]},   # White
            6: {"name": "BOLT", "color": [0, 0, 255]},        # Blue (changed from Purple)
            7: {"name": "FLASH", "color": [0, 255, 128]},     # Teal (changed from Pink)
            8: {"name": "STORM", "color": [0, 200, 255]}      # Cyan
        }
    
    def _show_boot_messages(self):
        """Show boot messages with profile information."""
        profiles = self._get_profiles()
        
        if self.robot_id:
            current_profile = profiles.get(self.robot_id, {"name": f"ROBOT-{self.robot_id}", "color": [255, 255, 255]})
            print(f"\nRobot #{self.robot_id} ({current_profile['name']}) at {self.robot_ip}")
        else:
            print(f"\nRobot at {self.robot_ip}")
        
        print("Profiles: " + ", ".join([f"{p['name']}" for p in profiles.values()]))
        print("Commands: profile \"NAME\" | help | quit")
        print()
    
    async def _handle_terminal_commands(self):
        """Background task to handle terminal commands."""
        import sys
        import threading
        import queue as thread_queue
        
        # Use a thread-safe queue for commands from stdin thread
        input_queue = thread_queue.Queue()
        
        # Use a thread to read stdin (blocking readline works in a thread)
        def read_stdin():
            import sys
            # Make stdin unbuffered for immediate reading
            try:
                sys.stdin.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass
            
            while self.running:
                try:
                    if sys.stdin.isatty() and not sys.stdin.closed:
                        # Blocking readline() - waits for user to press Enter
                        # This works in a separate thread
                        line = sys.stdin.readline()
                        if line:
                            line = line.strip()
                            if line:
                                # Put in thread queue immediately
                                input_queue.put(line)
                                # Flush to ensure it's processed
                                sys.stdout.flush()
                    else:
                        # Not a TTY or closed - wait a bit
                        time.sleep(0.1)
                except (EOFError, KeyboardInterrupt, BrokenPipeError):
                    break
                except Exception as e:
                    # Only print errors to stderr (won't interfere with commands)
                    print(f"ERROR in stdin thread: {e}", file=sys.stderr)
                    time.sleep(0.1)
        
        # Start stdin reader thread
        thread = threading.Thread(target=read_stdin, daemon=True)
        thread.start()
        
        # Give thread a moment to start
        await asyncio.sleep(0.1)
        
        # Process commands from thread queue
        while self.running:
            try:
                # Check thread queue (non-blocking)
                try:
                    command = input_queue.get_nowait()
                    # Process command immediately
                    sys.stdout.flush()  # Ensure output is flushed
                    await self._process_command(command)
                    sys.stdout.flush()  # Ensure response is flushed
                except thread_queue.Empty:
                    pass
            except Exception as e:
                # Debug: print error (but don't spam)
                import traceback
                print(f"ERROR processing command: {e}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
            await asyncio.sleep(0.05)  # Check more frequently
    
    async def _process_command(self, command: str):
        """Process a terminal command."""
        import sys
        cmd = command.strip()
        cmd_lower = cmd.lower()
        
        # Debug: confirm command received (remove after testing)
        # print(f"DEBUG: Processing command: {cmd}", file=sys.stderr)
        
        # Ensure we can print (flush stdout)
        sys.stdout.flush()
        
        if cmd_lower == 'profile' or cmd_lower.startswith('profile '):
            # Parse profile command: profile "PROFILE_NAME" or profile PROFILE_NAME
            profile_name = None
            if cmd_lower.startswith('profile '):
                # Extract profile name (handle quotes or no quotes)
                rest = cmd[8:].strip()  # Skip "profile "
                if rest.startswith('"') and rest.endswith('"'):
                    profile_name = rest[1:-1].strip()
                elif rest.startswith("'") and rest.endswith("'"):
                    profile_name = rest[1:-1].strip()
                else:
                    # No quotes - use the whole rest as profile name
                    profile_name = rest.strip()
            
            if profile_name:
                # Change to specific profile by name
                profiles = self._get_profiles()
                profile_id = None
                for rid, profile in profiles.items():
                    if profile['name'].upper() == profile_name.upper():
                        profile_id = rid
                        break
                
                if profile_id and self.robot_id:
                    # Send profile configuration directly via UDP
                    # Use robot's ID, but profile's name and color
                    # Use uppercase profile name to match firmware expectations
                    profile_name_upper = profile_name.upper()
                    success, message = await self._send_profile_config(self.robot_id, profile_name_upper, profiles[profile_id]['color'])
                    if success:
                        print(f"✅ Changed to profile: {profile_name_upper}")
                    else:
                        print(f"❌ Failed to change profile: {message}")
                elif not self.robot_id:
                    print("❌ Robot ID unknown - cannot change profile")
                else:
                    print(f"❌ Unknown profile: {profile_name}")
                    print(f"Available: {', '.join([p['name'] for p in profiles.values()])}")
            else:
                # Interactive profile selection
                print("Usage: profile \"PROFILE_NAME\"")
                profiles = self._get_profiles()
                print("Available profiles:")
                for rid, profile in profiles.items():
                    print(f"  {profile['name']}")
        elif cmd_lower == 'help' or cmd_lower == '?':
            profiles = self._get_profiles()
            print("\nCommands:")
            print("  profile \"NAME\"  - Change robot profile (e.g., profile \"BLITZ\")")
            print("  help            - Show this help")
            print("  quit            - Exit controller")
            print(f"\nProfiles: {', '.join([p['name'] for p in profiles.values()])}")
        elif cmd_lower == 'quit' or cmd_lower == 'exit':
            self.running = False
        else:
            print(f"Unknown command: {cmd}")
            print("Type 'help' for available commands")
    
    async def _send_profile_config(self, robot_id: int, name: str, color: list) -> tuple[bool, str]:
        """Send profile configuration to robot via UDP.
        
        Returns:
            (success: bool, message: str) tuple
        """
        import socket
        
        # Try up to 3 times with increasing timeout
        for attempt in range(3):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Increase timeout on retries
                timeout = 3.0 + (attempt * 1.0)  # 3s, 4s, 5s
                sock.settimeout(timeout)
                
                packet = {
                    "cmd": "set_profile",
                    "seq": 0,
                    "ts": int(time.time() * 1000),
                    "robot_id": robot_id,
                    "name": name,
                    "color": color
                }
                
                message = json.dumps(packet).encode()
                sock.sendto(message, (self.robot_ip, ROBOT_PORT))
                
                # Wait for response with longer timeout
                try:
                    data, _ = sock.recvfrom(4096)
                    response = json.loads(data.decode().strip())
                    
                    if response.get("type") == "profile_response":
                        if response.get("success"):
                            sock.close()
                            return True, response.get("message", "Profile updated")
                        else:
                            # Return error message from robot
                            error_msg = response.get("message", "Unknown error")
                            sock.close()
                            return False, error_msg
                    else:
                        sock.close()
                        return False, f"Unexpected response type: {response.get('type')}"
                except socket.timeout:
                    sock.close()
                    if attempt < 2:  # Retry if not last attempt
                        await asyncio.sleep(0.5)
                        continue
                    return False, "No response from robot (timeout after retries)"
                except json.JSONDecodeError as e:
                    sock.close()
                    return False, f"Invalid response from robot: {e}"
            except Exception as e:
                try:
                    sock.close()
                except:
                    pass
                if attempt < 2:
                    await asyncio.sleep(0.5)
                    continue
                return False, f"Error sending profile: {e}"
        
        return False, "Failed after multiple attempts"
    
    async def run(self):
        """Run the controller application."""
        self.running = True
        
        # Connect to robot (silent - status shown in pygame window)
        while self.running and not self.connection.connected:
            if not await self.connection.connect():
                await asyncio.sleep(RECONNECT_DELAY)
        
        if not self.running:
            return
        
        # Update display with connection info (all status in pygame window)
        profiles = self._get_profiles()
        self.display.update(
            robot_ip=self.robot_ip,
            robot_id=self.robot_id,
            connected=True,
            profiles=profiles,
            current_profile_id=self.robot_id
        )
        
        # Show profile information and commands on boot
        self._show_boot_messages()
        
        # Start terminal command handler
        command_task = asyncio.create_task(self._handle_terminal_commands())
        # Keep reference to prevent garbage collection
        self._command_task = command_task
        
        # Main control loop
        next_update_time = time.time()
        self.last_send_time = None  # Initialize for Hz tracking
        display_update_counter = 0

        # --- Button arming: require all relevant buttons to be released before accepting input ---
        start_armed = False
        back_armed = False
        while not (start_armed and back_armed):
            pygame.event.pump()
            start_pressed = self.controller.get_button(BUTTON_START)
            back_pressed = self.controller.get_button(BUTTON_BACK)
            if not start_pressed:
                start_armed = True
            if not back_pressed:
                back_armed = True
            if start_armed and back_armed:
                break
            await asyncio.sleep(0.01)
        # --- End arming ---
        
        try:
            while self.running:
                # Check for display window close
                if self.display.process_events():
                    break
                
                # Check for profile change requests from GUI
                try:
                    profile_id, profile = self.profile_change_queue.get_nowait()
                    await self._on_profile_selected(profile_id, profile)
                except asyncio.QueueEmpty:
                    pass
                
                # Check for exit button
                if self.controller_type == "Xbox":
                    # Only exit if START pressed without BACK
                    if (self.controller.get_button(BUTTON_START) and 
                        not self.controller.get_button(BUTTON_BACK)):
                        break
                else:
                    # Keyboard uses ESC handled in KeyboardController
                    if self.controller.get_button(BUTTON_START):
                        break
                
                # Rate limiting with precise timing
                now = time.time()
                
                if now >= next_update_time:
                    # Get controller input
                    throttle, steer = self.controller.get_axes()
                    
                    # Send command
                    if await self.connection.send_drive_command(throttle, steer):
                        self.packets_sent += 1
                        
                        # Track Hz (rolling average) - same calculation for terminal and display
                        if self.last_send_time is not None:
                            dt = now - self.last_send_time
                            if dt > 0:
                                current_hz = 1.0 / dt
                                self.hz_history.append(current_hz)
                                if len(self.hz_history) > self.hz_history_size:
                                    self.hz_history.pop(0)
                                
                                # Calculate average Hz (same for both displays)
                                avg_hz = sum(self.hz_history) / len(self.hz_history) if self.hz_history else 0.0
                                
                                # Update display
                                runtime = now - self.start_time
                                self.display.update(
                                    throttle=throttle,
                                    steer=steer,
                                    hz=avg_hz,
                                    packets_sent=self.packets_sent,
                                    runtime=runtime,
                                    connected=True
                                )
                                
                                # Terminal status removed - all info shown in pygame window
                                # This prevents interference with terminal input for commands
                        
                        self.last_send_time = now
                    else:
                        # Connection lost - try to reconnect
                        self.display.update(connected=False)
                        # Only print error to terminal, status shown in pygame window
                        print("⚠️  ERROR: Connection lost - Reconnecting...")
                        if not await self.connection.connect():
                            await asyncio.sleep(RECONNECT_DELAY)
                            continue
                        self.display.update(connected=True)
                        # Reconnection success shown in pygame window
                    
                    # Schedule next update precisely
                    next_update_time += self.control_rate
                    # If we're behind, catch up gradually
                    if next_update_time < now:
                        next_update_time = now + self.control_rate
                
                # Update display periodically (every 2 frames = 15 Hz)
                display_update_counter += 1
                if display_update_counter >= 2:
                    self.display._draw_ui()
                    display_update_counter = 0
                
                # Sleep only if we're ahead of schedule (prevents busy-waiting)
                sleep_time = next_update_time - time.time()
                if sleep_time > 0.0001:  # Only sleep if more than 0.1ms
                    await asyncio.sleep(min(sleep_time, 0.01))  # Cap at 10ms
                else:
                    # Very small yield to prevent CPU spinning
                    await asyncio.sleep(0.0001)
        
        except KeyboardInterrupt:
            pass  # Silent interrupt
        
        finally:
            # Don't print newline here - let shutdown handle cleanup
            await self.shutdown()
    
    async def shutdown(self):
        """Shutdown the application."""
        self.running = False
        
        # Send stop command
        if self.connection.connected:
            await self.connection.send_drive_command(0.0, 0.0)
            await asyncio.sleep(0.1)
        
        # Disconnect
        await self.connection.disconnect()
        
        # Cleanup display
        self.display.cleanup()
        
        # Statistics shown in pygame window, no terminal output


# ============================================================================
# ENTRY POINT
# ============================================================================

def print_usage():
    """Print usage information."""
    print("🤖 Pico-Go LAN Robot Controller")
    print()
    print("Usage:")
    print("  python3 controller_xbox.py                    # Auto-discover and connect")
    print("  python3 controller_xbox.py [robot_ip]          # Connect to specific robot")
    print("  python3 controller_xbox.py --configure         # Configure robot profile")
    print("  python3 controller_xbox.py --help              # Show this help")
    print()
    print("💡 To change robot profile (name/color):")
    print("   python3 configure_robot.py [robot_id] [robot_ip]")
    print("   Example: python3 configure_robot.py 1 192.168.8.230")
    print()
    print("   Or use: python3 controller_xbox.py --configure")
    print()


def main():
    """Main entry point."""
    # Check for help
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_usage()
        sys.exit(0)
    
    print("🤖 Pico-Go LAN Robot Controller")
    
    robot_ip = None
    robot_id = None  # Track robot ID for profile instructions
    
    # Check for profile configuration command
    if len(sys.argv) > 1 and sys.argv[1] in ['--configure', '-c', 'configure']:
        # Run profile configuration tool
        import subprocess
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_script = os.path.join(script_dir, 'configure_robot.py')
        if os.path.exists(config_script):
            # Pass remaining arguments to configure_robot.py
            subprocess.run([sys.executable, config_script] + sys.argv[2:])
        else:
            print("❌ configure_robot.py not found")
        sys.exit(0)
    
    # Check if IP provided as command-line argument
    if len(sys.argv) > 1:
        # Manual mode: use specified IP/hostname
        robot_address = sys.argv[1]
        robot_ip = resolve_robot_address(robot_address)
        if robot_ip:
            save_cached_robot(robot_ip)
            # Try to discover robot_id from this IP
            robots = discover_robots_on_network(timeout=1.0)
            for robot in robots:
                if robot['ip'] == robot_ip:
                    robot_id = robot['robot_id']
                    break
    else:
        # Auto mode: Always run discovery (don't blindly trust cache)
        robot_ip, robot_id = discover_and_select_robot()
    
    if robot_ip is None:
        print("❌ No robot selected. Exiting.")
        sys.exit(0)
    
    # Create and run application
    app = ControllerApp(robot_ip)
    
    # Store robot_id for connection message
    app.robot_id = robot_id
    
    # If we discovered the robot, apply calibration from discovery
    # (Otherwise it will be requested during connection)
    if len(sys.argv) == 1:  # Auto-discovery mode
        robots = discover_robots_on_network(timeout=1.0)
        for robot in robots:
            if robot['ip'] == robot_ip and robot.get('calibration'):
                app.connection.set_calibration(robot['calibration'])
                break
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass  # Silent exit
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
