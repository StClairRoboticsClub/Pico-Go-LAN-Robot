"""
Pico-Go LAN Robot - Calibration Module
=======================================
Stores and manages robot calibration data (steering trim, motor balance).

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

from utils import debug_print


class CalibrationData:
    """
    Robot calibration parameters.
    """
    
    def __init__(self):
        """Initialize with default calibration values."""
        self.steering_trim = 0.0  # Steering offset (-0.2 to +0.2)
        self.motor_left_scale = 1.0  # Left motor power multiplier (0.5 to 1.0)
        self.motor_right_scale = 1.0  # Right motor power multiplier (0.5 to 1.0)
    
    def to_dict(self):
        """
        Convert calibration to dictionary for JSON serialization.
        
        Returns:
            Dictionary with calibration values
        """
        return {
            "steering_trim": self.steering_trim,
            "motor_left_scale": self.motor_left_scale,
            "motor_right_scale": self.motor_right_scale
        }
    
    def from_dict(self, data):
        """
        Load calibration from dictionary.
        
        Args:
            data: Dictionary with calibration values
        """
        self.steering_trim = float(data.get("steering_trim", 0.0))
        self.motor_left_scale = float(data.get("motor_left_scale", 1.0))
        self.motor_right_scale = float(data.get("motor_right_scale", 1.0))
        
        # Clamp values to valid ranges
        self.steering_trim = max(-0.2, min(0.2, self.steering_trim))
        self.motor_left_scale = max(0.5, min(1.0, self.motor_left_scale))
        self.motor_right_scale = max(0.5, min(1.0, self.motor_right_scale))
    
    def reset(self):
        """Reset to default calibration values."""
        self.steering_trim = 0.0
        self.motor_left_scale = 1.0
        self.motor_right_scale = 1.0
        debug_print("Calibration reset to defaults")


# Global calibration instance
_calibration = CalibrationData()


def get_calibration():
    """
    Get the global calibration instance.
    
    Returns:
        CalibrationData instance
    """
    return _calibration


def initialize():
    """
    Initialize calibration system.
    
    Returns:
        CalibrationData instance
    """
    global _calibration
    _calibration = CalibrationData()
    debug_print("Calibration system initialized")
    return _calibration

