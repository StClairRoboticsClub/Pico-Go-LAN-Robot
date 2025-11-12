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
        self.robot_gamepad_assignments: Dict[str, int] = {}  # robot_ip -> joystick_index
        self.available_gamepads = 0
        self.gamepad_names: Dict[int, str] = {}  # joystick_index -> gamepad name
        
        # Initialize pygame for gamepad detection (minimal init)
        if PYGAME_AVAILABLE:
            try:
                pygame.init()
                pygame.joystick.init()
                self._update_gamepad_list()
            except:
                pass
        
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
        
        robots = discover_robots_on_network(timeout=2.0)
        self.discovered_robots = {robot['ip']: robot for robot in robots}
        
        self.robot_listbox.delete(0, tk.END)
        
        if not robots:
            self.robot_listbox.insert(0, "No robots found. Check network connection.")
        else:
            for robot in robots:
                robot_id = robot.get('robot_id', '?')
                hostname = robot.get('hostname', 'unknown')
                ip = robot['ip']
                
                # Show gamepad assignment if exists
                gamepad_info = ""
                if ip in self.robot_gamepad_assignments:
                    gamepad_idx = self.robot_gamepad_assignments[ip]
                    gamepad_name = self.gamepad_names.get(gamepad_idx, f"Gamepad {gamepad_idx}")
                    gamepad_info = f" [Gamepad {gamepad_idx}]"
                
                display_text = f"Robot #{robot_id} ({hostname}) - {ip}{gamepad_info}"
                self.robot_listbox.insert(tk.END, display_text)
                self.config.add_robot(ip, hostname, robot_id)
        
        # Also show saved robots
        saved_robots = self.config.get_robots()
        for robot in saved_robots:
            ip = robot.get('ip')
            if ip and ip not in self.discovered_robots:
                name = robot.get('name', 'Unknown')
                display_text = f"[Saved] {name} - {ip}"
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
            self.gamepad_info_label.configure(text="Gamepads: pygame not available")
            return
        
        try:
            pygame.joystick.quit()
            pygame.joystick.init()
            
            count = pygame.joystick.get_count()
            self.available_gamepads = count
            self.gamepad_names = {}
            
            for i in range(count):
                try:
                    joystick = pygame.joystick.Joystick(i)
                    joystick.init()
                    name = joystick.get_name()
                    self.gamepad_names[i] = name
                except:
                    self.gamepad_names[i] = f"Gamepad {i}"
            
            if count == 0:
                self.gamepad_info_label.configure(text="Gamepads: 0 detected")
            else:
                self.gamepad_info_label.configure(text=f"Gamepads: {count} detected")
        except Exception as e:
            self.gamepad_info_label.configure(text=f"Gamepads: Error ({str(e)[:20]})")
    
    def _launch_controller_with_gamepad(self):
        """Launch controller for selected robot with gamepad selection."""
        robot_ip = self._get_selected_robot_ip()
        if not robot_ip:
            messagebox.showwarning("No Selection", "Please select a robot first.")
            return
        
        if self.controller_manager.is_controller_running(robot_ip):
            messagebox.showinfo("Already Running", f"Controller already running for {robot_ip}")
            return
        
        # Check if gamepad already assigned
        if robot_ip in self.robot_gamepad_assignments:
            # Use existing assignment
            joystick_index = self.robot_gamepad_assignments[robot_ip]
        else:
            # Auto-assign next available gamepad
            self._update_gamepad_list()
            used_indices = set(self.robot_gamepad_assignments.values())
            joystick_index = None
            
            # Find first available gamepad
            for i in range(self.available_gamepads):
                if i not in used_indices:
                    joystick_index = i
                    break
            
            # If no gamepads available, show dialog
            if joystick_index is None:
                joystick_index = self._select_gamepad_dialog()
                if joystick_index is None:
                    return  # User cancelled
        
        # Store assignment
        self.robot_gamepad_assignments[robot_ip] = joystick_index
        
        # Get robot ID if available
        robot_id = None
        if robot_ip in self.discovered_robots:
            robot_id = self.discovered_robots[robot_ip].get('robot_id')
        
        # Launch controller with assigned gamepad
        if self.controller_manager.launch_controller(robot_ip, robot_id, "xbox", joystick_index):
            gamepad_name = self.gamepad_names.get(joystick_index, f"Gamepad {joystick_index}")
            messagebox.showinfo("Success", f"Controller launched for {robot_ip}\nUsing: {gamepad_name}")
            # Refresh robot list to show gamepad assignment
            self._scan_robots()
        else:
            messagebox.showerror("Error", f"Failed to launch controller for {robot_ip}")
    
    def _select_gamepad_dialog(self) -> Optional[int]:
        """Show dialog to select a gamepad."""
        if self.available_gamepads == 0:
            messagebox.showwarning("No Gamepads", "No gamepads detected. Controller will use keyboard input.")
            return 0  # Default to 0, will fall back to keyboard
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Select Gamepad")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        result = [None]  # Use list to allow modification in nested function
        
        ctk.CTkLabel(dialog, text="Select gamepad for this robot:", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)
        
        # Gamepad list
        listbox_frame = ctk.CTkFrame(dialog)
        listbox_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        gamepad_listbox = tk.Listbox(listbox_frame, height=8, font=("Arial", 11))
        gamepad_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
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
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        def select_gamepad():
            selection = gamepad_listbox.curselection()
            if selection:
                result[0] = selection[0]
                dialog.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select a gamepad.")
        
        def cancel():
            dialog.destroy()
        
        ctk.CTkButton(button_frame, text="Select", command=select_gamepad).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", command=cancel).pack(side="left", padx=5)
        
        dialog.wait_window()
        return result[0]
    
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
