#!/usr/bin/env python3
"""
Robot Configuration Manager
============================
Manages robot configurations and network settings with cross-platform support.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

import json
import os
import platform
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class RobotConfig:
    """Manages robot configuration storage and retrieval."""
    
    def __init__(self):
        """Initialize configuration manager with cross-platform paths."""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "robots.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()
    
    def _get_config_dir(self) -> Path:
        """
        Get platform-specific configuration directory.
        
        Returns:
            Path to configuration directory
        """
        system = platform.system()
        
        if system == "Windows":
            # Windows: %APPDATA%/picogo
            appdata = os.getenv("APPDATA")
            if appdata:
                return Path(appdata) / "picogo"
            else:
                return Path.home() / "AppData" / "Roaming" / "picogo"
        
        elif system == "Darwin":  # macOS
            # Mac: ~/Library/Application Support/picogo
            return Path.home() / "Library" / "Application Support" / "picogo"
        
        else:  # Linux and others
            # Linux: ~/.config/picogo
            xdg_config = os.getenv("XDG_CONFIG_HOME")
            if xdg_config:
                return Path(xdg_config) / "picogo"
            else:
                return Path.home() / ".config" / "picogo"
    
    def _load_config(self) -> Dict:
        """
        Load configuration from file or create default.
        
        Returns:
            Configuration dictionary
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Ensure required keys exist
                    if "network" not in config:
                        config["network"] = {"ssid": "", "password": ""}
                    if "robots" not in config:
                        config["robots"] = []
                    return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config: {e}")
                return self._default_config()
        else:
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """Create default configuration structure."""
        return {
            "network": {
                "ssid": "",
                "password": ""
            },
            "robots": []
        }
    
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_network_config(self) -> Dict[str, str]:
        """
        Get network configuration.
        
        Returns:
            Dictionary with 'ssid' and 'password'
        """
        return self._config.get("network", {"ssid": "", "password": ""})
    
    def set_network_config(self, ssid: str, password: str) -> bool:
        """
        Set network configuration.
        
        Args:
            ssid: Network SSID
            password: Network password
        
        Returns:
            True if successful
        """
        self._config["network"] = {
            "ssid": ssid,
            "password": password
        }
        return self.save()
    
    def get_robots(self) -> List[Dict]:
        """
        Get list of all robots.
        
        Returns:
            List of robot dictionaries
        """
        return self._config.get("robots", [])
    
    def get_robot_by_ip(self, ip: str) -> Optional[Dict]:
        """
        Get robot by IP address.
        
        Args:
            ip: Robot IP address
        
        Returns:
            Robot dictionary or None if not found
        """
        for robot in self.get_robots():
            if robot.get("ip") == ip:
                return robot
        return None
    
    def get_robot_by_id(self, robot_id: str) -> Optional[Dict]:
        """
        Get robot by ID.
        
        Args:
            robot_id: Robot ID
        
        Returns:
            Robot dictionary or None if not found
        """
        for robot in self.get_robots():
            if robot.get("robot_id") == robot_id:
                return robot
        return None
    
    def add_robot(self, robot_data: Dict) -> bool:
        """
        Add a new robot to configuration.
        
        Args:
            robot_data: Robot dictionary with required fields
        
        Returns:
            True if successful
        """
        # Ensure required fields
        if "ip" not in robot_data:
            return False
        
        # Check if robot already exists
        existing = self.get_robot_by_ip(robot_data["ip"])
        if existing:
            # Update existing robot
            existing.update(robot_data)
            existing["last_seen"] = datetime.now().isoformat()
        else:
            # Add new robot
            if "robot_id" not in robot_data:
                robot_data["robot_id"] = str(len(self.get_robots()) + 1)
            if "name" not in robot_data:
                robot_data["name"] = f"Robot {robot_data.get('robot_id', '?')}"
            if "controller_type" not in robot_data:
                robot_data["controller_type"] = "xbox"
            if "controller_path" not in robot_data:
                robot_data["controller_path"] = "controller_xbox.py"
            if "enabled" not in robot_data:
                robot_data["enabled"] = True
            
            robot_data["last_seen"] = datetime.now().isoformat()
            self._config["robots"].append(robot_data)
        
        return self.save()
    
    def update_robot(self, ip: str, updates: Dict) -> bool:
        """
        Update an existing robot.
        
        Args:
            ip: Robot IP address
            updates: Dictionary of fields to update
        
        Returns:
            True if successful, False if robot not found
        """
        robot = self.get_robot_by_ip(ip)
        if robot:
            robot.update(updates)
            robot["last_seen"] = datetime.now().isoformat()
            return self.save()
        return False
    
    def remove_robot(self, ip: str) -> bool:
        """
        Remove a robot from configuration.
        
        Args:
            ip: Robot IP address
        
        Returns:
            True if successful, False if robot not found
        """
        robots = self.get_robots()
        for i, robot in enumerate(robots):
            if robot.get("ip") == ip:
                robots.pop(i)
                self._config["robots"] = robots
                return self.save()
        return False
    
    def update_robot_last_seen(self, ip: str) -> bool:
        """
        Update last seen timestamp for a robot.
        
        Args:
            ip: Robot IP address
        
        Returns:
            True if successful
        """
        robot = self.get_robot_by_ip(ip)
        if robot:
            robot["last_seen"] = datetime.now().isoformat()
            return self.save()
        return False
    
    def export_config(self, filepath: str) -> bool:
        """
        Export configuration to a file.
        
        Args:
            filepath: Path to export file
        
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self._config, f, indent=2)
            return True
        except IOError as e:
            print(f"Error exporting config: {e}")
            return False
    
    def import_config(self, filepath: str) -> bool:
        """
        Import configuration from a file.
        
        Args:
            filepath: Path to import file
        
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r') as f:
                imported = json.load(f)
                # Validate structure
                if "network" in imported and "robots" in imported:
                    self._config = imported
                    return self.save()
                else:
                    print("Error: Invalid configuration file structure")
                    return False
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error importing config: {e}")
            return False

