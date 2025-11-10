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


def discover_and_select_robot() -> str:
    """
    Discover robots on network and let user select one.
    
    Returns:
        Robot IP address or None
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
            return prompt_for_robot_ip()
        return None
    
    elif len(robots) == 1:
        # Exactly one robot found - auto-select
        robot = robots[0]
        print(f"✅ Robot #{robot['robot_id']} ({robot['hostname']}) at {robot['ip']}")
        save_cached_robot(robot['ip'])
        return robot['ip']
    
    else:
        # Multiple robots found - let user choose
        print(f"📋 Found {len(robots)} robots:")
        for i, robot in enumerate(robots, 1):
            print(f"   {i}. Robot #{robot['robot_id']} ({robot['hostname']}) - {robot['ip']}")
        
        while True:
            try:
                choice = input(f"\nSelect (1-{len(robots)}) or 'q': ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                idx = int(choice) - 1
                if 0 <= idx < len(robots):
                    robot = robots[idx]
                    save_cached_robot(robot['ip'])
                    return robot['ip']
                else:
                    print(f"❌ Enter 1-{len(robots)}")
            
            except ValueError:
                print("❌ Invalid input")
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
# CONTROLLER INPUT HANDLERS
# ============================================================================

class KeyboardController:
    """
    Enhanced keyboard input handler with improved pygame window.
    Modern UI with visual feedback and better layout.
    """
    
    def __init__(self):
        """Initialize keyboard controller with improved pygame window."""
        pygame.init()
        
        # Window configuration
        self.window_width = 600
        self.window_height = 500
        self.bg_color = (20, 20, 30)  # Dark blue-gray
        self.accent_color = (100, 200, 255)  # Light blue
        self.text_color = (255, 255, 255)  # White
        self.success_color = (100, 255, 100)  # Green
        self.warning_color = (255, 200, 100)  # Orange
        
        # Create window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("🤖 Pico-Go LAN Robot - Keyboard Controller")
        
        # Set up fonts
        pygame.font.init()
        self.title_font = pygame.font.Font(None, 36)
        self.header_font = pygame.font.Font(None, 24)
        self.body_font = pygame.font.Font(None, 20)
        self.value_font = pygame.font.Font(None, 32)
        
        self.connected = True
        
        # Current state
        self.throttle = 0.0
        self.steer = 0.0
        
        # Control parameters
        self.throttle_step = 0.05  # Throttle change per frame
        self.steer_step = 0.05     # Steering change per frame
        self.throttle_decay = 0.95  # Throttle decay when no input
        self.steer_decay = 0.90     # Steering decay when no input
        
        # Initial render
        self._draw_ui()
    
    def _draw_ui(self):
        """Draw improved UI in the pygame window."""
        # Clear screen
        self.screen.fill(self.bg_color)
        
        # Title bar
        title_rect = pygame.Rect(0, 0, self.window_width, 50)
        pygame.draw.rect(self.screen, (30, 30, 45), title_rect)
        title_text = self.title_font.render("🤖 Pico-Go LAN Robot", True, self.accent_color)
        self.screen.blit(title_text, (20, 12))
        subtitle_text = self.body_font.render("Keyboard Controller", True, (200, 200, 200))
        self.screen.blit(subtitle_text, (20, 35))
        
        y = 70
        
        # Controls section
        controls_header = self.header_font.render("Controls", True, self.accent_color)
        self.screen.blit(controls_header, (20, y))
        y += 30
        
        controls = [
            ("W / S", "Throttle forward/reverse"),
            ("A / D", "Steer left/right"),
            ("SPACE", "Brake (rapid stop)"),
            ("ESC", "Exit")
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
        bar_x = 120
        bar_y = y - 5
        
        # Background bar
        pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_width, bar_height))
        
        # Throttle value bar (green for forward, red for reverse)
        throttle_width = int(abs(self.throttle) * bar_width)
        if self.throttle > 0:
            bar_color = self.success_color  # Green for forward
        elif self.throttle < 0:
            bar_color = (255, 100, 100)  # Red for reverse
        else:
            bar_color = (60, 60, 60)  # Gray for neutral
        
        if throttle_width > 0:
            if self.throttle > 0:
                pygame.draw.rect(self.screen, bar_color, (bar_x, bar_y, throttle_width, bar_height))
            else:
                pygame.draw.rect(self.screen, bar_color, (bar_x + bar_width - throttle_width, bar_y, throttle_width, bar_height))
        
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
            steer_x = bar_x + (bar_width // 2) - (steer_width // 2)
            if self.steer > 0:
                # Right turn
                pygame.draw.rect(self.screen, self.accent_color, 
                               (bar_x + bar_width // 2, bar_y, steer_width // 2, bar_height))
            else:
                # Left turn
                pygame.draw.rect(self.screen, self.accent_color, 
                               (bar_x + bar_width // 2 - steer_width // 2, bar_y, steer_width // 2, bar_height))
        
        # Center line
        pygame.draw.line(self.screen, (100, 100, 100), (bar_x + bar_width // 2, bar_y), 
                        (bar_x + bar_width // 2, bar_y + bar_height), 2)
        
        # Steering value text
        steer_value = self.value_font.render(f"{self.steer:+.2f}", True, self.text_color)
        self.screen.blit(steer_value, (bar_x + bar_width + 10, y - 2))
        
        y += 60
        
        # Instructions
        info_text = self.body_font.render("Keep this window focused to control the robot", True, (150, 150, 150))
        self.screen.blit(info_text, (20, y))
        
        pygame.display.flip()
    
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
        
        # Process pygame events (required for window to stay responsive)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.connected = False
                return 0.0, 0.0
        
        # Get current keyboard state
        keys = pygame.key.get_pressed()
        
        # Throttle control (W/S keys)
        if keys[pygame.K_w]:
            self.throttle = min(1.0, self.throttle + self.throttle_step)
        elif keys[pygame.K_s]:
            self.throttle = max(-1.0, self.throttle - self.throttle_step)
        elif keys[pygame.K_SPACE]:
            # Brake - rapid stop
            self.throttle *= 0.5
        else:
            # Decay throttle toward zero when no input
            self.throttle *= self.throttle_decay
            if abs(self.throttle) < 0.01:
                self.throttle = 0.0
        
        # Steering control (A/D keys)
        if keys[pygame.K_d]:
            self.steer = min(1.0, self.steer + self.steer_step)
        elif keys[pygame.K_a]:
            self.steer = max(-1.0, self.steer - self.steer_step)
        else:
            # Decay steering toward zero when no input
            self.steer *= self.steer_decay
            if abs(self.steer) < 0.01:
                self.steer = 0.0
        
        # Update UI
        self._draw_ui()
        
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
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
        
        keys = pygame.key.get_pressed()
        return keys[pygame.K_ESCAPE]
    
    def is_connected(self) -> bool:
        """Check if keyboard is available."""
        return self.connected
    
    def cleanup(self):
        """Cleanup pygame resources."""
        pygame.quit()


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
        self.back_was_pressed = False  # Track BACK button state for combo detection
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
    
    def check_charging_combo(self) -> bool:
        """
        Check if charging mode button combo is pressed (BACK + START).
        Returns True on combo press (rising edge), False otherwise.
        """
        if not self.connected:
            return False
        
        pygame.event.pump()
        
        # Check if BACK is currently pressed
        back_pressed = self.joystick.get_button(BUTTON_BACK)
        start_pressed = self.joystick.get_button(BUTTON_START)
        
        # Detect rising edge of BACK button while START is held
        combo_activated = False
        if back_pressed and start_pressed and not self.back_was_pressed:
            combo_activated = True
        
        # Update state for next check
        self.back_was_pressed = back_pressed
        
        return combo_activated
    
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
    
    async def send_charging_command(self, enable: bool) -> bool:
        """
        Send charging mode command to robot.
        
        Args:
            enable: True to enter charging mode, False to exit
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected or not self.sock:
            return False
        
        try:
            packet = {
                "ts": int(time.time() * 1000),
                "seq": self.seq_num,
                "cmd": "charging",
                "enable": enable
            }
            
            message = json.dumps(packet).encode()
            self.sock.sendto(message, (self.robot_ip, self.robot_port))
            
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
        
        # Try Xbox controller first, fall back to keyboard
        self.controller = XboxController()
        self.controller_type = "Xbox"
        
        if not self.controller.is_connected():
            self.controller = KeyboardController()
            self.controller_type = "Keyboard"
        
        self.connection = RobotConnection(robot_ip, ROBOT_PORT)
        self.running = False
        self.control_rate = 1.0 / CONTROL_RATE_HZ
        
        # Statistics
        self.packets_sent = 0
        self.start_time = time.time()
        self.robot_calibration = None  # Will be set from discovery or connection
    
    async def run(self):
        """Run the controller application."""
        self.running = True
        
        # Connect to robot
        print("🔌 Connecting...", end='', flush=True)
        while self.running and not self.connection.connected:
            if not await self.connection.connect():
                print(f"\r⏳ Retrying...", end='', flush=True)
                await asyncio.sleep(RECONNECT_DELAY)
        
        if not self.running:
            return
        
        if self.controller_type == "Keyboard":
            # For keyboard, connection message goes on stats line
            with self.controller._display_lock:
                stats_line = getattr(self.controller, '_stats_line', 11)
                sys.stdout.write(f"\033[{stats_line};1H\033[K✅ Connected to {self.robot_ip}\n")
                sys.stdout.flush()
        else:
            print(f"\r{' ' * 50}\r✅ Connected to {self.robot_ip}", flush=True)
            print("🎮 Controls: RT=Forward, LT=Reverse, LS=Steer, START=Exit")
        
        # Main control loop
        last_update = time.time()
        charging_mode_active = False

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
                # Check for charging mode combo (BACK + START for Xbox)
                if self.controller_type == "Xbox":
                    if self.controller.check_charging_combo():
                        charging_mode_active = not charging_mode_active
                        mode_str = "ENABLED" if charging_mode_active else "DISABLED"
                        print(f"\n🔋 Charging mode {mode_str}")
                        await self.connection.send_charging_command(charging_mode_active)
                        continue
                
                # Check for exit button (START only, not combo)
                if self.controller_type == "Xbox":
                    # Only exit if START pressed without BACK
                    if (self.controller.get_button(BUTTON_START) and 
                        not self.controller.get_button(BUTTON_BACK)):
                        break
                else:
                    # Keyboard uses ESC handled in KeyboardController
                    if self.controller.get_button(BUTTON_START):
                        break
                
                # Rate limiting
                now = time.time()
                elapsed = now - last_update
                
                if elapsed >= self.control_rate:
                    # Get controller input
                    throttle, steer = self.controller.get_axes()
                    
                    # Send command
                    if await self.connection.send_drive_command(throttle, steer):
                        self.packets_sent += 1
                        
                        # Print status (overwrites same line)
                        if self.packets_sent % 30 == 0:
                            runtime = time.time() - self.start_time
                            rate = self.packets_sent / runtime if runtime > 0 else 0
                            print(f"\r📊 {self.packets_sent} pkts | {rate:.1f} Hz | T:{throttle:+.2f} S:{steer:+.2f}", end='', flush=True)
                    else:
                        # Connection lost - try to reconnect
                        print("\r⚠️  Reconnecting...", end='', flush=True)
                        if not await self.connection.connect():
                            await asyncio.sleep(RECONNECT_DELAY)
                            continue
                        print(f"\r{' ' * 50}\r", end='', flush=True)  # Clear reconnect message
                    
                    last_update = now
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(0.001)
        
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
        
        # Cleanup controllers
        if self.controller_type == "Keyboard":
            self.controller.cleanup()
        elif self.controller_type == "Xbox":
            pygame.quit()
        
        # Brief statistics
        runtime = time.time() - self.start_time
        avg_rate = self.packets_sent / runtime if runtime > 0 else 0
        print(f"\n📊 {self.packets_sent} pkts in {runtime:.1f}s ({avg_rate:.1f} Hz avg)")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    print("🤖 Pico-Go LAN Robot Controller")
    
    robot_ip = None
    
    # Check if IP provided as command-line argument
    if len(sys.argv) > 1:
        # Manual mode: use specified IP/hostname
        robot_address = sys.argv[1]
        robot_ip = resolve_robot_address(robot_address)
        if robot_ip:
            save_cached_robot(robot_ip)
    else:
        # Auto mode: Always run discovery (don't blindly trust cache)
        robot_ip = discover_and_select_robot()
    
    if robot_ip is None:
        print("❌ No robot selected. Exiting.")
        sys.exit(0)
    
    # Create and run application
    app = ControllerApp(robot_ip)
    
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
