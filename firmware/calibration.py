"""
Pico-Go LAN Robot - Calibration Storage Module
==============================================
Stores robot-specific calibration data in non-volatile storage.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT

Calibration Parameters:
- steering_trim: Offset to compensate for drift (-0.5 to +0.5)
- motor_left_scale: Left motor power multiplier (0.5 to 1.0)
- motor_right_scale: Right motor power multiplier (0.5 to 1.0)
"""

import json
import os
from utils import debug_print

# Calibration file path (stored in filesystem)
CALIBRATION_FILE = "/calibration.json"

# Default calibration values
DEFAULT_CALIBRATION = {
    "robot_id": "unknown",
    "steering_trim": 0.0,        # -0.5 to +0.5 (positive = right correction)
    "motor_left_scale": 1.0,     # 0.5 to 1.0 (reduce if left motor too strong)
    "motor_right_scale": 1.0,    # 0.5 to 1.0 (reduce if right motor too strong)
    "version": 1
}


class CalibrationManager:
    """Manages robot calibration data persistence."""
    
    def __init__(self, robot_id: str = "unknown"):
        """
        Initialize calibration manager.
        
        Args:
            robot_id: Unique robot identifier (e.g., "picogo1")
        """
        self.robot_id = robot_id
        self.calibration = DEFAULT_CALIBRATION.copy()
        self.calibration["robot_id"] = robot_id
        self.load()
    
    def load(self):
        """Load calibration from file, or create with defaults if not found."""
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
                
                # Validate and merge with defaults (in case new fields added)
                for key in DEFAULT_CALIBRATION:
                    if key in data:
                        self.calibration[key] = data[key]
                
                # Update robot ID
                self.calibration["robot_id"] = self.robot_id
                
                debug_print(f"✅ Calibration loaded from {CALIBRATION_FILE}", force=True)
                debug_print(f"   Steering trim: {self.calibration['steering_trim']:.3f}", force=True)
                debug_print(f"   Motor balance: L={self.calibration['motor_left_scale']:.2f} R={self.calibration['motor_right_scale']:.2f}", force=True)
                
        except OSError:
            # File doesn't exist - create with defaults
            debug_print(f"⚠️  No calibration file found, creating defaults", force=True)
            self.save()
        except Exception as e:
            debug_print(f"❌ Error loading calibration: {e}", force=True)
            # Use defaults
    
    def save(self):
        """Save current calibration to file."""
        try:
            with open(CALIBRATION_FILE, 'w') as f:
                json.dump(self.calibration, f)
            debug_print(f"✅ Calibration saved to {CALIBRATION_FILE}", force=True)
            return True
        except Exception as e:
            debug_print(f"❌ Error saving calibration: {e}", force=True)
            return False
    
    def get(self, key: str, default=None):
        """
        Get calibration value.
        
        Args:
            key: Calibration parameter name
            default: Default value if key not found
        
        Returns:
            Calibration value
        """
        return self.calibration.get(key, default)
    
    def set(self, key: str, value):
        """
        Set calibration value.
        
        Args:
            key: Calibration parameter name
            value: New value
        
        Returns:
            True if successful
        """
        if key == "robot_id":
            debug_print("⚠️  Cannot change robot_id via set()", force=True)
            return False
        
        if key in DEFAULT_CALIBRATION:
            self.calibration[key] = value
            return True
        else:
            debug_print(f"⚠️  Unknown calibration key: {key}", force=True)
            return False
    
    def update(self, updates: dict):
        """
        Update multiple calibration values.
        
        Args:
            updates: Dictionary of key-value pairs to update
        
        Returns:
            True if all updates successful
        """
        success = True
        for key, value in updates.items():
            if not self.set(key, value):
                success = False
        return success
    
    def get_all(self) -> dict:
        """
        Get all calibration data.
        
        Returns:
            Complete calibration dictionary
        """
        return self.calibration.copy()
    
    def reset_to_defaults(self):
        """Reset calibration to factory defaults."""
        self.calibration = DEFAULT_CALIBRATION.copy()
        self.calibration["robot_id"] = self.robot_id
        debug_print("⚠️  Calibration reset to defaults", force=True)
        return self.save()


# Global instance (initialized by main)
calibration_manager = None


def initialize(robot_id: str):
    """
    Initialize calibration manager.
    
    Args:
        robot_id: Unique robot identifier
    
    Returns:
        CalibrationManager instance
    """
    global calibration_manager
    calibration_manager = CalibrationManager(robot_id)
    return calibration_manager


def get_manager():
    """Get global calibration manager instance."""
    return calibration_manager
