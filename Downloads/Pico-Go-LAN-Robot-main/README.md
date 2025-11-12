# 🤖 Pico-Go LAN Robot

**Real-time LAN-controlled robot using Raspberry Pi Pico W and Waveshare Pico-Go v2**

Control your robot with an Xbox controller over Wi-Fi. Perfect for robotics education, competitions, and fun!

---

## ✨ Features

- 🎮 **Xbox controller** control at 30 Hz
- 📡 **Local Wi-Fi** control (no internet needed)
- 🛡️ **Safety watchdog** - motors stop if connection lost
- 📺 **Live LCD display** with status information
- 🌈 **RGB LED underglow** with color-coded status
- 🏁 **8 robot profiles** - customize name and colors
- 🔍 **Auto-discovery** - automatically finds robots on network via UDP broadcast

---

## 🚀 Quick Start

### 1. Setup Wi-Fi Hotspot

Turn on your phone hotspot:
- **SSID**: `DevNet-2.4G`
- **Password**: `DevPass**99`
- **Band**: 2.4 GHz only (Pico W doesn't support 5 GHz)

Or configure your own network in `firmware/config.py`.

### 2. Flash MicroPython Firmware

**⚠️ IMPORTANT: You MUST use Pico W firmware (not regular Pico firmware)!**

1. Connect Pico W to computer via USB
2. Hold **BOOTSEL** button and plug in USB (or double-press RESET while holding BOOTSEL)
3. Copy `PicoW_Micropython/RPI_PICO_W-20250911-v1.26.1.uf2` to the Pico W drive (it will appear as `RPI-RP2`)
4. Wait for the Pico W to reboot automatically

**Note**: The robot uses UDP protocol on port 8765 for low-latency control (not WebSocket despite the module name).

### 3. Upload Robot Code

```bash
# Install mpremote (MicroPython tool)
pip install mpremote

# Upload all firmware files
cd firmware
mpremote cp *.py :
```

**Watch the LCD:** 
- **BOOT**: Initial startup (robot name and ID displayed)
- **NET_UP**: WiFi connected (shows IP address, e.g., 192.168.8.104)
- **CLIENT_OK**: Controller connected and ready
- **DRIVING**: Active control (shows robot icon, connection status)
- **LINK_LOST**: Connection timeout (motors stopped for safety)

### 4. Launch Master GUI

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the Master GUI (ONLY entry point - everything runs through this!)
# Notice: Only ONE file at controller/ level - it's obvious which one to run!
python3 controller/robot_master_gui.py
```

**The Master GUI is the ONLY way to control robots. Everything runs through it:**

1. **Auto-discovery**: Click "Scan for Robots" to automatically find robots on the network
2. **Launch Controller**: Select a robot and click "Launch Controller" to open a controller window
3. **Launch Calibration**: Select a robot and click "Launch Calibration" to open the calibration tool
4. **Manage Multiple Robots**: Control multiple robots from one interface

**Controller Controls (when launched from Master GUI):**
- **Right Trigger**: Drive forward
- **Left Trigger**: Drive backward
- **Left Stick X-axis**: Steering (left/right)
- **BACK + START**: Toggle charging mode (power saving)
- **START (alone)**: Exit controller

**Control Protocol:**
- Uses UDP on port 8765 for low-latency control
- 30 Hz control rate (33ms intervals)
- Safety watchdog stops motors if no packet received for 500ms

---

## 📂 Project Structure

```
Pico-Go-LAN-Robot/
├── PicoW_Micropython/    # ⚠️ MicroPython firmware file (flash this!)
│   └── RPI_PICO_W-20250911-v1.26.1.uf2  # Pico W firmware (v1.26.1)
├── firmware/             # Robot firmware code (Python files)
│   ├── main.py           # Main entry point (runs automatically on boot)
│   ├── config.py         # Robot configuration (edit ROBOT_ID, WiFi settings)
│   ├── wifi.py           # WiFi connection management
│   ├── motor.py          # Motor control (TB6612FNG driver)
│   ├── lcd_status.py     # LCD display (ST7789)
│   ├── underglow.py      # RGB LED underglow (WS2812B)
│   ├── watchdog.py       # Safety watchdog system
│   ├── ws_server.py      # UDP server for control commands (port 8765)
│   ├── calibration.py    # Motor calibration system
│   └── utils.py          # Utility functions
├── controller/           # Python controller application
│   ├── robot_master_gui.py  # ⭐ MAIN ENTRY POINT - Launch this ONLY!
│   ├── controller_xbox.py  # Xbox controller (launched from Master GUI)
│   ├── calibrate.py      # Calibration tool (launched from Master GUI)
│   ├── controller_manager.py  # Manages controller subprocesses
│   └── robot_config.py   # Robot configuration storage
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

**Important**: 
- `robot_master_gui.py` is the **ONLY** entry point
- `controller_xbox.py` and `calibrate.py` are **subsidiary modules** - they cannot be run directly
- They are automatically launched by the Master GUI as subprocesses
- All controller modules are in the `controller/` directory for simplicity

---

## 🏁 Robot Profiles

Each robot can have a unique profile (1-8) with:
- **Name**: Displayed on LCD (e.g., "THUNDER", "BLITZ", "NITRO", "TURBO", "SPEED", "BOLT", "FLASH", "STORM")
- **Color**: RGB LED underglow color (unique per profile)
- **LCD Theme**: Robot icon and color scheme for display

**Available Profiles:**
1. **THUNDER** - Orange (255, 140, 0)
2. **BLITZ** - Yellow (255, 255, 0)
3. **NITRO** - Red (255, 0, 0)
4. **TURBO** - Green (0, 255, 0)
5. **SPEED** - White (255, 255, 255)
6. **BOLT** - Blue (0, 0, 255)
7. **FLASH** - Teal (0, 255, 128)
8. **STORM** - Cyan (0, 200, 255)

Edit `firmware/config.py` to set `ROBOT_ID` (1-8). The robot name, color, and LCD theme will update automatically.

---

## 🔧 Calibration

If your robot drifts or steers incorrectly:

1. Launch Master GUI
2. Select your robot from the list
3. Click "Launch Calibration" button
4. Use Xbox controller to adjust:
   - **D-Pad Left/Right**: Adjust steering trim
   - **D-Pad Up/Down**: Adjust motor balance (left/right)
   - **A button**: Save calibration to robot
   - **B button**: Reset to defaults
   - **START**: Exit calibration

Calibration is saved on the robot's flash memory and persists across reboots. The calibration tool uses UDP on port 8765 to communicate with the robot.

---

## 🛠️ Hardware Requirements

- **Waveshare Pico-Go v2** with Raspberry Pi Pico W
- **7.4V LiPo battery** (1000+ mAh recommended)
- **Xbox controller** (USB or Bluetooth)
- **Laptop/PC** with Wi-Fi and Python 3.11+
- **Phone hotspot** or Wi-Fi router (2.4 GHz)

---

## 📋 Software Requirements

- **Python 3.11+**
- **MicroPython 1.26.1** (Pico W firmware included as .uf2 file)
- **Dependencies**: See `requirements.txt`

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 🔍 Troubleshooting

### Robot doesn't appear in discovery
- Check robot is powered on and connected to Wi-Fi
- Verify LCD shows "NET_UP" with IP address (e.g., 192.168.8.104)
- Ensure laptop and robot are on same network (same Wi-Fi SSID)
- Check robot is running Pico W firmware (not regular Pico)
- Try manually adding robot IP in Master GUI
- Verify UDP port 8765 is not blocked by firewall

### Motors don't move
- Check battery is charged (7.0-8.4V recommended)
- Verify controller window is open and connected (check Master GUI status)
- Check calibration settings (use calibration tool from Master GUI)
- Ensure connection is active (LCD should show "DRIVING" when receiving commands)
- Verify motors are enabled (watchdog must be receiving packets)
- Check motor pins in `firmware/config.py` match your hardware

### Connection lost
- Check Wi-Fi signal strength (LCD shows RSSI in dBm)
- Verify network SSID/password in `firmware/config.py` match your hotspot
- Ensure phone hotspot is on and 2.4 GHz (Pico W doesn't support 5 GHz)
- Restart robot and reconnect
- Check if robot LCD shows "LINK_LOST" state
- Verify UDP port 8765 is accessible on your network

---

## 📝 Configuration

### Robot Configuration (`firmware/config.py`)

**Main Settings:**
- `ROBOT_ID`: Robot profile (1-8) - determines name and color
- `WIFI_SSID`: Network name (default: `DevNet-2.4G`)
- `WIFI_PASSWORD`: Network password (default: `DevPass**99`)
- `WEBSOCKET_PORT`: Control port (default: 8765) - uses UDP protocol
- `CONTROL_RATE_HZ`: Control packet rate (default: 30 Hz)
- `WATCHDOG_TIMEOUT_MS`: Safety timeout (default: 500ms)

**Robot Profiles (1-8):**
- Each profile has a unique name (THUNDER, BLITZ, NITRO, TURBO, SPEED, BOLT, FLASH, STORM)
- Each profile has a unique RGB color for LED underglow
- Change `ROBOT_ID` to switch profiles

**Default Network Settings:**
- SSID: `DevNet-2.4G`
- Password: `DevPass**99`
- Port: `8765` (UDP)

---

## 🎮 Usage

**Everything is done through the Master GUI - it's the only entry point!**

1. **Power on robot** - Wait for LCD to show IP address (NET_UP state)
2. **Launch Master GUI** - `python3 controller/robot_master_gui.py`
3. **Auto-discovery** - Robots are automatically scanned on startup (UDP broadcast on port 8765)
4. **Select robot** - Click on robot in the list (shows IP address and name)
5. **Launch controller** - Click "Launch Controller" button to open controller window
6. **Or launch calibration** - Click "Launch Calibration" button to calibrate motors
7. **Drive!** - Use Xbox controller to control robot (when controller window is open)
   - Right trigger: Forward
   - Left trigger: Backward  
   - Left stick X: Steering
   - START: Exit controller

**Note**: All robot control and calibration is done through the Master GUI. Do not run `controller_xbox.py` or `calibrate.py` directly - they are subsidiary modules launched automatically by the Master GUI!

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👥 Credits

**St. Clair College Robotics Club**

Author: Jeremy Dueck

---

## 🆘 Support

For issues or questions:
1. Check troubleshooting section above
2. Verify all hardware connections
3. Ensure firmware and controller code are up to date
4. Check robot LCD for error messages

---

**Happy Robot Racing! 🏁**
