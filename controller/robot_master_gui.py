#!/usr/bin/env python3
"""
Robot Controller Master GUI
============================
Master application for managing multiple robot controllers.

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

# Import our modules
from robot_config import RobotConfig
from controller_manager import ControllerManager

# Import discovery functions from controller_xbox
# Add parent directory to path to import controller_xbox
controller_dir = Path(__file__).parent
sys.path.insert(0, str(controller_dir))

try:
    from controller_xbox import (
        discover_robots_on_network,
        test_robot_connection,
        ROBOT_PORT
    )
except ImportError as e:
    print(f"Warning: Could not import from controller_xbox: {e}")
    # Fallback functions if import fails
    def discover_robots_on_network(timeout: float = 1.5):
        return []
    
    def test_robot_connection(ip: str, timeout: float = 1.0):
        return False
    
    ROBOT_PORT = 8765

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RobotMasterGUI:
    """Main GUI application for robot controller management."""
    
    def __init__(self):
        """Initialize the master GUI application."""
        self.config = RobotConfig()
        self.controller_manager = ControllerManager()
        
        # Track discovered robots
        self.discovered_robots: Dict[str, Dict] = {}
        self.known_robot_ips: set = set()
        
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
    
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Settings", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Export Config", command=self._export_config)
        file_menu.add_command(label="Import Config", command=self._import_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add Robot", command=self._add_robot_dialog)
        edit_menu.add_command(label="Remove Robot", command=self._remove_robot_dialog)
        edit_menu.add_command(label="Edit Robot", command=self._edit_robot_dialog)
        edit_menu.add_separator()
        edit_menu.add_command(label="Refresh Discovery", command=self._scan_robots)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Network Panel", command=lambda: self._toggle_panel(self.network_frame, True))
        view_menu.add_command(label="Hide Network Panel", command=lambda: self._toggle_panel(self.network_frame, False))
        view_menu.add_separator()
        view_menu.add_command(label="Theme Settings", command=self._show_theme_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
    
    def _setup_ui(self):
        """Setup the main UI components."""
        # Main container
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel - Network and Robots
        left_panel = ctk.CTkFrame(main_container)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Network panel
        self.network_frame = ctk.CTkFrame(left_panel)
        self.network_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        network_label = ctk.CTkLabel(self.network_frame, text="Network Configuration", 
                                     font=ctk.CTkFont(size=16, weight="bold"))
        network_label.pack(pady=(10, 5))
        
        # SSID display
        ssid_frame = ctk.CTkFrame(self.network_frame)
        ssid_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(ssid_frame, text="SSID:").pack(side="left", padx=5)
        self.ssid_label = ctk.CTkLabel(ssid_frame, text="Not configured", anchor="w")
        self.ssid_label.pack(side="left", fill="x", expand=True, padx=5)
        
        # Password display
        password_frame = ctk.CTkFrame(self.network_frame)
        password_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(password_frame, text="Password:").pack(side="left", padx=5)
        self.password_label = ctk.CTkLabel(password_frame, text="••••••••", anchor="w")
        self.password_label.pack(side="left", fill="x", expand=True, padx=5)
        self.password_visible = False
        
        # Password reveal button
        self.password_button = ctk.CTkButton(password_frame, text="Show Password", 
                                             width=120, command=self._toggle_password)
        self.password_button.pack(side="right", padx=5)
        
        # Edit network button
        edit_network_btn = ctk.CTkButton(self.network_frame, text="Edit Network Config", 
                                         command=self._edit_network_dialog)
        edit_network_btn.pack(pady=10)
        
        # Update network display
        self._update_network_display()
        
        # Robots panel
        robots_label = ctk.CTkLabel(left_panel, text="Robots", 
                                    font=ctk.CTkFont(size=16, weight="bold"))
        robots_label.pack(pady=(10, 5))
        
        # Robot list with scrollbar
        list_frame = ctk.CTkFrame(left_panel)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.robot_listbox = tk.Listbox(list_frame, bg="#2b2b2b", fg="white", 
                                        selectbackground="#1f538d", font=("Arial", 11))
        self.robot_listbox.pack(side="left", fill="both", expand=True)
        self.robot_listbox.bind("<<ListboxSelect>>", self._on_robot_select)
        
        scrollbar = ctk.CTkScrollbar(list_frame, command=self.robot_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.robot_listbox.config(yscrollcommand=scrollbar.set)
        
        # Robot action buttons
        button_frame = ctk.CTkFrame(left_panel)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        scan_btn = ctk.CTkButton(button_frame, text="Scan for Robots", 
                                 command=self._scan_robots)
        scan_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        add_btn = ctk.CTkButton(button_frame, text="Add Robot", 
                                command=self._add_robot_dialog)
        add_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Right panel - Robot details and controller
        right_panel = ctk.CTkFrame(main_container)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Selected robot info
        info_label = ctk.CTkLabel(right_panel, text="Robot Information", 
                                 font=ctk.CTkFont(size=16, weight="bold"))
        info_label.pack(pady=(10, 5))
        
        self.robot_info_frame = ctk.CTkFrame(right_panel)
        self.robot_info_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.robot_info_text = ctk.CTkTextbox(self.robot_info_frame, height=200)
        self.robot_info_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.robot_info_text.insert("1.0", "Select a robot to view details")
        
        # Controller section
        controller_label = ctk.CTkLabel(right_panel, text="Controller", 
                                      font=ctk.CTkFont(size=16, weight="bold"))
        controller_label.pack(pady=(10, 5))
        
        controller_frame = ctk.CTkFrame(right_panel)
        controller_frame.pack(fill="x", padx=10, pady=5)
        
        # Controller type dropdown
        ctk.CTkLabel(controller_frame, text="Controller Type:").pack(pady=5)
        self.controller_type_var = ctk.StringVar(value="xbox")
        controller_dropdown = ctk.CTkOptionMenu(controller_frame, 
                                                values=["xbox", "gamepad", "keyboard"],
                                                variable=self.controller_type_var)
        controller_dropdown.pack(pady=5)
        
        # Launch/Stop button
        self.controller_button = ctk.CTkButton(controller_frame, text="Launch Controller", 
                                              command=self._launch_controller,
                                              state="disabled")
        self.controller_button.pack(pady=10)
        
        # Charging mode button
        self.charging_mode_button = ctk.CTkButton(controller_frame, text="Enable Charging Mode", 
                                                 command=self._toggle_charging_mode,
                                                 state="disabled",
                                                 fg_color=("gray75", "gray30"))
        self.charging_mode_button.pack(pady=5)
        
        # Track charging mode state per robot
        self.charging_mode_states: Dict[str, bool] = {}  # robot_ip -> bool
        
        # Status section
        status_label = ctk.CTkLabel(right_panel, text="Status", 
                                  font=ctk.CTkFont(size=16, weight="bold"))
        status_label.pack(pady=(10, 5))
        
        self.status_text = ctk.CTkTextbox(right_panel, height=100)
        self.status_text.pack(fill="x", padx=10, pady=5)
        self.status_text.insert("1.0", "Ready")
        
        # Active controllers count
        self.active_controllers_label = ctk.CTkLabel(right_panel, text="Active Controllers: 0")
        self.active_controllers_label.pack(pady=5)
    
    def _update_network_display(self):
        """Update network configuration display."""
        network = self.config.get_network_config()
        ssid = network.get("ssid", "")
        password = network.get("password", "")
        
        if ssid:
            self.ssid_label.configure(text=ssid)
        else:
            self.ssid_label.configure(text="Not configured")
        
        if not self.password_visible:
            if password:
                self.password_label.configure(text="••••••••")
            else:
                self.password_label.configure(text="Not set")
    
    def _toggle_password(self):
        """Toggle password visibility."""
        network = self.config.get_network_config()
        password = network.get("password", "")
        
        self.password_visible = not self.password_visible
        if self.password_visible:
            self.password_label.configure(text=password if password else "Not set")
            self.password_button.configure(text="Hide Password")
        else:
            self.password_label.configure(text="••••••••" if password else "Not set")
            self.password_button.configure(text="Show Password")
    
    def _edit_network_dialog(self):
        """Show dialog to edit network configuration."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Network Configuration")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.update_idletasks()  # Ensure window is ready
        dialog.grab_set()
        
        # SSID entry
        ctk.CTkLabel(dialog, text="SSID:").pack(pady=10)
        ssid_entry = ctk.CTkEntry(dialog, width=300)
        network = self.config.get_network_config()
        ssid_entry.insert(0, network.get("ssid", ""))
        ssid_entry.pack(pady=5)
        
        # Password entry
        ctk.CTkLabel(dialog, text="Password:").pack(pady=10)
        password_entry = ctk.CTkEntry(dialog, width=300, show="*")
        password_entry.insert(0, network.get("password", ""))
        password_entry.pack(pady=5)
        
        def save():
            ssid = ssid_entry.get().strip()
            password = password_entry.get().strip()
            if self.config.set_network_config(ssid, password):
                self._update_network_display()
                dialog.destroy()
                messagebox.showinfo("Success", "Network configuration saved successfully", parent=self.root)
            else:
                messagebox.showerror("Error", "Failed to save network configuration", parent=dialog)
        
        # Button frame
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save, width=100)
        save_btn.pack(side="left", padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy, width=100)
        cancel_btn.pack(side="left", padx=10)
        
        # Make Enter key save
        dialog.bind("<Return>", lambda e: save())
        ssid_entry.bind("<Return>", lambda e: password_entry.focus())
        password_entry.bind("<Return>", lambda e: save())
        
        # Focus on SSID entry
        ssid_entry.focus()
    
    def _scan_robots(self):
        """Scan network for robots."""
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", "Scanning for robots...")
        self.root.update()
        
        def scan_thread():
            robots = discover_robots_on_network(timeout=2.0)
            self.root.after(0, lambda: self._on_scan_complete(robots))
        
        threading.Thread(target=scan_thread, daemon=True).start()
    
    def _on_scan_complete(self, robots: List[Dict]):
        """Handle scan completion."""
        new_robots = []
        for robot in robots:
            robot_ip = robot.get("ip")
            if robot_ip:
                # Check if this is a new robot
                if robot_ip not in self.known_robot_ips:
                    new_robots.append(robot)
                    self.known_robot_ips.add(robot_ip)
                
                # Update discovered robots
                self.discovered_robots[robot_ip] = robot
                
                # Get profile name for display
                robot_id = robot.get("robot_id", "?")
                profile_name = self._get_profile_name(robot_id)
                
                # Add/update in config
                robot_data = {
                    "ip": robot_ip,
                    "robot_id": robot_id,
                    "hostname": robot.get("hostname", "unknown"),
                    "version": robot.get("version", "?"),
                    "color": robot.get("color", [255, 255, 255]),
                    "profile_name": profile_name  # Store profile name
                }
                self.config.add_robot(robot_data)
        
        # Prompt for new robots
        for robot in new_robots:
            self._prompt_new_robot(robot)
        
        self._refresh_robot_list()
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", f"Found {len(robots)} robot(s)")
    
    def _prompt_new_robot(self, robot: Dict):
        """Prompt user when new robot is detected."""
        robot_id = robot.get("robot_id", "?")
        robot_ip = robot.get("ip", "?")
        profile_name = self._get_profile_name(robot_id)
        
        result = messagebox.askyesno(
            "New Robot Detected",
            f"New robot detected!\n\n"
            f"Robot ID: {robot_id}\n"
            f"Profile: {profile_name}\n"
            f"IP Address: {robot_ip}\n\n"
            f"Would you like to open a controller window for this robot?",
            parent=self.root
        )
        
        if result:
            self._launch_controller_for_robot(robot_ip, "xbox")
    
    def _auto_scan_startup(self):
        """Auto-scan for robots on startup."""
        self._scan_robots()
    
    def _refresh_robot_list(self):
        """Refresh the robot list display."""
        self.robot_listbox.delete(0, tk.END)
        
        robots = self.config.get_robots()
        for robot in robots:
            robot_id = robot.get("robot_id", "?")
            name = robot.get("name", f"Robot {robot_id}")
            ip = robot.get("ip", "?")
            status = "●" if self.controller_manager.is_controller_running(ip) else "○"
            profile_name = self._get_profile_name(robot_id)
            
            # Display with profile name
            display_text = f"{status} [{profile_name}] {name} ({ip})"
            self.robot_listbox.insert(tk.END, display_text)
    
    def _on_robot_select(self, event):
        """Handle robot selection."""
        selection = self.robot_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        robots = self.config.get_robots()
        if index < len(robots):
            robot = robots[index]
            self._display_robot_info(robot)
            self.controller_button.configure(state="normal")
            # Charging mode button state is set in _display_robot_info
    
    def _get_profile_name(self, robot_id: str) -> str:
        """
        Get profile name from robot ID using default profiles.
        
        Args:
            robot_id: Robot ID as string
        
        Returns:
            Profile name or "Unknown"
        """
        # Default profiles from configure_robot.py
        DEFAULT_PROFILES = {
            "1": "THUNDER",
            "2": "BLITZ",
            "3": "NITRO",
            "4": "TURBO",
            "5": "SPEED",
            "6": "BOLT",
            "7": "FLASH",
            "8": "STORM"
        }
        return DEFAULT_PROFILES.get(str(robot_id), "Unknown")
    
    def _display_robot_info(self, robot: Dict):
        """Display robot information."""
        robot_ip = robot.get("ip", "?")
        robot_id = robot.get("robot_id", "?")
        profile_name = self._get_profile_name(robot_id)
        color = robot.get("color", [255, 255, 255])
        
        # Format color as RGB
        color_str = f"RGB({color[0]}, {color[1]}, {color[2]})" if isinstance(color, list) and len(color) == 3 else "Unknown"
        
        info_text = f"""Robot ID: {robot_id}
Profile: {profile_name}
Name: {robot.get('name', 'Unknown')}
IP Address: {robot_ip}
Version: {robot.get('version', '?')}
Profile Color: {color_str}
Controller Type: {robot.get('controller_type', 'xbox')}
Last Seen: {robot.get('last_seen', 'Never')}
"""
        
        # Add controller status
        if self.controller_manager.is_controller_running(robot_ip):
            info_text += "\nController Status: Running"
        else:
            info_text += "\nController Status: Stopped"
        
        # Add charging mode status
        charging_enabled = self.charging_mode_states.get(robot_ip, False)
        info_text += f"\nCharging Mode: {'Enabled' if charging_enabled else 'Disabled'}"
        
        self.robot_info_text.delete("1.0", "end")
        self.robot_info_text.insert("1.0", info_text)
        
        # Update charging mode button state and text
        if robot_ip:
            self.charging_mode_button.configure(state="normal")
            if charging_enabled:
                self.charging_mode_button.configure(text="Disable Charging Mode", 
                                                   fg_color=("red", "darkred"))
            else:
                self.charging_mode_button.configure(text="Enable Charging Mode",
                                                   fg_color=("gray75", "gray30"))
    
    def _launch_controller(self):
        """Launch controller for selected robot."""
        selection = self.robot_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a robot first")
            return
        
        index = selection[0]
        robots = self.config.get_robots()
        if index >= len(robots):
            return
        
        robot = robots[index]
        robot_ip = robot.get("ip")
        controller_type = self.controller_type_var.get()
        
        if not robot_ip:
            messagebox.showerror("Error", "Robot IP not found")
            return
        
        self._launch_controller_for_robot(robot_ip, controller_type)
    
    def _launch_controller_for_robot(self, robot_ip: str, controller_type: str):
        """Launch controller for a specific robot."""
        robot = self.config.get_robot_by_ip(robot_ip)
        robot_id = robot.get("robot_id") if robot else None
        
        if self.controller_manager.launch_controller(robot_ip, robot_id, controller_type):
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Controller launched for {robot_ip}")
            self._refresh_robot_list()
            self._update_active_controllers()
        else:
            messagebox.showerror("Error", f"Failed to launch controller for {robot_ip}")
    
    def _send_charging_command(self, robot_ip: str, enable: bool) -> bool:
        """
        Send charging mode command to robot via UDP.
        
        Args:
            robot_ip: Robot IP address
            enable: True to enable charging mode, False to disable
        
        Returns:
            True if command sent successfully, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            
            packet = {
                "cmd": "charging",
                "enable": enable,
                "seq": 0,
                "ts": int(time.time() * 1000)
            }
            
            message = json.dumps(packet).encode()
            sock.sendto(message, (robot_ip, ROBOT_PORT))
            sock.close()
            return True
        except Exception as e:
            print(f"Error sending charging command: {e}")
            return False
    
    def _toggle_charging_mode(self):
        """Toggle charging mode for selected robot."""
        selection = self.robot_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a robot first")
            return
        
        index = selection[0]
        robots = self.config.get_robots()
        if index >= len(robots):
            return
        
        robot = robots[index]
        robot_ip = robot.get("ip")
        
        if not robot_ip:
            messagebox.showerror("Error", "Robot IP not found")
            return
        
        # Get current state
        current_state = self.charging_mode_states.get(robot_ip, False)
        new_state = not current_state
        
        # Send command
        def send_command():
            success = self._send_charging_command(robot_ip, new_state)
            self.root.after(0, lambda: self._on_charging_command_complete(robot_ip, new_state, success))
        
        # Show status
        self.status_text.delete("1.0", "end")
        mode_text = "enabling" if new_state else "disabling"
        self.status_text.insert("1.0", f"{mode_text.capitalize()} charging mode for {robot_ip}...")
        
        # Send command in background thread
        threading.Thread(target=send_command, daemon=True).start()
    
    def _on_charging_command_complete(self, robot_ip: str, enabled: bool, success: bool):
        """Handle charging command completion."""
        if success:
            self.charging_mode_states[robot_ip] = enabled
            mode_text = "enabled" if enabled else "disabled"
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Charging mode {mode_text} for {robot_ip}")
            
            # Update robot info display if this robot is selected
            selection = self.robot_listbox.curselection()
            if selection:
                index = selection[0]
                robots = self.config.get_robots()
                if index < len(robots) and robots[index].get("ip") == robot_ip:
                    self._display_robot_info(robots[index])
        else:
            messagebox.showerror("Error", f"Failed to {'enable' if enabled else 'disable'} charging mode for {robot_ip}")
            self.status_text.delete("1.0", "end")
            self.status_text.insert("1.0", f"Failed to toggle charging mode for {robot_ip}")
    
    def _add_robot_dialog(self):
        """Show dialog to add robot manually."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Robot")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.update_idletasks()  # Ensure window is ready
        dialog.grab_set()
        
        # IP entry
        ctk.CTkLabel(dialog, text="Robot IP Address:").pack(pady=10)
        ip_entry = ctk.CTkEntry(dialog, width=300)
        ip_entry.pack(pady=5)
        
        # Name entry
        ctk.CTkLabel(dialog, text="Robot Name (optional):").pack(pady=10)
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.pack(pady=5)
        
        # Robot ID entry
        ctk.CTkLabel(dialog, text="Robot ID (optional):").pack(pady=10)
        id_entry = ctk.CTkEntry(dialog, width=300)
        id_entry.pack(pady=5)
        
        def save():
            ip = ip_entry.get().strip()
            if not ip:
                messagebox.showerror("Error", "IP address is required")
                return
            
            # Test connection
            if test_robot_connection(ip):
                robot_data = {
                    "ip": ip,
                    "name": name_entry.get().strip() or f"Robot {ip}",
                    "robot_id": id_entry.get().strip() or "?"
                }
                if self.config.add_robot(robot_data):
                    self._refresh_robot_list()
                    dialog.destroy()
                    messagebox.showinfo("Success", f"Robot {ip} added successfully")
                else:
                    messagebox.showerror("Error", "Failed to add robot")
            else:
                result = messagebox.askyesno(
                    "Connection Test Failed",
                    f"Could not connect to robot at {ip}.\n\n"
                    "Do you want to add it anyway?",
                    parent=dialog
                )
                if result:
                    robot_data = {
                        "ip": ip,
                        "name": name_entry.get().strip() or f"Robot {ip}",
                        "robot_id": id_entry.get().strip() or "?"
                    }
                    if self.config.add_robot(robot_data):
                        self._refresh_robot_list()
                        dialog.destroy()
        
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="Test Connection", 
                     command=lambda: self._test_connection(ip_entry.get().strip(), dialog)).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Save", command=save).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
    
    def _test_connection(self, ip: str, parent):
        """Test connection to robot."""
        if not ip:
            messagebox.showwarning("No IP", "Please enter an IP address", parent=parent)
            return
        
        def test_thread():
            result = test_robot_connection(ip)
            self.root.after(0, lambda: self._on_test_complete(ip, result, parent))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def _on_test_complete(self, ip: str, success: bool, parent):
        """Handle connection test completion."""
        if success:
            messagebox.showinfo("Success", f"Successfully connected to {ip}", parent=parent)
        else:
            messagebox.showerror("Failed", f"Could not connect to {ip}", parent=parent)
    
    def _remove_robot_dialog(self):
        """Show dialog to remove robot."""
        selection = self.robot_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a robot to remove")
            return
        
        index = selection[0]
        robots = self.config.get_robots()
        if index >= len(robots):
            return
        
        robot = robots[index]
        robot_ip = robot.get("ip")
        robot_name = robot.get("name", robot_ip)
        
        result = messagebox.askyesno(
            "Remove Robot",
            f"Are you sure you want to remove {robot_name} ({robot_ip})?",
            parent=self.root
        )
        
        if result:
            # Stop controller if running
            if self.controller_manager.is_controller_running(robot_ip):
                self.controller_manager.stop_controller(robot_ip)
            
            if self.config.remove_robot(robot_ip):
                self._refresh_robot_list()
                self.robot_info_text.delete("1.0", "end")
                self.robot_info_text.insert("1.0", "Select a robot to view details")
                self.controller_button.configure(state="disabled")
                self.charging_mode_button.configure(state="disabled")
                self._update_active_controllers()
            else:
                messagebox.showerror("Error", "Failed to remove robot")
    
    def _edit_robot_dialog(self):
        """Show dialog to edit robot."""
        selection = self.robot_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a robot to edit")
            return
        
        index = selection[0]
        robots = self.config.get_robots()
        if index >= len(robots):
            return
        
        robot = robots[index]
        robot_ip = robot.get("ip")
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Edit Robot")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.update_idletasks()  # Ensure window is ready
        dialog.grab_set()
        
        # IP entry (read-only)
        ctk.CTkLabel(dialog, text="Robot IP Address:").pack(pady=10)
        ip_entry = ctk.CTkEntry(dialog, width=300, state="readonly")
        ip_entry.insert(0, robot_ip)
        ip_entry.pack(pady=5)
        
        # Name entry
        ctk.CTkLabel(dialog, text="Robot Name:").pack(pady=10)
        name_entry = ctk.CTkEntry(dialog, width=300)
        name_entry.insert(0, robot.get("name", ""))
        name_entry.pack(pady=5)
        
        # Robot ID entry
        ctk.CTkLabel(dialog, text="Robot ID:").pack(pady=10)
        id_entry = ctk.CTkEntry(dialog, width=300)
        id_entry.insert(0, robot.get("robot_id", ""))
        id_entry.pack(pady=5)
        
        # Controller type dropdown
        ctk.CTkLabel(dialog, text="Controller Type:").pack(pady=10)
        controller_type_var = ctk.StringVar(value=robot.get("controller_type", "xbox"))
        controller_dropdown = ctk.CTkOptionMenu(dialog, 
                                                values=["xbox", "gamepad", "keyboard"],
                                                variable=controller_type_var)
        controller_dropdown.pack(pady=5)
        
        def save():
            updates = {
                "name": name_entry.get().strip(),
                "robot_id": id_entry.get().strip(),
                "controller_type": controller_type_var.get()
            }
            if self.config.update_robot(robot_ip, updates):
                self._refresh_robot_list()
                self._display_robot_info(self.config.get_robot_by_ip(robot_ip))
                dialog.destroy()
                messagebox.showinfo("Success", "Robot updated successfully")
            else:
                messagebox.showerror("Error", "Failed to update robot")
        
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(pady=20)
        
        ctk.CTkButton(button_frame, text="Save", command=save).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy).pack(side="left", padx=5)
    
    def _toggle_panel(self, panel, show: bool):
        """Toggle panel visibility."""
        if show:
            panel.pack(fill="x", padx=10, pady=(10, 5))
        else:
            panel.pack_forget()
    
    def _show_settings(self):
        """Show settings dialog."""
        messagebox.showinfo("Settings", "Settings dialog - To be implemented")
    
    def _export_config(self):
        """Export configuration to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            if self.config.export_config(filename):
                messagebox.showinfo("Success", f"Configuration exported to {filename}")
            else:
                messagebox.showerror("Error", "Failed to export configuration")
    
    def _import_config(self):
        """Import configuration from file."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            result = messagebox.askyesno(
                "Import Configuration",
                "This will replace your current configuration. Continue?",
                parent=self.root
            )
            if result:
                if self.config.import_config(filename):
                    self._refresh_robot_list()
                    self._update_network_display()
                    messagebox.showinfo("Success", "Configuration imported successfully")
                else:
                    messagebox.showerror("Error", "Failed to import configuration")
    
    def _show_theme_settings(self):
        """Show theme settings dialog."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Theme Settings")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.update_idletasks()  # Ensure window is ready
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Appearance Mode:").pack(pady=10)
        mode_var = ctk.StringVar(value=ctk.get_appearance_mode())
        mode_menu = ctk.CTkOptionMenu(dialog, values=["dark", "light", "system"],
                                       variable=mode_var)
        mode_menu.pack(pady=5)
        
        def apply():
            ctk.set_appearance_mode(mode_var.get())
            dialog.destroy()
        
        ctk.CTkButton(dialog, text="Apply", command=apply).pack(pady=20)
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Robot Controller Master\n\n"
            "Version 1.0\n"
            "St. Clair College Robotics Club\n\n"
            "Manage multiple robot controllers from one interface.",
            parent=self.root
        )
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts."""
        messagebox.showinfo(
            "Keyboard Shortcuts",
            "Keyboard Shortcuts:\n\n"
            "Ctrl+S - Scan for robots\n"
            "Ctrl+A - Add robot\n"
            "Ctrl+R - Remove robot\n"
            "Ctrl+E - Edit robot\n"
            "Ctrl+Q - Exit",
            parent=self.root
        )
    
    def _update_active_controllers(self):
        """Update active controllers count."""
        count = len(self.controller_manager.get_all_running_controllers())
        self.active_controllers_label.configure(text=f"Active Controllers: {count}")
    
    def _start_background_tasks(self):
        """Start background monitoring tasks."""
        def monitor():
            while self.running:
                time.sleep(2)  # Update every 2 seconds
                if self.running:
                    self.root.after(0, self._refresh_robot_list)
                    self.root.after(0, self._update_active_controllers)
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def _on_closing(self):
        """Handle window closing."""
        self.running = False
        self.controller_manager.cleanup()
        self.root.destroy()
    
    def run(self):
        """Run the application."""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()


def main():
    """Main entry point."""
    app = RobotMasterGUI()
    app.run()


if __name__ == "__main__":
    main()

