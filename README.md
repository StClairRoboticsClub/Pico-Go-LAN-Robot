# 🤖 Pico-Go LAN Robot

**Real-time LAN-controlled racing robot using Raspberry Pi Pico W and Waveshare Pico-Go v2**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MicroPython](https://img.shields.io/badge/MicroPython-1.22+-green.svg)](https://micropython.org/)

---

## 📘 Overview

The **Pico-Go LAN Robot** is a teleoperated racing robot platform built for education and competition, featuring:

- 🎮 **Real-time Xbox controller** input at 30 Hz
- 📡 **Local WiFi control** (no internet required)
- 🛡️ **Automatic safety cutoff** (500ms watchdog timeout)
- 📺 **Live LCD status display** with racing graphics
- 🌈 **RGB LED underglow** with state-based animations
- 🏁 **8 robot profiles** - easy to configure for racing events

Perfect for robotics education, competitions, and sparking curiosity in STEM!

---

## 🎯 Quick Start

### 1. Setup Phone Hotspot

Turn on your phone hotspot with these settings:
- **SSID**: `DevNet-2.4G`
- **Password**: `DevPass**99`
- **Band**: 2.4 GHz only (Pico W doesn't support 5 GHz)

### 2. Configure Robot Profile

**Edit `firmware/config.py` and change ONE line:**

```python
ROBOT_PROFILE = 2  # ← CHANGE THIS NUMBER (0-7) BEFORE FLASHING!
```

**Available Profiles:**
- `0`: WHITE - Clean, bright, high visibility
- `1`: RED - Bold, aggressive racing style
- `2`: THUNDER - High energy (Orange) ⚡
- `3`: BLITZ - Fast and striking (Yellow)
- `4`: NITRO - Speed boost (Green)
- `5`: TURBO - Cool performance (Blue)
- `6`: SPEED - Deep racing (Indigo)
- `7`: PULSE - Electric purple energy (Violet)

Each profile sets the robot's name, LCD theme color, and LED underglow color.

### 3. Flash Firmware (Pico W)

```bash
# Install mpremote
pip install mpremote

# Upload all firmware files
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :
mpremote reset
```

**Watch the LCD:** BOOT (purple) → NET_UP (blue) → displays robot IP

### 4. Run Controller (Laptop)

```bash
# Install dependencies
pip install -r controller/requirements.txt

# Connect Xbox controller via USB or Bluetooth

# Run controller (replace IP with value from LCD)
python3 controller/controller_xbox.py 10.42.0.123
```

**Controls:**
- **Right Trigger**: Forward throttle
- **Left Trigger**: Reverse throttle
- **Left Stick X-axis**: Steering
- **BACK + START**: Toggle charging mode (power saving)
- **START (alone)**: Exit controller app

### 5. Charging Mode (Power Saving)

The robot has a special low-power charging mode that can be activated remotely from the controller:

**To Enter Charging Mode:**
1. Make sure robot and controller are connected
2. Press **BACK + START** together on the Xbox controller
3. LCD will show "CHARGING MODE" screen
4. All systems suspended (motors, WiFi, LEDs off)

**To Exit Charging Mode:**
1. Press **BACK + START** again on the controller
2. Robot will reset and resume normal operation

This is ideal when charging the battery or storing the robot - it prevents unnecessary power drain while keeping the LCD active to show charging status.

---

## 📂 Key Files

```
Pico-Go-LAN-Robot/
├── firmware/              # MicroPython code for Pico W
│   ├── config.py         # ← EDIT THIS to change robot profile & WiFi
│   ├── main.py           # Main entry point
│   ├── lcd_status.py     # LCD racing display
│   ├── underglow.py      # WS2812B LED control
│   └── ...
├── controller/           # Python controller application
│   └── controller_xbox.py
└── docs/                 # Documentation
    ├── GUIDE.md         # Complete setup guide
    ├── CALIBRATION.md   # Motor calibration
    └── RACING_LCD_DISPLAYS.md
```

---

## 🌈 Robot Profiles

Each profile configures:
1. **Robot Name** - Displayed on LCD
2. **LED Underglow Color** - RGB color for WS2812B LEDs
3. **LCD Theme Color** - Used for racing graphics

### LED Underglow States

| State | Animation | Description |
|-------|-----------|-------------|
| **BOOT** | Flash robot color + red | Robot starting up |
| **NET_UP** | Solid robot color | WiFi connected, waiting for controller |
| **CLIENT_OK** | Flash robot color + green | Controller connected |
| **DRIVING** | Solid robot color | Driving (controller active) |
| **LINK_LOST** | Flash robot color + red | Connection lost |

---

## 🐛 Troubleshooting

### Robot Won't Connect to WiFi
1. Make sure phone hotspot is on with SSID `DevNet-2.4G`
2. Verify password is `DevPass**99` in `firmware/config.py`
3. Check phone is broadcasting 2.4 GHz (not 5 GHz only)
4. Check serial output: `mpremote connect /dev/ttyACM0`

### Motors Don't Move
1. Check battery is charged (7.0-8.4V)
2. Verify STBY pin (GP6) is HIGH
3. Check motor connections

### Controller Won't Connect
1. Verify robot IP from LCD display
2. Make sure laptop is connected to same DevNet-2.4G hotspot
3. Test connectivity: `ping <robot-ip>`

For detailed troubleshooting, see **[docs/GUIDE.md](docs/GUIDE.md)**.

---

## 📚 Documentation

- **[GUIDE.md](docs/GUIDE.md)** - Complete setup and development guide
- **[CALIBRATION.md](docs/CALIBRATION.md)** - Motor calibration procedures
- **[RACING_LCD_DISPLAYS.md](docs/RACING_LCD_DISPLAYS.md)** - LCD design documentation

## 🤖 Multi-Agent Development System

This project uses a structured multi-agent coordination system for organized development:

- **[AGENT_ROLES.md](AGENT_ROLES.md)** - Complete agent role definitions and responsibilities
- **[agents.yaml](agents.yaml)** - Machine-readable agent configuration and task routing
- **[DIRECTOR_WORKFLOW.md](DIRECTOR_WORKFLOW.md)** - Director coordination procedures
- **[TASK_ROUTING.md](TASK_ROUTING.md)** - Task classification and routing guide
- **[QUALITY_METRICS.md](QUALITY_METRICS.md)** - Quality standards and performance benchmarks
- **[agent_prompts/](agent_prompts/)** - Agent system prompt templates

The system includes:
- **Director Agent**: Main coordinator for task management and integration
- **Firmware & Hardware Agent**: Owns `/firmware` and `/schematics`
- **Controller & Network Agent**: Owns `/controller`
- **Documentation & Performance Agent**: Owns `/docs`

---

## 📜 License

MIT License - See LICENSE file for details.

**Author**: Jeremy Dueck  
**Organization**: St. Clair College Robotics Club  
**Repository**: https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot

---

**Happy Racing! 🏁🤖**
