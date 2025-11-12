#!/usr/bin/env python3
"""
Xbox Controller Axis/Button Mapping Tool
=========================================
Run this to identify all controller inputs and document them.

Usage:
    python3 scripts/test_controller_mapping.py
"""

import pygame
import time
import sys

def main():
    pygame.init()
    pygame.joystick.init()
    
    if pygame.joystick.get_count() == 0:
        print("❌ No controller found!")
        print("   Please connect an Xbox controller and try again.")
        return 1
    
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    
    print("=" * 70)
    print("🎮 Xbox Controller Mapping Tool")
    print("=" * 70)
    print(f"Controller: {joystick.get_name()}")
    print(f"Axes: {joystick.get_numaxes()}")
    print(f"Buttons: {joystick.get_numbuttons()}")
    print("\n📋 Instructions:")
    print("   - Move sticks and press triggers/buttons")
    print("   - Watch which axis/button numbers change")
    print("   - Press Ctrl+C when done")
    print("=" * 70)
    print()
    
    try:
        last_values = [0.0] * joystick.get_numaxes()
        last_buttons = [False] * joystick.get_numbuttons()
        
        while True:
            pygame.event.pump()
            
            # Check axes
            print("\r", end="")
            output = []
            
            for i in range(joystick.get_numaxes()):
                value = joystick.get_axis(i)
                
                # Highlight changed values
                if abs(value - last_values[i]) > 0.01:
                    output.append(f"\033[1;32mAxis {i}: {value:+.2f}\033[0m")
                elif abs(value) > 0.1:  # Show non-zero values
                    output.append(f"Axis {i}: {value:+.2f}")
                else:
                    output.append(f"Axis {i}: {value:+.2f}")
                
                last_values[i] = value
            
            # Check buttons (only show pressed)
            pressed_buttons = []
            for i in range(joystick.get_numbuttons()):
                is_pressed = joystick.get_button(i)
                if is_pressed:
                    pressed_buttons.append(f"\033[1;33mBtn {i}\033[0m")
                last_buttons[i] = is_pressed
            
            # Print combined output
            print(" | ".join(output), end="")
            if pressed_buttons:
                print(f" | {' '.join(pressed_buttons)}", end="")
            print("   ", end="")  # Clear trailing characters
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n")
        print("=" * 70)
        print("📝 Mapping Summary (based on what you tested):")
        print("=" * 70)
        print("Copy the values you observed into the controller configuration.")
        print("\nExample documentation:")
        print("# Axis 0: Left Stick X    (-1.0 = left,  +1.0 = right)")
        print("# Axis 1: Left Stick Y    (-1.0 = up,    +1.0 = down)")
        print("# Axis N: Left Trigger    (-1.0 = released, +1.0 = pressed)")
        print("# etc...")
        print("=" * 70)
        return 0

if __name__ == "__main__":
    sys.exit(main())
