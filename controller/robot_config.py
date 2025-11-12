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
        """Get platform-specific configuration directory."""
        system = platform.system()
        
        if system == "Windows":
            appdata = os.getenv("APPDATA")
            if appdata:
                return Path(appdata) / "picogo"
            else:
                return Path.home() / "AppData" / "Roaming" / "picogo"
        
        elif system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "picogo"
        
        else:  # Linux and others
            xdg_config = os.getenv("XDG_CONFIG_HOME")
            if xdg_config:
                return Path(xdg_config) / "picogo"
            else:
                return Path.home() / ".config" / "picogo"
    
    def _load_config(self) -> Dict:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self._default_config()
        return self._default_config()
    
    def _default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "robots": [],
            "network": {
                "ssid": "DevNet-2.4G",
                "password": "DevPass**99"
            },
            "version": 1
        }
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_robots(self) -> List[Dict]:
        """Get list of all robots."""
        return self._config.get("robots", [])
    
    def add_robot(self, ip: str, name: Optional[str] = None, robot_id: Optional[int] = None):
        """Add a robot to configuration."""
        robots = self.get_robots()
        
        # Check if robot already exists
        for robot in robots:
            if robot.get("ip") == ip:
                # Update existing robot
                if name:
                    robot["name"] = name
                if robot_id:
                    robot["robot_id"] = robot_id
                robot["last_seen"] = datetime.now().isoformat()
                self._save_config()
                return
        
        # Add new robot
        new_robot = {
            "ip": ip,
            "name": name or f"Robot {ip}",
            "robot_id": robot_id,
            "added": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
        robots.append(new_robot)
        self._config["robots"] = robots
        self._save_config()
    
    def remove_robot(self, ip: str):
        """Remove a robot from configuration."""
        robots = self.get_robots()
        self._config["robots"] = [r for r in robots if r.get("ip") != ip]
        self._save_config()
    
    def update_robot(self, ip: str, **kwargs):
        """Update robot properties."""
        robots = self.get_robots()
        for robot in robots:
            if robot.get("ip") == ip:
                robot.update(kwargs)
                robot["last_seen"] = datetime.now().isoformat()
                self._save_config()
                return
    
    def get_network_config(self) -> Dict:
        """Get network configuration."""
        return self._config.get("network", {})
    
    def set_network_config(self, ssid: str, password: str):
        """Set network configuration."""
        self._config["network"] = {
            "ssid": ssid,
            "password": password
        }
        self._save_config()
