"""
Pico-Go LAN Robot - Motor Control Module
========================================
Motor control based on Waveshare Pico-Go v2 example code.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

from machine import Pin, PWM
from config import (
    PIN_MOTOR_A_PWM, PIN_MOTOR_A_IN1, PIN_MOTOR_A_IN2,
    PIN_MOTOR_B_PWM, PIN_MOTOR_B_IN1, PIN_MOTOR_B_IN2,
    MOTOR_PWM_FREQ, MOTOR_MAX_DUTY,
    MAX_SPEED, TURN_RATE
)
from utils import clamp, debug_print


class Motor:
    """Individual motor controller matching Waveshare implementation."""
    
    def __init__(self, pwm_pin, in1_pin, in2_pin, name="Motor"):
        self.name = name
        # Initialize PWM first and set to 0 immediately
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(MOTOR_PWM_FREQ)
        self.pwm.duty_u16(0)  # Set PWM to 0 BEFORE initializing direction pins
        
        # Now initialize direction pins
        self.in1 = Pin(in1_pin, Pin.OUT)
        self.in2 = Pin(in2_pin, Pin.OUT)
        
        # Ensure stopped state
        self.current_speed = 0.0
        self.stop()
    
    def set_speed(self, speed):
        """Set motor speed using Waveshare method."""
        speed = clamp(speed, -1.0, 1.0)
        self.current_speed = speed
        
        # If speed is effectively zero, use stop() to ensure all pins are safe
        if abs(speed) < 0.01:
            self.stop()
            return
        
        # Convert to percent and duty cycle
        speed_percent = abs(speed) * 100
        duty = int(speed_percent * MOTOR_MAX_DUTY / 100)
        
        # Set PWM duty FIRST (critical - Waveshare order)
        self.pwm.duty_u16(duty)
        
        # Then set direction (Waveshare style)
        if speed >= 0:
            self.in1.value(0)
            self.in2.value(1)
        else:
            self.in1.value(1)
            self.in2.value(0)
    
    def stop(self):
        self.pwm.duty_u16(0)
        self.in1.value(0)
        self.in2.value(0)
        self.current_speed = 0.0
    
    def get_speed(self):
        return self.current_speed


class DifferentialDrive:
    """Differential drive for Waveshare Pico-Go v2."""
    
    def __init__(self):
        self.stby = None  # No STBY on Waveshare
        
        self.left_motor = Motor(PIN_MOTOR_A_PWM, PIN_MOTOR_A_IN1, PIN_MOTOR_A_IN2, "Left")
        self.right_motor = Motor(PIN_MOTOR_B_PWM, PIN_MOTOR_B_IN1, PIN_MOTOR_B_IN2, "Right")
        
        self.enabled = False  # Start disabled for safety
        self.stop()  # Ensure motors are stopped
        debug_print("Differential drive initialized (Waveshare) - motors DISABLED")
    
    def enable(self):
        self.enabled = True
        # Ensure motors are stopped when enabling
        self.stop()
        debug_print("Motors ENABLED - stopped position")
    
    def disable(self):
        self.enabled = False
        self.left_motor.stop()
        self.right_motor.stop()
        debug_print("Motors DISABLED")
    
    def drive(self, throttle, steer):
        """
        Drive the robot with improved wheel mixing that preserves curvature.
        
        Per driver experience report: The old sum-and-clamp logic would clip
        whichever wheel exceeded ±1, altering the curvature mid-turn. The new
        approach normalizes the wheel commands to preserve the intended turn
        radius even at high combined throttle+steer.
        
        Args:
            throttle: Forward/reverse command (-1.0 to 1.0)
            steer: Steering command (-1.0 to 1.0, positive = clockwise)
        """
        if not self.enabled:
            return
        
        # Apply config limits
        throttle = clamp(throttle, -1.0, 1.0) * MAX_SPEED
        steer = clamp(steer, -1.0, 1.0) * TURN_RATE
        
        # Calculate raw wheel speeds (differential drive mixing)
        left_speed_raw = throttle + steer
        right_speed_raw = throttle - steer
        
        # Find the maximum magnitude to check if we need normalization
        max_magnitude = max(abs(left_speed_raw), abs(right_speed_raw))
        
        # If either wheel exceeds ±1.0, normalize BOTH wheels proportionally
        # This preserves the curvature (turn radius) while keeping speeds legal
        if max_magnitude > 1.0:
            left_speed = left_speed_raw / max_magnitude
            right_speed = right_speed_raw / max_magnitude
        else:
            left_speed = left_speed_raw
            right_speed = right_speed_raw
        
        # Final safety clamp (should be redundant after normalization)
        left_speed = clamp(left_speed, -1.0, 1.0)
        right_speed = clamp(right_speed, -1.0, 1.0)
        
        if abs(left_speed) > 0.1 or abs(right_speed) > 0.1:
            debug_print(f"MOTOR: L={left_speed:.2f} R={right_speed:.2f}")
        
        self.left_motor.set_speed(left_speed)
        self.right_motor.set_speed(right_speed)
    
    def stop(self):
        self.left_motor.stop()
        self.right_motor.stop()
    
    def coast(self):
        self.stop()
    
    def get_status(self):
        return {
            "enabled": self.enabled,
            "left_speed": self.left_motor.get_speed(),
            "right_speed": self.right_motor.get_speed()
        }


motor_controller = None

def initialize():
    global motor_controller
    try:
        debug_print("Creating motor controller (Waveshare)...")
        motor_controller = DifferentialDrive()
        debug_print("Motor controller created", force=True)
        return motor_controller
    except Exception as e:
        debug_print(f"Motor init failed: {e}", force=True)
        return None

def get_controller():
    return motor_controller
