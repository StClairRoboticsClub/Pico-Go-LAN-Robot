#!/usr/bin/env python3
"""
Robot Controller Master GUI
============================
Master application for managing multiple robot controllers.
THIS IS THE ONLY ENTRY POINT - Everything runs through this GUI!

Do not run controller_xbox.py or calibrate.py directly.
Always launch this Master GUI and use it to launch controllers and calibration tools.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

import sys
import os
import threading
import time
import socket
import json
from pathlib import Path
from typing import Dict, List, Optional
import tkinter as tk
from tkinter import messagebox, filedialog

import customtkinter as ctk

# Import pygame for gamepad detection (only for detection, not full init)
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# ============================================================================
# Portable Path Handling
# ============================================================================
# Get the directory where this script/executable is located
# This works whether running as script or as PyInstaller executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable (PyInstaller)
    BASE_DIR = Path(sys._MEIPASS)  # PyInstaller temp directory (bundled files)
    APP_DIR = Path(sys.executable).parent  # Directory where .exe is located
    # Add both locations to path
    sys.path.insert(0, str(BASE_DIR))
    sys.path.insert(0, str(APP_DIR))
else:
    # Running as script
    BASE_DIR = Path(__file__).parent
    APP_DIR = BASE_DIR
    sys.path.insert(0, str(BASE_DIR))

# Import our modules from controller directory
# All modules are now in the same directory as robot_master_gui.py
try:
    from robot_config import RobotConfig
    from controller_manager import ControllerManager
    from controller_xbox import (
        discover_robots_on_network,
        test_robot_connection,
        query_robot_directly,
        ROBOT_PORT
    )
except ImportError as e:
    # If running as executable, try importing from bundled location
    if getattr(sys, 'frozen', False):
        # Try bundled controller directory
        bundled_controller = BASE_DIR / "controller"
        if bundled_controller.exists():
            sys.path.insert(0, str(bundled_controller))
            from robot_config import RobotConfig
            from controller_manager import ControllerManager
            from controller_xbox import (
                discover_robots_on_network,
                test_robot_connection,
                query_robot_directly,
                ROBOT_PORT
            )
        else:
            print(f"Error: Could not find controller modules: {e}")
            sys.exit(1)
    else:
        print(f"Error: Could not import modules: {e}")
        sys.exit(1)

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RobotMasterGUI:
    """Master GUI application for managing robot controllers."""
    
    def __init__(self):
        """Initialize the master GUI application."""
        # Set working directory to app directory for portable operation
        os.chdir(str(APP_DIR))
        
        self.config = RobotConfig()
        self.controller_manager = ControllerManager()
        
        # Track discovered robots
        self.discovered_robots: Dict[str, Dict] = {}
        self.known_robot_ips: set = set()
        
        # Track gamepad assignments per robot
        # Load from config first
        self.robot_gamepad_assignments: Dict[str, int] = self.config.get_gamepad_assignments()
        self.available_gamepads = 0
        self.gamepad_names: Dict[int, str] = {}  # joystick_index -> gamepad name
        
        # Initialize pygame for gamepad detection (minimal init)
        if PYGAME_AVAILABLE:
            try:
                # Initialize pygame if not already initialized
                if not pygame.get_init():
                    pygame.init()
                pygame.joystick.init()
                # Small delay to allow joystick subsystem to initialize
                import time
                time.sleep(0.1)
                self._update_gamepad_list()
            except Exception as e:
                print(f"Warning: Could not initialize pygame for gamepad detection: {e}")
                self.available_gamepads = 0
                self.gamepad_names = {}
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Robot Controller Master")
        self.root.geometry("1000x700")
        
        # Setup UI
        self._setup_menu()
        self._setup_ui()
        
        # Start background tasks
        self.running = True
        self._start_background_tasks()
        
        # Auto-scan on startup
        self.root.after(500, self._auto_scan_startup)
        
        # Update gamepad list periodically
        self.root.after(2000, self._periodic_gamepad_update)
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add Robot", command=self._add_robot_dialog)
        edit_menu.add_command(label="Remove Robot", command=self._remove_robot)
        edit_menu.add_command(label="Refresh Discovery", command=self._scan_robots)
        edit_menu.add_separator()
        edit_menu.add_command(label="Gamepad Assignments", command=self._show_gamepad_assignments)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Network Panel", command=lambda: None)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _setup_ui(self):
        """Setup main UI components."""
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top info panel (network and gamepads)
        top_info_frame = ctk.CTkFrame(main_frame)
        top_info_frame.pack(fill="x", padx=10, pady=10)
        
        # Network info
        network_info = self.config.get_network_config()
        ctk.CTkLabel(top_info_frame, text=f"Network: {network_info.get('ssid', 'Unknown')}", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=5)
        
        # Gamepad info
        self.gamepad_info_label = ctk.CTkLabel(top_info_frame, text="Gamepads: 0 detected", 
                                             font=ctk.CTkFont(size=12))
        self.gamepad_info_label.pack(side="right", padx=10, pady=5)
        
        # Refresh gamepad button
        ctk.CTkButton(top_info_frame, text="Refresh Gamepads", 
                     command=self._update_gamepad_list, width=120).pack(side="right", padx=5)
        
        # Robot list
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(list_frame, text="Discovered Robots", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)
        
        # Scrollable robot list
        self.robot_listbox = tk.Listbox(list_frame, height=15, font=("Arial", 12))
        self.robot_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.robot_listbox.bind("<<ListboxSelect>>", self._on_robot_select)
        
        # Control buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(button_frame, text="Scan for Robots", 
                     command=self._scan_robots).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Launch Controller", 
                     command=self._launch_controller_with_gamepad).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Launch Calibration", 
                     command=self._launch_calibration).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Add Robot", 
                     command=self._add_robot_dialog).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Gamepad Assignments", 
                     command=self._show_gamepad_assignments).pack(side="left", padx=5)
    
    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        def monitor_controllers():
            while self.running:
                time.sleep(2)
                # Clean up dead processes
                self.controller_manager.get_all_running_controllers()
        
        thread = threading.Thread(target=monitor_controllers, daemon=True)
        thread.start()
    
    def _auto_scan_startup(self):
        """Auto-scan for robots on startup."""
        self._scan_robots()
    
    def _periodic_gamepad_update(self):
        """Periodically update gamepad list."""
        if self.running:
            self._update_gamepad_list()
            # Update every 5 seconds
            self.root.after(5000, self._periodic_gamepad_update)
    
    def _scan_robots(self):
        """Scan network for robots."""
        self.robot_listbox.delete(0, tk.END)
        self.robot_listbox.insert(0, "Scanning for robots...")
        self.root.update()
        
        # Increase timeout for better reliability (longer timeout for initial scan)
        # Enable debug mode to help diagnose network issues
        print("\n=== Robot Discovery Debug ===")
        robots = discover_robots_on_network(timeout=5.0, debug=True)
        print("=== End Discovery Debug ===\n")
        self.discovered_robots = {robot['ip']: robot for robot in robots}
        
        # If broadcast discovery failed, try direct queries to saved robots
        if not robots:
            saved_robots = self.config.get_robots()
            if saved_robots:
                print("\n=== Trying Direct Queries to Saved Robots ===")
                for saved_robot in saved_robots:
                    ip = saved_robot.get('ip')
                    if ip and ip not in self.discovered_robots:
                        robot_info = query_robot_directly(ip, timeout=2.0, debug=True)
                        if robot_info:
                            robots.append(robot_info)
                            self.discovered_robots[robot_info['ip']] = robot_info
                print("=== End Direct Queries ===\n")
        
        # Update robot list display
        self._update_robot_list_display()
        
        # Save discovered robots to config
        for robot in robots:
            ip = robot.get('ip')
            hostname = robot.get('hostname', 'unknown')
            robot_id = robot.get('robot_id')
            if ip:
                self.config.add_robot(ip, hostname, robot_id)
    
    def _update_robot_list_display(self):
        """Update the robot listbox display with current robots and gamepad assignments."""
        self.robot_listbox.delete(0, tk.END)
        
        robots = list(self.discovered_robots.values())
        
        if not robots:
            self.robot_listbox.insert(0, "No robots found. Troubleshooting:")
            self.robot_listbox.insert(1, "  ✓ Robots are powered on")
            self.robot_listbox.insert(2, "  ✓ Same WiFi network as computer")
            self.robot_listbox.insert(3, "  ✓ Firewall allows UDP port 8765 (in/out)")
            self.robot_listbox.insert(4, "  ✓ UDP broadcasts enabled on network")
            self.robot_listbox.insert(5, "")
            self.robot_listbox.insert(6, "  → Try 'Add Robot' to enter IP manually")
            self.robot_listbox.insert(7, "  → Check robot's LCD screen for IP address")
        else:
            for robot in robots:
                robot_id = robot.get('robot_id', '?')
                hostname = robot.get('hostname', 'unknown')
                ip = robot['ip']
                
                # Show gamepad assignment if exists (session-based)
                gamepad_info = ""
                if ip in self.robot_gamepad_assignments:
                    gamepad_idx = self.robot_gamepad_assignments[ip]
                    if gamepad_idx == -1:
                        gamepad_info = " [Keyboard]"
                    elif gamepad_idx == 0 and self.available_gamepads == 0:
                        gamepad_info = " [Keyboard]"
                    elif gamepad_idx == 0:
                        # Check if it's actually a gamepad or keyboard
                        if 0 in self.gamepad_names:
                            gamepad_name = self.gamepad_names.get(0, "Gamepad 0")
                            gamepad_info = f" [{gamepad_name}]"
                        else:
                            gamepad_info = " [Keyboard]"
                    else:
                        gamepad_name = self.gamepad_names.get(gamepad_idx, f"Gamepad {gamepad_idx}")
                        gamepad_info = f" [{gamepad_name}]"
                
                display_text = f"Robot #{robot_id} ({hostname}) - {ip}{gamepad_info}"
                self.robot_listbox.insert(tk.END, display_text)
        
        # Also show saved robots (not discovered but in config)
        saved_robots = self.config.get_robots()
        for robot in saved_robots:
            ip = robot.get('ip')
            if ip and ip not in self.discovered_robots:
                name = robot.get('name', 'Unknown')
                # Show gamepad assignment for saved robots too
                gamepad_info = ""
                if ip in self.robot_gamepad_assignments:
                    gamepad_idx = self.robot_gamepad_assignments[ip]
                    if gamepad_idx == -1:
                        gamepad_info = " [Keyboard]"
                    elif gamepad_idx > 0:
                        gamepad_name = self.gamepad_names.get(gamepad_idx, f"Gamepad {gamepad_idx}")
                        gamepad_info = f" [{gamepad_name}]"
                    else:
                        gamepad_info = " [Keyboard]"
                
                display_text = f"[Saved] {name} - {ip}{gamepad_info}"
                self.robot_listbox.insert(tk.END, display_text)
    
    def _on_robot_select(self, event):
        """Handle robot selection."""
        selection = self.robot_listbox.curselection()
        if selection:
            # Robot selected - enable launch buttons
            pass
    
    def _get_selected_robot_ip(self) -> Optional[str]:
        """Get IP address of selected robot."""
        selection = self.robot_listbox.curselection()
        if not selection:
            return None
        
        selected_text = self.robot_listbox.get(selection[0])
        
        # Extract IP from display text
        if " - " in selected_text:
            ip = selected_text.split(" - ")[-1]
            return ip.strip()
        return None
    
    def _update_gamepad_list(self):
        """Update list of available gamepads."""
        if not PYGAME_AVAILABLE:
            self.available_gamepads = 0
            self.gamepad_names = {}
            if hasattr(self, 'gamepad_info_label'):
                self.gamepad_info_label.configure(text="Gamepads: pygame not available")
            return
        
        try:
            # Ensure pygame is initialized
            if not pygame.get_init():
                pygame.init()
            
            # Reinitialize joystick subsystem
            pygame.joystick.quit()
            pygame.joystick.init()
            
            # Small delay to allow joystick subsystem to initialize
            import time
            time.sleep(0.1)
            
            count = pygame.joystick.get_count()
            self.available_gamepads = count
            self.gamepad_names = {}
            
            for i in range(count):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                    name = joystick.get_name()
                    self.gamepad_names[i] = name
                except Exception as e:
                    # If we can't get the name, use a default
                    self.gamepad_names[i] = f"Gamepad {i}"
            
            if hasattr(self, 'gamepad_info_label'):
                if count == 0:
                    self.gamepad_info_label.configure(text="Gamepads: 0 detected")
                else:
                    self.gamepad_info_label.configure(text=f"Gamepads: {count} detected")
        except Exception as e:
            self.available_gamepads = 0
            self.gamepad_names = {}
            if hasattr(self, 'gamepad_info_label'):
                self.gamepad_info_label.configure(text=f"Gamepads: Error ({str(e)[:20]})")
            # Print error for debugging
            print(f"Error updating gamepad list: {e}")
            import traceback
            traceback.print_exc()
    
    def _launch_controller_with_gamepad(self):
        """Launch controller for selected robot with gamepad selection."""
        robot_ip = self._get_selected_robot_ip()
        if not robot_ip:
            messagebox.showwarning("No Selection", "Please select a robot first.")
            return
        
        if self.controller_manager.is_controller_running(robot_ip):
            messagebox.showinfo("Already Running", f"Controller already running for {robot_ip}")
            return
        
        # Always show gamepad selection dialog
        self._update_gamepad_list()
        joystick_index = self._select_gamepad_dialog()
        
        if joystick_index is None:
            return  # User cancelled
        
        # Check if selected gamepad is already assigned to another robot
        if joystick_index > 0:  # Only check for actual gamepads, not keyboard
            for ip, assigned_idx in list(self.robot_gamepad_assignments.items()):
                if ip != robot_ip and assigned_idx == joystick_index:
                    # Remove old assignment (reassign to this robot)
                    del self.robot_gamepad_assignments[ip]
                    self.config.remove_gamepad_assignment(ip)
        
        # Store assignment in session memory (for real-time display)
        # All assignments (including keyboard) are session-based
        self.robot_gamepad_assignments[robot_ip] = joystick_index
        
        # Save to config only for real gamepads (not keyboard) for persistence
        if joystick_index > 0:
            self.config.set_gamepad_assignment(robot_ip, joystick_index)
        else:
            # Keyboard - don't save to config, but keep in session memory
            # Remove from config if it was previously saved
            if robot_ip in self.config.get_gamepad_assignments():
                self.config.remove_gamepad_assignment(robot_ip)
        
        # Update robot list display immediately to show assignment
        self._update_robot_list_display()
        
        # Get robot ID if available
        robot_id = None
        if robot_ip in self.discovered_robots:
            robot_id = self.discovered_robots[robot_ip].get('robot_id')
        
        # Launch controller with assigned gamepad
        if self.controller_manager.launch_controller(robot_ip, robot_id, "xbox", joystick_index):
            # Determine input method name
            if joystick_index == -1:
                input_method = "Keyboard Input"
            elif joystick_index == 0 and self.available_gamepads == 0:
                input_method = "Keyboard Input"
            elif joystick_index == 0:
                # Check if gamepad 0 exists
                if 0 in self.gamepad_names:
                    input_method = self.gamepad_names.get(0, "Gamepad 0")
                else:
                    input_method = "Keyboard Input"
            else:
                input_method = self.gamepad_names.get(joystick_index, f"Gamepad {joystick_index}")
            
            messagebox.showinfo("Success", f"Controller launched for {robot_ip}\nUsing: {input_method}")
        else:
            messagebox.showerror("Error", f"Failed to launch controller for {robot_ip}")
    
    def _select_gamepad_dialog(self) -> Optional[int]:
        """Show dialog to select a gamepad."""
        # Always refresh gamepad list before showing dialog
        self._update_gamepad_list()
        
        if self.available_gamepads == 0:
            messagebox.showwarning("No Gamepads", 
                                 "No gamepads detected.\n\n"
                                 "Please:\n"
                                 "1. Connect a gamepad/joystick\n"
                                 "2. Click 'Refresh Gamepads' button\n"
                                 "3. Try again\n\n"
                                 "Controller will use keyboard input if no gamepad is available.")
            return 0  # Default to 0, will fall back to keyboard
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Select Gamepad")
        dialog.geometry("500x450")  # Increased size to show all buttons
        dialog.transient(self.root)
        
        # Ensure window is visible before grabbing
        dialog.update_idletasks()
        dialog.lift()
        dialog.focus_force()
        
        # Try to grab focus, but don't fail if it doesn't work
        try:
            dialog.grab_set()
        except:
            pass  # Some systems don't support grab_set, continue anyway
        
        result = [None]  # Use list to allow modification in nested function
        
        ctk.CTkLabel(dialog, text="Select input method for this robot:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        # Gamepad list
        listbox_frame = ctk.CTkFrame(dialog)
        listbox_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        gamepad_listbox = tk.Listbox(listbox_frame, height=10, font=("Arial", 11))
        gamepad_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Always add "Use Keyboard" option first
        gamepad_listbox.insert(0, "Keyboard Input [No gamepad]")
        
        # Populate listbox with available gamepads
        for i in range(self.available_gamepads):
            name = self.gamepad_names.get(i, f"Gamepad {i}")
            # Check if already assigned
            assigned_to = None
            for ip, idx in self.robot_gamepad_assignments.items():
                if idx == i:
                    assigned_to = ip
                    break
            
            if assigned_to:
                display_text = f"Gamepad {i}: {name} [Assigned to {assigned_to}]"
            else:
                display_text = f"Gamepad {i}: {name} [Available]"
            
            gamepad_listbox.insert(tk.END, display_text)
        
        # Select first item (keyboard) by default
        gamepad_listbox.selection_set(0)
        gamepad_listbox.see(0)
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        def select_gamepad():
            selection = gamepad_listbox.curselection()
            if selection:
                selected_idx = selection[0]
                # If first item (index 0) is selected, it's keyboard
                # Use -1 as a special value to explicitly request keyboard
                if selected_idx == 0:
                    result[0] = -1  # Special value: use keyboard explicitly
                    dialog.destroy()
                else:
                    # Gamepad index is selection - 1 (because keyboard is at index 0)
                    gamepad_idx = selected_idx - 1
                    
                    # Check if this gamepad is already assigned to another robot
                    assigned_to = None
                    for ip, idx in self.robot_gamepad_assignments.items():
                        if idx == gamepad_idx:
                            assigned_to = ip
                            break
                    
                    if assigned_to:
                        # Ask user if they want to reassign
                        response = messagebox.askyesno(
                            "Gamepad Already Assigned",
                            f"Gamepad {gamepad_idx} is already assigned to {assigned_to}.\n\n"
                            f"Do you want to reassign it to this robot?\n"
                            f"(The previous assignment will be removed.)"
                        )
                        if response:
                            # Remove old assignment
                            del self.robot_gamepad_assignments[assigned_to]
                            self.config.remove_gamepad_assignment(assigned_to)
                            result[0] = gamepad_idx
                            dialog.destroy()
                        # If user says no, don't close dialog - let them select something else
                    else:
                        # Gamepad is available
                        result[0] = gamepad_idx
                        dialog.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select an input method.")
        
        def cancel():
            dialog.destroy()
        
        ctk.CTkButton(button_frame, text="Select", command=select_gamepad).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=cancel).pack(side="left", padx=5)
        
        dialog.wait_window()
        return result[0]
    
    def _show_gamepad_assignments(self):
        """Show gamepad assignment management dialog."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Gamepad Assignments")
        dialog.geometry("750x600")  # Increased size to show all UI elements
        dialog.transient(self.root)
        
        # Ensure window is visible before grabbing
        dialog.update_idletasks()
        dialog.lift()
        dialog.focus_force()
        
        # Try to grab focus, but don't fail if it doesn't work
        try:
            dialog.grab_set()
        except:
            pass  # Some systems don't support grab_set, continue anyway
        
        # Update gamepad list
        self._update_gamepad_list()
        
        # Header
        header_frame = ctk.CTkFrame(dialog)
        header_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(header_frame, text="Manage Gamepad Assignments", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        ctk.CTkLabel(header_frame, text="Assign specific gamepads to specific robots", 
                    font=ctk.CTkFont(size=12)).pack()
        
        # Main content area with scrollable frame
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Get all robots (discovered + saved)
        all_robots = {}
        for ip, robot in self.discovered_robots.items():
            all_robots[ip] = robot
        saved_robots = self.config.get_robots()
        for robot in saved_robots:
            ip = robot.get('ip')
            if ip and ip not in all_robots:
                all_robots[ip] = robot
        
        # Create assignment table
        table_frame = ctk.CTkFrame(content_frame)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Column headers
        header_row = ctk.CTkFrame(table_frame)
        header_row.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(header_row, text="Robot", width=200, 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Current Gamepad", width=250, 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(header_row, text="Action", width=150, 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=5)
        
        # Robot rows
        robot_rows = {}
        for ip, robot in sorted(all_robots.items(), key=lambda x: x[1].get('robot_id', 999)):
            row_frame = ctk.CTkFrame(table_frame)
            row_frame.pack(fill="x", padx=5, pady=3)
            
            # Robot info
            robot_id = robot.get('robot_id', '?')
            hostname = robot.get('hostname', robot.get('name', 'Unknown'))
            robot_label = f"Robot #{robot_id} ({hostname}) - {ip}"
            ctk.CTkLabel(row_frame, text=robot_label, width=200, anchor="w").pack(side="left", padx=5)
            
            # Current assignment
            current_idx = self.robot_gamepad_assignments.get(ip)
            if current_idx is not None:
                gamepad_name = self.gamepad_names.get(current_idx, f"Gamepad {current_idx}")
                assignment_text = f"Gamepad {current_idx}: {gamepad_name}"
            else:
                assignment_text = "Not assigned"
            
            assignment_label = ctk.CTkLabel(row_frame, text=assignment_text, width=250, anchor="w")
            assignment_label.pack(side="left", padx=5)
            
            # Action buttons
            button_frame = ctk.CTkFrame(row_frame)
            button_frame.pack(side="left", padx=5)
            
            def make_assign_callback(robot_ip):
                def assign():
                    idx = self._select_gamepad_dialog()
                    if idx is not None:
                        # Check if this gamepad is already assigned to another robot
                        # (keyboard/index 0 can be assigned to multiple robots)
                        if idx > 0:  # Only check for actual gamepads, not keyboard
                            assigned_to = None
                            for ip, assigned_idx in self.robot_gamepad_assignments.items():
                                if ip != robot_ip and assigned_idx == idx:
                                    assigned_to = ip
                                    break
                            
                            if assigned_to:
                                # Ask user if they want to reassign
                                response = messagebox.askyesno(
                                    "Gamepad Already Assigned",
                                    f"Gamepad {idx} is already assigned to {assigned_to}.\n\n"
                                    f"Do you want to reassign it to Robot #{robot.get('robot_id', '?')}?\n"
                                    f"(The previous assignment will be removed.)"
                                )
                                if not response:
                                    return  # User cancelled
                                
                                # Remove old assignment
                                del self.robot_gamepad_assignments[assigned_to]
                                self.config.remove_gamepad_assignment(assigned_to)
                        
                        # Assign to this robot
                        self.robot_gamepad_assignments[robot_ip] = idx
                        self.config.set_gamepad_assignment(robot_ip, idx)
                        # Update display
                        if idx == 0:
                            assignment_label.configure(text="Keyboard Input")
                        else:
                            gamepad_name = self.gamepad_names.get(idx, f"Gamepad {idx}")
                            assignment_label.configure(text=f"Gamepad {idx}: {gamepad_name}")
                        # Refresh main robot list
                        self._scan_robots()
                return assign
            
            def make_remove_callback(robot_ip, label):
                def remove():
                    if robot_ip in self.robot_gamepad_assignments:
                        del self.robot_gamepad_assignments[robot_ip]
                        self.config.remove_gamepad_assignment(robot_ip)
                        label.configure(text="Not assigned")
                        # Refresh main robot list
                        self._scan_robots()
                return remove
            
            assign_btn = ctk.CTkButton(button_frame, text="Assign", width=70,
                                      command=make_assign_callback(ip))
            assign_btn.pack(side="left", padx=2)
            
            if current_idx is not None:
                remove_btn = ctk.CTkButton(button_frame, text="Remove", width=70,
                                         command=make_remove_callback(ip, assignment_label))
                remove_btn.pack(side="left", padx=2)
            
            robot_rows[ip] = {
                'frame': row_frame,
                'assignment_label': assignment_label
            }
        
        # Available gamepads info
        info_frame = ctk.CTkFrame(dialog)
        info_frame.pack(fill="x", padx=20, pady=10)
        
        if self.available_gamepads == 0:
            info_text = "No gamepads detected. Connect gamepads and click 'Refresh Gamepads'."
        else:
            used_indices = set(self.robot_gamepad_assignments.values())
            available = [i for i in range(self.available_gamepads) if i not in used_indices]
            if available:
                info_text = f"Available gamepads: {', '.join([f'Gamepad {i}' for i in available])}"
            else:
                info_text = "All gamepads are assigned."
        
        ctk.CTkLabel(info_frame, text=info_text, font=ctk.CTkFont(size=11)).pack(pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        def refresh_gamepads():
            self._update_gamepad_list()
            dialog.destroy()
            self._show_gamepad_assignments()  # Reopen with updated list
        
        ctk.CTkButton(button_frame, text="Refresh Gamepads", command=refresh_gamepads).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Close", command=dialog.destroy).pack(side="right", padx=5)
    
    def _launch_controller(self):
        """Launch controller for selected robot (legacy method, redirects to new method)."""
        self._launch_controller_with_gamepad()
    
    def _launch_calibration(self):
        """Launch calibration tool for selected robot."""
        robot_ip = self._get_selected_robot_ip()
        if not robot_ip:
            messagebox.showwarning("No Selection", "Please select a robot first.")
            return
        
        if self.controller_manager.is_controller_running(robot_ip):
            messagebox.showinfo("Already Running", f"Controller already running for {robot_ip}")
            return
        
        robot_id = None
        if robot_ip in self.discovered_robots:
            robot_id = self.discovered_robots[robot_ip].get('robot_id')
        
        if self.controller_manager.launch_controller(robot_ip, robot_id, "calibrate"):
            messagebox.showinfo("Success", f"Calibration tool launched for {robot_ip}")
        else:
            messagebox.showerror("Error", f"Failed to launch calibration for {robot_ip}")
    
    def _add_robot_dialog(self):
        """Show dialog to add robot manually."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Robot")
        dialog.geometry("400x200")
        
        ctk.CTkLabel(dialog, text="Robot IP Address:").pack(pady=10)
        ip_entry = ctk.CTkEntry(dialog, width=200)
        ip_entry.pack(pady=5)
        
        def add_robot():
            ip = ip_entry.get().strip()
            if ip:
                if test_robot_connection(ip):
                    self.config.add_robot(ip)
                    self._scan_robots()
                    dialog.destroy()
                    messagebox.showinfo("Success", f"Robot {ip} added successfully")
                else:
                    messagebox.showerror("Error", f"Could not connect to {ip}")
            else:
                messagebox.showwarning("Invalid", "Please enter an IP address")
        
        ctk.CTkButton(dialog, text="Add", command=add_robot).pack(pady=10)
        ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def _remove_robot(self):
        """Remove selected robot."""
        robot_ip = self._get_selected_robot_ip()
        if not robot_ip:
            messagebox.showwarning("No Selection", "Please select a robot first.")
            return
        
        if messagebox.askyesno("Confirm", f"Remove robot {robot_ip}?"):
            self.config.remove_robot(robot_ip)
            self._scan_robots()
    
    def _show_settings(self):
        """Show settings dialog."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("400x300")
        
        network_info = self.config.get_network_config()
        
        ctk.CTkLabel(dialog, text="Network Configuration", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(dialog, text="SSID:").pack(pady=5)
        ssid_entry = ctk.CTkEntry(dialog, width=200)
        ssid_entry.insert(0, network_info.get('ssid', ''))
        ssid_entry.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Password:").pack(pady=5)
        password_entry = ctk.CTkEntry(dialog, width=200, show="*")
        password_entry.insert(0, network_info.get('password', ''))
        password_entry.pack(pady=5)
        
        def save_settings():
            self.config.set_network_config(ssid_entry.get(), password_entry.get())
            dialog.destroy()
            messagebox.showinfo("Success", "Settings saved")
        
        ctk.CTkButton(dialog, text="Save", command=save_settings).pack(pady=10)
        ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About", 
                           "Pico-Go LAN Robot Controller Master\n\n"
                           "Manage and control multiple robots from one interface.\n\n"
                           "St. Clair College Robotics Club")
    
    def _on_closing(self):
        """Handle window closing."""
        if messagebox.askokcancel("Quit", "Stop all controllers and exit?"):
            self.controller_manager.cleanup()
            self.running = False
            self.root.destroy()
    
    def run(self):
        """Run the GUI application."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()


def main():
    """Main entry point."""
    app = RobotMasterGUI()
    app.run()


if __name__ == "__main__":
    main()
