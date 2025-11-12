#!/usr/bin/env python3
"""
Controller Process Manager
===========================
Manages launching and monitoring multiple controller subprocesses.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

import subprocess
import sys
import os
import platform
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class ControllerManager:
    """Manages controller subprocess lifecycle."""
    
    def __init__(self):
        """Initialize controller manager."""
        self.controllers: Dict[str, subprocess.Popen] = {}
        self.controller_info: Dict[str, Dict] = {}  # Additional info per controller
        self.controller_scripts = {
            "xbox": "controller_xbox.py",
            "gamepad": "controller_gamepad.py",  # To be created
            "keyboard": "controller_keyboard.py"  # To be created
        }
    
    def _get_controller_path(self, controller_type: str) -> Optional[Path]:
        """
        Get path to controller script.
        
        Args:
            controller_type: Type of controller (xbox, gamepad, keyboard)
        
        Returns:
            Path to controller script or None if not found
        """
        script_name = self.controller_scripts.get(controller_type)
        if not script_name:
            return None
        
        # Get directory of this file
        controller_dir = Path(__file__).parent
        script_path = controller_dir / script_name
        
        if script_path.exists():
            return script_path
        return None
    
    def launch_controller(self, robot_ip: str, robot_id: Optional[str] = None, 
                         controller_type: str = "xbox") -> bool:
        """
        Launch a controller subprocess for a robot.
        
        Args:
            robot_ip: Robot IP address
            robot_id: Optional robot ID
            controller_type: Type of controller (xbox, gamepad, keyboard)
        
        Returns:
            True if launched successfully, False otherwise
        """
        # Check if controller already running for this robot
        if robot_ip in self.controllers:
            process = self.controllers[robot_ip]
            if process.poll() is None:  # Still running
                return False  # Already running
        
        # Get controller script path
        script_path = self._get_controller_path(controller_type)
        if not script_path:
            print(f"Error: Controller script not found for type '{controller_type}'")
            return False
        
        # Determine Python executable
        python_exe = sys.executable
        
        # Build command
        cmd = [python_exe, str(script_path), robot_ip]
        
        # Launch subprocess
        try:
            # Use CREATE_NEW_PROCESS_GROUP on Windows to allow separate window
            creation_flags = 0
            if platform.system() == "Windows":
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
                cwd=str(script_path.parent)
            )
            
            self.controllers[robot_ip] = process
            self.controller_info[robot_ip] = {
                "robot_id": robot_id,
                "controller_type": controller_type,
                "started_at": datetime.now().isoformat(),
                "pid": process.pid
            }
            
            return True
            
        except Exception as e:
            print(f"Error launching controller: {e}")
            return False
    
    def stop_controller(self, robot_ip: str) -> bool:
        """
        Stop a controller subprocess.
        
        Args:
            robot_ip: Robot IP address
        
        Returns:
            True if stopped successfully, False if not found or already stopped
        """
        if robot_ip not in self.controllers:
            return False
        
        process = self.controllers[robot_ip]
        
        if process.poll() is None:  # Still running
            try:
                # Try graceful termination first
                if platform.system() == "Windows":
                    process.terminate()
                else:
                    process.terminate()
                
                # Wait a bit for graceful shutdown
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    process.kill()
                    process.wait()
                
                del self.controllers[robot_ip]
                if robot_ip in self.controller_info:
                    del self.controller_info[robot_ip]
                return True
            except Exception as e:
                print(f"Error stopping controller: {e}")
                return False
        else:
            # Already stopped, just clean up
            del self.controllers[robot_ip]
            if robot_ip in self.controller_info:
                del self.controller_info[robot_ip]
            return True
    
    def is_controller_running(self, robot_ip: str) -> bool:
        """
        Check if controller is running for a robot.
        
        Args:
            robot_ip: Robot IP address
        
        Returns:
            True if running, False otherwise
        """
        if robot_ip not in self.controllers:
            return False
        
        process = self.controllers[robot_ip]
        return process.poll() is None
    
    def get_controller_status(self, robot_ip: str) -> Optional[Dict]:
        """
        Get status information for a controller.
        
        Args:
            robot_ip: Robot IP address
        
        Returns:
            Dictionary with status info or None if not found
        """
        if robot_ip not in self.controllers:
            return None
        
        process = self.controllers[robot_ip]
        info = self.controller_info.get(robot_ip, {}).copy()
        
        info["running"] = process.poll() is None
        info["return_code"] = process.poll()
        
        return info
    
    def get_all_running_controllers(self) -> List[str]:
        """
        Get list of robot IPs with running controllers.
        
        Returns:
            List of robot IP addresses
        """
        running = []
        for robot_ip, process in list(self.controllers.items()):
            if process.poll() is None:  # Still running
                running.append(robot_ip)
            else:
                # Clean up stopped processes
                del self.controllers[robot_ip]
                if robot_ip in self.controller_info:
                    del self.controller_info[robot_ip]
        
        return running
    
    def stop_all_controllers(self) -> int:
        """
        Stop all running controllers.
        
        Returns:
            Number of controllers stopped
        """
        count = 0
        for robot_ip in list(self.controllers.keys()):
            if self.stop_controller(robot_ip):
                count += 1
        return count
    
    def cleanup(self):
        """Clean up all controllers."""
        self.stop_all_controllers()

