#!/usr/bin/env python3
"""
Xbox Controller Axis Tester
============================
Tests all axes and buttons to document the correct mappings.

Run this script and press each trigger/stick to see which axis number it is.
"""

import pygame
import time
import sys

def main():
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("❌ No controller found!")
        sys.exit(1)
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    
    print("=" * 70)
    print(f"Controller: {joystick.get_name()}")
    print(f"Total Axes: {joystick.get_numaxes()}")
    print(f"Total Buttons: {joystick.get_numbuttons()}")
    print("=" * 70)
    print("\n📋 INSTRUCTIONS:")
    print("   1. Leave all controls at rest position")
    print("   2. Note which axes show -1.000 (released triggers)")
    print("   3. Press LEFT trigger fully -> see which axis goes to +1.000")
    print("   4. Press RIGHT trigger fully -> see which axis goes to +1.000")
    print("   5. Move LEFT stick X (left/right) -> see which axis changes")
    print("   6. Press Ctrl+C when done\n")
    print("=" * 70)
    
    try:
        while True:
            pygame.event.pump()
            
            # Print all axes on one line
            print("\r", end="")
            for i in range(joystick.get_numaxes()):
                value = joystick.get_axis(i)
                # Highlight non-zero values
                if abs(value) > 0.1:
                    print(f"Axis {i}: \033[1;32m{value:+.3f}\033[0m | ", end="")
                else:
                    print(f"Axis {i}: {value:+.3f} | ", end="")
            
            print("    ", end="")  # Clear any trailing text
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("📝 DOCUMENT YOUR FINDINGS:")
        print("   - Left Trigger Axis: ?")
        print("   - Right Trigger Axis: ?")
        print("   - Left Stick X Axis: ?")
        print("=" * 70)
        print("\n✅ Test complete!")

if __name__ == "__main__":
    main()
