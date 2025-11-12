# Robot Controller Master GUI

A modern, cross-platform desktop application for managing multiple robot controllers simultaneously.

## Features

- **Auto-Discovery**: Automatically scans for robots on the network when the application starts
- **Multiple Controllers**: Launch and manage multiple robot controllers simultaneously
- **Network Configuration**: Display and edit network SSID and password (with password reveal)
- **Robot Management**: Add, edit, and remove robots with connection testing
- **Controller Types**: Support for Xbox, gamepad, and keyboard controllers
- **Real-Time Status**: Monitor robot connections and controller status
- **Modern UI**: Built with CustomTkinter for a sleek, modern appearance

## Requirements

- Python 3.11+
- CustomTkinter >= 5.2.0
- pygame >= 2.5.0 (for controllers)
- All dependencies from `requirements.txt`

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python3 robot_master_gui.py
```

## Usage

### Starting the Application

Simply run `robot_master_gui.py`. The application will:
1. Auto-scan for robots on the network
2. Display discovered robots in the list
3. Prompt you if new robots are detected

### Network Configuration

1. Click "Edit Network Config" to set the SSID and password
2. Use "Show Password" / "Hide Password" to toggle password visibility
3. The network information is displayed at the top of the window

### Managing Robots

- **Add Robot**: Click "Add Robot" or use Edit → Add Robot menu
  - Enter robot IP address
  - Optionally enter name and robot ID
  - Test connection before adding
  
- **Remove Robot**: Select robot and use Edit → Remove Robot menu
  - Controller will be stopped if running

- **Edit Robot**: Select robot and use Edit → Edit Robot menu

### Launching Controllers

1. Select a robot from the list
2. Choose controller type from dropdown (Xbox, gamepad, keyboard)
3. Click "Launch Controller"
4. A separate controller window will open for that robot

### Menu Options

- **File**:
  - Settings: Application settings
  - Export Config: Export robot configuration to JSON
  - Import Config: Import robot configuration from JSON
  - Exit: Close application

- **Edit**:
  - Add Robot: Manually add a robot
  - Remove Robot: Remove selected robot
  - Edit Robot: Edit selected robot
  - Refresh Discovery: Manually scan for robots

- **View**:
  - Show/Hide Network Panel: Toggle network panel visibility
  - Theme Settings: Change appearance mode (dark/light/system)

- **Help**:
  - About: Application information
  - Keyboard Shortcuts: List of keyboard shortcuts

## Building Desktop Executable

See `build/README.md` for instructions on building executables for Windows, Linux, and Mac.

## Configuration Storage

Configuration is stored in platform-specific locations:

- **Windows**: `%APPDATA%/picogo/robots.json`
- **Linux**: `~/.config/picogo/robots.json`
- **Mac**: `~/Library/Application Support/picogo/robots.json`

## Troubleshooting

### Robots Not Found

- Ensure robots are powered on and connected to WiFi
- Check that you're on the same network as the robots
- Try manual "Scan for Robots" button
- Add robot manually with IP address

### Controller Won't Launch

- Ensure controller script exists (controller_xbox.py, etc.)
- Check that Python can find the controller script
- Verify robot IP address is correct
- Check console/terminal for error messages

### Network Configuration Not Saving

- Check file permissions in configuration directory
- Ensure sufficient disk space
- Check console for error messages

## Keyboard Shortcuts

- Ctrl+S: Scan for robots
- Ctrl+A: Add robot
- Ctrl+R: Remove robot
- Ctrl+E: Edit robot
- Ctrl+Q: Exit

## Architecture

The application consists of three main components:

1. **robot_config.py**: Manages robot and network configuration storage
2. **controller_manager.py**: Handles launching and monitoring controller subprocesses
3. **robot_master_gui.py**: Main GUI application with CustomTkinter

## License

MIT License - St. Clair College Robotics Club

