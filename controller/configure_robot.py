#!/usr/bin/env python3
"""
Robot Profile Configuration Tool
================================
Configure robot profiles (name and color) for robots 1-8.

Usage:
    python3 configure_robot.py [robot_id] [robot_ip]
    
Example:
    python3 configure_robot.py 1 192.168.8.230
"""

import sys
import socket
import json
import time

# Default robot profiles (8 profiles)
DEFAULT_PROFILES = {
    1: {"name": "THUNDER", "color": [255, 140, 0]},   # Orange
    2: {"name": "BLITZ", "color": [255, 255, 0]},    # Yellow
    3: {"name": "NITRO", "color": [255, 0, 0]},      # Red (changed from Magenta)
    4: {"name": "TURBO", "color": [0, 255, 0]},      # Green
    5: {"name": "SPEED", "color": [255, 255, 255]},   # White
    6: {"name": "BOLT", "color": [0, 0, 255]},       # Blue (changed from Purple)
    7: {"name": "FLASH", "color": [0, 255, 128]},    # Teal (changed from Pink)
    8: {"name": "STORM", "color": [0, 200, 255]}     # Cyan
}

ROBOT_PORT = 8765


def get_color_input(prompt, default_color):
    """Get RGB color input from user."""
    print(f"\n{prompt}")
    print(f"Current: RGB({default_color[0]}, {default_color[1]}, {default_color[2]})")
    print("Enter RGB values (0-255) separated by commas, or press Enter to keep current:")
    
    while True:
        try:
            user_input = input("RGB: ").strip()
            if not user_input:
                return default_color
            
            parts = [int(x.strip()) for x in user_input.split(',')]
            if len(parts) != 3:
                print("❌ Please enter 3 values (R, G, B)")
                continue
            
            if any(x < 0 or x > 255 for x in parts):
                print("❌ Values must be between 0 and 255")
                continue
            
            return parts
        except ValueError:
            print("❌ Invalid input. Please enter numbers separated by commas.")
        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            sys.exit(0)


def send_profile_config(robot_ip, robot_id, name, color):
    """Send profile configuration to robot."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        
        # Send set_profile command
        packet = {
            "cmd": "set_profile",
            "seq": 0,
            "ts": int(time.time() * 1000),
            "robot_id": robot_id,
            "name": name,
            "color": color
        }
        
        message = json.dumps(packet).encode()
        sock.sendto(message, (robot_ip, ROBOT_PORT))
        
        # Wait for response
        try:
            data, _ = sock.recvfrom(4096)
            response = json.loads(data.decode().strip())
            
            if response.get("type") == "profile_response" and response.get("success"):
                return True
            else:
                print(f"⚠️  Robot response: {response.get('message', 'Unknown error')}")
                return False
        except socket.timeout:
            print("⚠️  No response from robot (timeout)")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        sock.close()


def main():
    """Main configuration tool."""
    print("╔═══════════════════════════════════════════════════════╗")
    print("║     🤖 Robot Profile Configuration Tool             ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()
    
    # Get robot ID
    if len(sys.argv) > 1:
        try:
            robot_id = int(sys.argv[1])
            if robot_id < 1 or robot_id > 8:
                print(f"❌ Robot ID must be between 1 and 8")
                sys.exit(1)
        except ValueError:
            print(f"❌ Invalid robot ID: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("Available robot profiles (1-8):")
        for rid, profile in DEFAULT_PROFILES.items():
            color = profile["color"]
            print(f"  {rid}. {profile['name']:8s} - RGB({color[0]:3d}, {color[1]:3d}, {color[2]:3d})")
        print()
        
        while True:
            try:
                robot_id = int(input("Enter robot ID (1-8): ").strip())
                if 1 <= robot_id <= 8:
                    break
                print("❌ Robot ID must be between 1 and 8")
            except ValueError:
                print("❌ Please enter a number")
            except KeyboardInterrupt:
                print("\n❌ Cancelled")
                sys.exit(0)
    
    # Get robot IP
    if len(sys.argv) > 2:
        robot_ip = sys.argv[2]
    else:
        robot_ip = input(f"Enter robot IP address for robot #{robot_id}: ").strip()
        if not robot_ip:
            print("❌ IP address required")
            sys.exit(1)
    
    # Get current profile
    profile = DEFAULT_PROFILES.get(robot_id, {"name": f"ROBOT-{robot_id}", "color": [255, 255, 255]})
    
    print(f"\n📝 Configuring Robot #{robot_id}")
    print(f"   Current name: {profile['name']}")
    print(f"   Current color: RGB{profile['color']}")
    print()
    
    # Get new name
    new_name = input(f"Enter new name (or Enter to keep '{profile['name']}'): ").strip()
    if not new_name:
        new_name = profile['name']
    elif len(new_name) > 20:
        print("⚠️  Name too long, truncating to 20 characters")
        new_name = new_name[:20]
    
    # Get new color
    new_color = get_color_input("Color Configuration", profile['color'])
    
    # Confirm
    print(f"\n📋 Configuration Summary:")
    print(f"   Robot ID: {robot_id}")
    print(f"   Name: {new_name}")
    print(f"   Color: RGB({new_color[0]}, {new_color[1]}, {new_color[2]})")
    print(f"   Target: {robot_ip}:{ROBOT_PORT}")
    
    confirm = input("\nApply this configuration? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        sys.exit(0)
    
    # Send configuration
    print(f"\n📡 Sending configuration to robot...")
    if send_profile_config(robot_ip, robot_id, new_name, new_color):
        print("✅ Configuration applied successfully!")
        print("   Note: Robot will use this profile after restart or reconnection.")
    else:
        print("❌ Failed to apply configuration")
        print("   Make sure:")
        print("   - Robot is powered on and connected to WiFi")
        print("   - Robot firmware supports set_profile command")
        print("   - IP address is correct")
        sys.exit(1)


if __name__ == "__main__":
    main()

