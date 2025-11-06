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
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(MOTOR_PWM_FREQ)
        self.in1 = Pin(in1_pin, Pin.OUT)
        self.in2 = Pin(in2_pin, Pin.OUT)
        self.current_speed = 0.0
        self.stop()
    
    def set_speed(self, speed):
        """Set motor speed using Waveshare method."""
        speed = clamp(speed, -1.0, 1.0)
        self.current_speed = speed
        
        # Convert to percent and duty cycle
        speed_percent = abs(speed) * 100
        duty = int(speed_percent * MOTOR_MAX_DUTY / 100)
        self.pwm.duty_u16(duty)
        
        # Set direction (Waveshare style)
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
        
        self.enabled = True
        debug_print("Differential drive initialized (Waveshare)")
    
    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False
        self.left_motor.stop()
        self.right_motor.stop()
    
    def drive(self, throttle, steer):
        if not self.enabled:
            return
        
        throttle = clamp(throttle, -1.0, 1.0) * MAX_SPEED
        steer = clamp(steer, -1.0, 1.0) * TURN_RATE
        
        left_speed = clamp(throttle + steer, -1.0, 1.0)
        right_speed = clamp(throttle - steer, -1.0, 1.0)
        
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
