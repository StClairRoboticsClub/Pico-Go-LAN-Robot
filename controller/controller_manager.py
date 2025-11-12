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
                    # Pass joystick index as second argument, robot_id as third (only for xbox controller)
                    if controller_type == "xbox":
                        if robot_id is not None:
                            process = subprocess.Popen(
                                [str(bundled_exe), robot_ip, str(joystick_index), str(robot_id)],
                                cwd=str(APP_DIR),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                        else:
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
                        # Ensure we use the correct Python interpreter
                        python_exe = sys.executable
                        if not python_exe or not os.path.exists(python_exe):
                            python_exe = "python3"
                        
                        # Use absolute path for script to avoid path resolution issues
                        script_abs_path = os.path.abspath(str(script_path))
                        
                        # Pass joystick index as second argument, robot_id as third (only for xbox controller)
                        if controller_type == "xbox":
                            if robot_id is not None:
                                cmd = [python_exe, script_abs_path, robot_ip, str(joystick_index), str(robot_id)]
                            else:
                                cmd = [python_exe, script_abs_path, robot_ip, str(joystick_index)]
                        else:
                            cmd = [python_exe, script_abs_path, robot_ip]
                        
                        # Launch with proper environment - don't capture output so window can display
                        creation_flags = 0
                        if platform.system() == "Windows":
                            import subprocess as sp
                            creation_flags = sp.CREATE_NEW_CONSOLE
                        
                        process = subprocess.Popen(
                            cmd,
                            cwd=str(APP_DIR),
                            stdout=None,  # Don't capture - let it display in its own window
                            stderr=None,  # Don't capture - let errors show
                            stdin=None,   # Don't capture stdin
                            creationflags=creation_flags if platform.system() == "Windows" else 0,
                            start_new_session=True if platform.system() != "Windows" else False
                        )
                    else:
                        raise FileNotFoundError(f"Could not find {exe_name} or {script_name}")
            else:
                # Running as script - use Python
                # Ensure we use the correct Python interpreter
                python_exe = sys.executable
                if not python_exe or not os.path.exists(python_exe):
                    # Fallback: try python3
                    python_exe = "python3"
                
                # Use absolute path for script to avoid path resolution issues
                script_abs_path = os.path.abspath(str(script_path))
                
                # Pass joystick index as second argument, robot_id as third (only for xbox controller)
                # -1 is valid for keyboard, 0-7 for gamepads
                if controller_type == "xbox":
                    if robot_id is not None:
                        cmd = [python_exe, script_abs_path, robot_ip, str(joystick_index), str(robot_id)]
                    else:
                        cmd = [python_exe, script_abs_path, robot_ip, str(joystick_index)]
                else:
                    cmd = [python_exe, script_abs_path, robot_ip]
                
                # Debug: print command for troubleshooting
                print(f"Launching controller: {' '.join(cmd)}")
                
                # Launch with proper environment - don't capture output so window can display
                # Use CREATE_NEW_CONSOLE on Windows, or detach on Linux
                creation_flags = 0
                if platform.system() == "Windows":
                    import subprocess as sp
                    creation_flags = sp.CREATE_NEW_CONSOLE
                
                # Prepare environment - ensure DISPLAY is set for GUI on Linux
                env = os.environ.copy()
                if platform.system() != "Windows":
                    # Ensure DISPLAY is set for GUI applications
                    if 'DISPLAY' not in env:
                        # Try to get DISPLAY from current process
                        display = os.environ.get('DISPLAY')
                        if display:
                            env['DISPLAY'] = display
                
                # For debugging: temporarily capture stderr to see errors
                # TODO: Remove stderr capture once issue is resolved
                process = subprocess.Popen(
                    cmd,
                    cwd=str(script_path.parent),
                    stdout=None,  # Don't capture - let it display in its own window
                    stderr=subprocess.PIPE,  # Temporarily capture to see errors
                    stdin=None,   # Don't capture stdin
                    env=env,  # Pass environment with DISPLAY
                    creationflags=creation_flags if platform.system() == "Windows" else 0,
                    start_new_session=True if platform.system() != "Windows" else False
                )
            
            # Give process a moment to start and check if it's still running
            import time
            time.sleep(0.2)  # Small delay to let process initialize
            
            # Verify process started successfully
            if process.poll() is not None:
                # Process already terminated (error)
                error_msg = f"Controller process exited immediately with code {process.returncode}"
                print(f"Error launching controller: {error_msg}")
                # Try to read stderr to see what went wrong
                try:
                    stderr_output = process.stderr.read().decode('utf-8', errors='ignore')
                    if stderr_output:
                        print(f"Controller stderr output:\n{stderr_output}")
                except:
                    pass
                return False
            
            self.controllers[robot_ip] = process
            self.controller_info[robot_ip] = {
                "type": controller_type,
                "robot_id": robot_id,
                "joystick_index": joystick_index,
                "started": datetime.now().isoformat()
            }
            
            return True
        except FileNotFoundError as e:
            print(f"Error launching controller: File not found - {e}")
            print(f"  Python executable: {sys.executable}")
            print(f"  Script path: {script_path}")
            return False
        except Exception as e:
            import traceback
            print(f"Error launching controller: {e}")
            traceback.print_exc()
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
