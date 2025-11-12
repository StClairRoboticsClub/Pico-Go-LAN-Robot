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

# Portable path handling
if getattr(sys, 'frozen', False):
    # Running as PyInstaller executable
    APP_DIR = Path(sys.executable).parent
else:
    # Running as script
    APP_DIR = Path(__file__).parent


class ControllerManager:
    """Manages controller subprocess lifecycle."""
    
    def __init__(self):
        """Initialize controller manager."""
        self.controllers: Dict[str, subprocess.Popen] = {}
        self.controller_info: Dict[str, Dict] = {}
        self.controller_scripts = {
            "xbox": "controller_xbox.py",
            "calibrate": "calibrate.py"
        }
    
    def _get_controller_path(self, controller_type: str) -> Optional[Path]:
        """Get path to controller script."""
        script_name = self.controller_scripts.get(controller_type)
        if not script_name:
            return None
        
        # Portable path handling - works whether running as script or executable
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            # Scripts are bundled in controller directory
            app_dir = Path(sys.executable).parent
            script_path = app_dir / "controller" / script_name
            if script_path.exists():
                return script_path
            # Fallback: check same directory as executable
            script_path = app_dir / script_name
            if script_path.exists():
                return script_path
        else:
            # Running as script - scripts are in same directory (controller/)
            controller_dir = Path(__file__).parent
            script_path = controller_dir / script_name
            if script_path.exists():
                return script_path
        return None
    
    def launch_controller(self, robot_ip: str, robot_id: Optional[str] = None, 
                         controller_type: str = "xbox", joystick_index: int = 0) -> bool:
        """
        Launch a controller subprocess for a robot.
        
        Args:
            robot_ip: Robot IP address
            robot_id: Optional robot ID
            controller_type: Type of controller ("xbox" or "calibrate")
            joystick_index: Index of the joystick to use (0-7). Defaults to 0.
        
        Returns:
            True if launched successfully
        """
        if robot_ip in self.controllers:
            # Controller already running
            return False
        
        script_path = self._get_controller_path(controller_type)
        if not script_path:
            return False
        
        try:
            # Launch controller subprocess
            # Priority: 1) Bundled executable, 2) Python script, 3) System Python
            if getattr(sys, 'frozen', False):
                # Running as bundled executable - look for bundled controller executables
                # Map script names to executable names
                script_name = script_path.name
                exe_names = {
                    "controller_xbox.py": "RobotController",
                    "calibrate.py": "RobotCalibration"
                }
                exe_base = exe_names.get(script_name, script_path.stem)
                if sys.platform == "win32":
                    exe_name = f"{exe_base}.exe"
                else:
                    exe_name = exe_base
                
                # Check in same directory as master GUI executable
                bundled_exe = APP_DIR / exe_name
                if bundled_exe.exists():
                    # Pass joystick index as second argument (only for xbox controller)
                    if controller_type == "xbox":
                        process = subprocess.Popen(
                            [str(bundled_exe), robot_ip, str(joystick_index)],
                            cwd=str(APP_DIR),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                    else:
                        process = subprocess.Popen(
                            [str(bundled_exe), robot_ip],
                            cwd=str(APP_DIR),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                else:
                    # Fall back to Python script (if available)
                    if script_path.exists():
                        # Pass joystick index as second argument (only for xbox controller)
                        if controller_type == "xbox":
                            process = subprocess.Popen(
                                [sys.executable, str(script_path), robot_ip, str(joystick_index)],
                                cwd=str(APP_DIR),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                        else:
                            process = subprocess.Popen(
                                [sys.executable, str(script_path), robot_ip],
                                cwd=str(APP_DIR),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                    else:
                        raise FileNotFoundError(f"Could not find {exe_name} or {script_name}")
            else:
                # Running as script - use Python
                # Pass joystick index as second argument (only for xbox controller)
                if controller_type == "xbox":
                    process = subprocess.Popen(
                        [sys.executable, str(script_path), robot_ip, str(joystick_index)],
                        cwd=str(script_path.parent),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                else:
                    process = subprocess.Popen(
                        [sys.executable, str(script_path), robot_ip],
                        cwd=str(script_path.parent),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
            
            self.controllers[robot_ip] = process
            self.controller_info[robot_ip] = {
                "type": controller_type,
                "robot_id": robot_id,
                "joystick_index": joystick_index,
                "started": datetime.now().isoformat()
            }
            
            return True
        except Exception as e:
            print(f"Error launching controller: {e}")
            return False
    
    def stop_controller(self, robot_ip: str):
        """Stop a controller subprocess."""
        if robot_ip in self.controllers:
            process = self.controllers[robot_ip]
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass
            del self.controllers[robot_ip]
            if robot_ip in self.controller_info:
                del self.controller_info[robot_ip]
    
    def is_controller_running(self, robot_ip: str) -> bool:
        """Check if controller is running for a robot."""
        if robot_ip not in self.controllers:
            return False
        
        process = self.controllers[robot_ip]
        return process.poll() is None
    
    def get_all_running_controllers(self) -> List[str]:
        """Get list of all running controller IPs."""
        running = []
        for ip, process in list(self.controllers.items()):
            if process.poll() is None:
                running.append(ip)
            else:
                # Clean up dead processes
                del self.controllers[ip]
                if ip in self.controller_info:
                    del self.controller_info[ip]
        return running
    
    def cleanup(self):
        """Stop all controllers."""
        for robot_ip in list(self.controllers.keys()):
            self.stop_controller(robot_ip)
