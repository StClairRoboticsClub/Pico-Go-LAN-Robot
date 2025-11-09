# 🤖 Pico-Go LAN Robot# 🤖 Pico-Go LAN Robot# 🤖 Pico-Go LAN Robot



**Real-time LAN-controlled racing robot using Raspberry Pi Pico W and Waveshare Pico-Go v2**



[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)**Real-time LAN-controlled robot using Raspberry Pi Pico W and Waveshare Pico-Go v2****Real-time LAN-controlled sumo robot using Raspberry Pi Pico W and Waveshare Pico-Go v2**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

[![MicroPython](https://img.shields.io/badge/MicroPython-1.22+-green.svg)](https://micropython.org/)



---[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)



## 📘 Overview[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)



The **Pico-Go LAN Robot** is a teleoperated racing robot platform built for education and competition, featuring:[![MicroPython](https://img.shields.io/badge/MicroPython-1.22+-green.svg)](https://micropython.org/)[![MicroPython](https://img.shields.io/badge/MicroPython-1.22+-green.svg)](https://micropython.org/)



- 🎮 **Real-time Xbox controller** input at 30 Hz

- 📡 **Local WiFi control** (no internet required)

- 🛡️ **Automatic safety cutoff** (500ms watchdog timeout)------

- 📺 **Live LCD status display** with racing graphics

- 🌈 **RGB LED underglow** with state-based animations

- 🏁 **8 robot profiles** - easy to configure for racing events

## Overview## 📘 Overview

Perfect for robotics education, competitions, and sparking curiosity in STEM!



---

A teleoperated robot platform built for education, competitions, and R&D. Control your robot in real-time over WiFi using an Xbox controller.The **Pico-Go LAN Robot** is a teleoperated robot platform built on the Waveshare Pico-Go v2 chassis, featuring:

## 🎯 Quick Start



### 1. Setup Ubuntu Hotspot (Laptop)

**Key Features:**- **Real-time control** over local Wi-Fi (no internet required)

```bash

# Create the Wi-Fi hotspot- 🎮 Real-time Xbox controller input (30 Hz)- **Xbox controller** input at 30 Hz via WebSocket/TCP

sudo ./scripts/setup_hotspot.sh start

- 📡 Local WiFi control (no internet required)- **Automatic fail-safe** - motors stop if connection lost > 200ms

# Verify it's running

./scripts/setup_hotspot.sh status- 🛡️ Automatic safety cutoff (200ms timeout)- **Live status display** on ST7789 LCD

```

- 📺 Live LCD status display with color-coded connection- **Modular architecture** - easy to extend and customize

**Default Settings:**

- SSID: `PicoLAN`- 🔧 Modular, extensible codebase

- Password: `pico1234`

- Network: `10.42.0.x`Perfect for robotics education, competitions, and R&D projects.



### 2. Configure Robot Profile---



**Edit `firmware/config.py` and change ONE line:**---



```python## Quick Start

ROBOT_PROFILE = 2  # ← CHANGE THIS NUMBER (0-7) BEFORE FLASHING!

```## 🎯 Quick Start



**Available Profiles:**### 1. Setup Laptop Hotspot

- `0`: WHITE - Clean, bright, high visibility

- `1`: RED - Bold, aggressive racing style### 1. Setup Ubuntu Hotspot (Laptop)

- `2`: THUNDER - High energy (Orange) ⚡

- `3`: BLITZ - Fast and striking (Yellow)```bash

- `4`: NITRO - Speed boost (Green)

- `5`: TURBO - Cool performance (Blue)git clone https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot.git```bash

- `6`: SPEED - Deep racing (Indigo)

- `7`: PULSE - Electric purple energy (Violet)cd Pico-Go-LAN-Robot# Create the Wi-Fi hotspot



Each profile sets the robot's name, LCD theme color, and LED underglow color.pip install -r controller/requirements.txtsudo ./scripts/setup_hotspot.sh start



### 3. Flash Firmware (Pico W)sudo ./scripts/setup_hotspot.sh start



```bash```# Verify it's running

# Install mpremote

pip install mpremote./scripts/setup_hotspot.sh status



# Upload all firmware files### 2. Configure & Flash Firmware```

cd firmware

mpremote connect /dev/ttyACM0 cp *.py :

mpremote reset

```Edit `firmware/config.py` with your WiFi credentials, then:### 2. Flash Firmware (Pico W)



**Watch the LCD:** BOOT (purple) → NET_UP (blue) → displays robot IP



### 4. Run Controller (Laptop)```bash```bash



```bashpip install mpremote# Install MicroPython on Pico W (if not already installed)

# Install dependencies

pip install -r controller/requirements.txtcd firmware# Download from: https://micropython.org/download/RPI_PICO_W/



# Connect Xbox controller via USB or Bluetoothmpremote connect /dev/ttyACM0 cp *.py :



# Run controller (replace IP with value from LCD)mpremote reset# Upload firmware files

python3 controller/controller_xbox.py 10.42.0.123

``````cd firmware



**Controls:**mpremote connect /dev/ttyACM0 cp *.py :

- **Left Stick Y-axis**: Forward/Reverse throttle

- **Left Stick X-axis**: Steering### 3. Run Controllermpremote reset

- **START button**: Exit controller app

```

---

```bash

## 🧩 System Architecture

python3 controller/controller_xbox.py <robot-ip-from-lcd>### 3. Run Controller (Laptop)

```

┌─────────────────┐```

│ Xbox Controller │

└────────┬────────┘```bash

         │ USB/Bluetooth

         ▼**Controls:** Left stick Y = forward/reverse, Left stick X = steering# Install dependencies

┌─────────────────────┐      Wi-Fi LAN       ┌──────────────────┐

│ Laptop Controller   │◄───────────────────►│ Raspberry Pi     │pip install -r controller/requirements.txt

│ • Python 3.11       │   UDP 10.42.0.x:8765 │ Pico W           │

│ • pygame            │                      │ • MicroPython    │---

│ • asyncio           │                      │ • Motor Control  │

└─────────────────────┘                      │ • LCD Display    │# Connect Xbox controller via USB or Bluetooth

                                              │ • LED Underglow  │

                                              │ • Safety Systems │## System Architecture

                                              └──────────────────┘

```# Run controller (update robot IP if needed)



---```python3 controller/controller_xbox.py 10.42.0.123



## 🛠️ Hardware Requirements[Xbox Controller] ──► [Laptop] ──WiFi──► [Pico W] ──► [Motors]```



| Component | Specification | Notes |                                          └──► [LCD Status]

|-----------|---------------|-------|

| **Microcontroller** | Raspberry Pi Pico W | RP2040 + CYW43439 Wi-Fi |```---

| **Platform** | Waveshare Pico-Go v2 | Includes motors, LCD, motor driver |

| **Motor Driver** | TB6612FNG | Dual H-bridge |

| **Display** | ST7789 240×135 LCD | SPI display with racing graphics |

| **LED Underglow** | WS2812B (4 LEDs) | GPIO 22, state-based animations |**Components:**## 🧩 System Architecture

| **Battery** | 7.4V Li-ion | 2S with protection |

| **Controller** | Xbox Controller | Wired or Bluetooth |- **Firmware:** MicroPython on Raspberry Pi Pico W

| **Laptop** | Ubuntu 22.04+ | Hosts hotspot + controller app |

- **Controller:** Python app with pygame for Xbox input```

### Pin Assignments

- **Network:** Ubuntu hotspot (10.42.0.x), TCP/JSON protocol┌─────────────────┐

**Motor Driver (TB6612FNG):**

- Motor A: PWMA=GP0, AIN1=GP1, AIN2=GP2- **Hardware:** Waveshare Pico-Go v2, TB6612FNG driver, ST7789 LCD│ Xbox Controller │

- Motor B: PWMB=GP3, BIN1=GP4, BIN2=GP5

- STBY: GP6└────────┬────────┘



**LCD (ST7789):**---         │ USB/Bluetooth

- SPI: SCK=GP18, MOSI=GP19

- Control: DC=GP16, RST=GP20, CS=GP17, BL=GP21         ▼



**LED Underglow (WS2812B):**## Project Structure┌─────────────────────┐      Wi-Fi LAN       ┌──────────────────┐

- Data: GP22 (4 LEDs)

│ Laptop Controller   │◄───────────────────►│ Raspberry Pi     │

---

```│ • Python 3.11       │   10.42.0.x:8765    │ Pico W           │

## 📦 Software Requirements

Pico-Go-LAN-Robot/│ • pygame            │                      │ • MicroPython    │

### Firmware (Pico W)

- MicroPython 1.22+├── firmware/           # MicroPython code for Pico W│ • asyncio           │                      │ • Motor Control  │

- Built-in libraries: `uasyncio`, `network`, `machine`, `json`

│   ├── main.py        # Entry point└─────────────────────┘                      │ • LCD Display    │

### Controller (Laptop)

- Python 3.11+│   ├── config.py      # Hardware/network configuration                                              │ • Safety Systems │

- pygame >= 2.5

- asyncio (built-in)│   ├── motor.py       # Motor control                                              └──────────────────┘



---│   ├── wifi.py        # WiFi management```



## 🌈 Robot Profiles System│   ├── ws_server.py   # TCP server



Each robot profile configures:│   ├── lcd_status.py  # LCD display---

1. **Robot Name** - Displayed on LCD (e.g., "THUNDER")

2. **LED Underglow Color** - RGB color for WS2812B LEDs│   ├── watchdog.py    # Safety system

3. **LCD Theme Color** - Used for racing graphics

│   └── utils.py       # Helper functions## 🛠️ Hardware Requirements

### LED Underglow States

├── controller/         # Python controller app

| State | Animation | Description |

|-------|-----------|-------------|│   └── controller_xbox.py| Component | Specification | Notes |

| **BOOT** | Flash robot color + red | Robot starting up |

| **NET_UP** | Solid robot color | WiFi connected, waiting for controller |├── scripts/           # Setup utilities|-----------|---------------|-------|

| **CLIENT_OK** | Flash robot color + green | Controller connected |

| **DRIVING** | Solid robot color | Driving (controller active) |│   ├── setup_hotspot.sh| **Microcontroller** | Raspberry Pi Pico W | RP2040 + CYW43439 Wi-Fi |

| **LINK_LOST** | Flash robot color + red | Connection lost |

│   └── install_lcd_driver.sh| **Platform** | Waveshare Pico-Go v2 | Includes motors, LCD, motor driver |

---

├── schematics/        # Hardware diagrams| **Motor Driver** | TB6612FNG | Dual H-bridge |

## 📂 Project Structure

└── docs/| **Display** | ST7789 240×240 LCD | 1.3" SPI display |

```

Pico-Go-LAN-Robot/    └── GUIDE.md       # 📖 Complete documentation| **Battery** | 7.4V Li-ion | 2S with protection |

├── firmware/              # MicroPython code for Pico W

│   ├── main.py           # Main entry point```| **Controller** | Xbox Controller | Wired or Bluetooth |

│   ├── config.py         # Robot profiles & settings ← EDIT THIS!

│   ├── wifi.py           # Wi-Fi connection manager| **Laptop** | Ubuntu 22.04+ | Hosts hotspot + controller app |

│   ├── motor.py          # Motor control & differential drive

│   ├── lcd_status.py     # LCD racing display---

│   ├── underglow.py      # WS2812B LED control

│   ├── watchdog.py       # 500ms safety watchdog### Pin Assignments

│   ├── ws_server.py      # UDP server

│   └── utils.py          # Helper functions## Documentation

├── controller/           # Python controller application

│   ├── controller_xbox.py**Motor Driver (TB6612FNG)**

│   ├── calibrate.py

│   └── requirements.txt**📖 [Complete Guide](docs/GUIDE.md)** - Everything you need:- PWMA: GP0, AIN1: GP1, AIN2: GP2

├── scripts/              # Utility scripts

│   ├── setup_hotspot.sh  # Ubuntu hotspot management- Hardware requirements and pin assignments- PWMB: GP3, BIN1: GP4, BIN2: GP5

│   └── install_lcd_driver.sh

├── docs/                 # Documentation- Detailed setup instructions- STBY: GP6

│   ├── GUIDE.md                 # Complete setup guide

│   ├── CALIBRATION.md           # Motor calibration- Software architecture and development

│   ├── RACING_LCD_DISPLAYS.md   # LCD design documentation

│   └── driver_experience_report.md- Network configuration**LCD (ST7789)**

└── schematics/           # Wiring diagrams

```- Troubleshooting guide- SCK: GP18, MOSI: GP19, DC: GP16



---- API reference- RST: GP20, CS: GP17, BL: GP21



## 🎮 Usage



### Starting the System------



1. **Power on robot** - Pico W boots and connects to PicoLAN

2. **Check LCD** - Displays robot name, IP address, and WiFi status

3. **Connect Xbox controller** to laptop (USB or Bluetooth)## Hardware Requirements## 📦 Software Requirements

4. **Run controller**:

   ```bash

   python3 controller/controller_xbox.py [robot_ip]

   ```| Component | Specification | Cost |### Firmware (Pico W)

5. **Watch underglow** - Changes from green flashing (CLIENT_OK) to solid color (DRIVING)

|-----------|---------------|------|- MicroPython 1.22+

### Safety Features

| Raspberry Pi Pico W | RP2040 + WiFi | $6 |- Built-in libraries: `uasyncio`, `network`, `machine`, `json`

- **Watchdog Timer**: Motors stop if no packet received for 500ms

- **Dead Zone**: 8% joystick dead zone to prevent drift| Waveshare Pico-Go v2 | Platform + motors + LCD | $25 |- Optional: `uwebsocket` (for WebSocket support)

- **Auto-reconnect**: Controller and firmware recover automatically

- **Visual Feedback**: LCD and LEDs show connection status| Li-ion Battery | 7.4V 2S 1000mAh+ | $15 |



---| Xbox Controller | USB or Bluetooth | $30-60 |### Controller (Laptop)



## 🔧 Configuration| **Total** | | **~$75-100** |- Python 3.11+



### Network Settings- pygame >= 2.5



Edit `firmware/config.py`:---- asyncio (built-in)

```python

WIFI_SSID = "PicoLAN"

WIFI_PASSWORD = "pico1234"

```## License---



Edit `scripts/setup_hotspot.sh` to match:

```bash

SSID="PicoLAN"MIT License## 🚀 Installation Guide

PASSWORD="pico1234"

```



### Control Parameters**Author:** Jeremy Dueck  ### Step 1: Laptop Setup



Edit `firmware/config.py`:**Organization:** St. Clair College Robotics Club  

```python

WATCHDOG_TIMEOUT_MS = 500  # Fail-safe timeout**Repository:** https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot```bash

MAX_SPEED = 1.0            # Speed multiplier

TURN_RATE = 0.8            # Steering sensitivity# Clone repository

DEAD_ZONE = 0.08           # Joystick dead zone

```---git clone https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot.git



### LED Underglow Brightnesscd Pico-Go-LAN-Robot



```python## Contributing

UNDERGLOW_BRIGHTNESS = 255  # 0-255 (always max brightness)

```# Install Python dependencies



---Contributions welcome! Please:pip install -r controller/requirements.txt



## 🧪 Testing1. Fork the repository



### Verify Firmware Upload2. Create a feature branch# Install system packages (Ubuntu)

```bash

# Connect via mpremote3. Make your changes and test thoroughlysudo apt update

mpremote connect /dev/ttyACM0

4. Submit a pull requestsudo apt install network-manager python3-pygame

# Check LCD - should show robot name and IP

```



### Test Motors (Wheels Off Ground!)For bugs and feature requests, open an issue on GitHub.# Setup hotspot

```bash

# In MicroPython REPL:sudo ./scripts/setup_hotspot.sh start

>>> import motor```

>>> m = motor.initialize()

>>> m.enable()### Step 2: Pico W Firmware

>>> m.test_sequence()

``````bash

# Install mpremote (MicroPython remote control)

### Test Networkpip install mpremote

```bash

# Ping robot# Connect Pico W via USB

ping 10.42.0.123# Upload all firmware files

cd firmware

# Check latencympremote connect /dev/ttyACM0 cp *.py :

./scripts/setup_hotspot.sh scan

```# Optional: Upload st7789 LCD driver if not included

# mpremote mip install st7789

---

# Reset to start

## 🐛 Troubleshootingmpremote reset

```

### Robot Won't Connect to WiFi

1. Check `firmware/config.py` - SSID and password must match hotspot### Step 3: Verify Connection

2. Verify hotspot is running: `./scripts/setup_hotspot.sh status`

3. Check serial output: `mpremote connect /dev/ttyACM0````bash

4. Pico W only supports 2.4 GHz WiFi (not 5 GHz)# Check hotspot status

./scripts/setup_hotspot.sh status

### Motors Don't Move

1. Check battery is charged (7.0-8.4V)# Scan for robot

2. Verify STBY pin (GP6) is HIGH./scripts/setup_hotspot.sh scan

3. Run motor test sequence (see Testing section)

4. Check motor connections# Monitor Pico serial output

mpremote connect /dev/ttyACM0

### Controller Won't Connect```

1. Verify robot IP from LCD display

2. Check both devices on same network---

3. Test connectivity: `ping <robot-ip>`

4. Ensure controller is detected: `ls /dev/input/js*`## 🎮 Usage



### LCD Shows Nothing### Starting the System

1. Check physical connection - reseat LCD connector

2. Verify 3.3V power to LCD1. **Power on the robot** - Pico W should boot and connect to PicoLAN

3. Test backlight (see docs/GUIDE.md)2. **Check LCD** - Should display IP address (e.g., 10.42.0.123)

3. **Connect Xbox controller** to laptop

### Underglow LEDs Not Working4. **Run controller app**:

1. Verify using GPIO 22 (not GPIO 6!)   ```bash

2. Check power to LED strip   python3 controller/controller_xbox.py [robot_ip]

3. Ensure data line connected properly   ```

4. Test with simple color: `underglow.set_color_all((255, 0, 0))`

### Controls

For detailed troubleshooting, see **[docs/GUIDE.md](docs/GUIDE.md)**.

- **Left Stick Y-axis**: Forward/Reverse throttle

---- **Left Stick X-axis**: Steering

- **START button**: Exit controller app

## 📚 Documentation

### Safety Features

- **[GUIDE.md](docs/GUIDE.md)** - Complete setup and development guide

- **[CALIBRATION.md](docs/CALIBRATION.md)** - Motor calibration procedures- **Watchdog Timer**: Automatically stops motors if no packet received for 200ms

- **[RACING_LCD_DISPLAYS.md](docs/RACING_LCD_DISPLAYS.md)** - LCD design documentation- **Dead Zone**: 8% joystick dead zone to prevent drift

- **[driver_experience_report.md](docs/driver_experience_report.md)** - Control feel analysis- **E-Stop Ready**: Software emergency stop capability

- **Connection Monitoring**: Auto-reconnect on link loss

---

---

## 🤝 Contributing

## 📂 Project Structure

Contributions welcome! This is an educational project from the St. Clair College Robotics Club.

```

1. Fork the repositoryPico-Go-LAN-Robot/

2. Create a feature branch├── firmware/              # MicroPython code for Pico W

3. Test thoroughly (see AGENTS.md for guidelines)│   ├── main.py           # Main entry point

4. Submit a pull request│   ├── config.py         # Pin definitions & settings

│   ├── wifi.py           # Wi-Fi connection manager

See **[AGENTS.md](AGENTS.md)** for coding standards and development practices.│   ├── motor.py          # Motor control & differential drive

│   ├── lcd_status.py     # LCD status display

---│   ├── watchdog.py       # Safety watchdog timer

│   ├── ws_server.py      # WebSocket/TCP server

## 📜 License│   └── utils.py          # Helper functions

├── controller/           # Python controller application

MIT License - See LICENSE file for details.│   ├── controller_xbox.py

│   └── requirements.txt

---├── scripts/              # Utility scripts

│   ├── setup_hotspot.sh  # Ubuntu hotspot management

## 👥 Credits│   └── install_lcd_driver.sh

├── docs/                 # Documentation

**Lead Engineer**: Jeremy Dueck  │   ├── QUICKSTART.md

**Organization**: St. Clair College Robotics Club  │   ├── HARDWARE.md

**Repository**: https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot│   ├── NETWORKING.md

│   └── TROUBLESHOOTING.md

---├── examples/             # Reference code from Waveshare

├── schematics/           # Wiring diagrams

## 🔗 Resources├── init.md               # Unified context file

└── README.md

- [Raspberry Pi Pico W Documentation](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)```

- [MicroPython Documentation](https://docs.micropython.org/)

- [Waveshare Pico-Go Wiki](https://www.waveshare.com/wiki/Pico-Go)---

- [TB6612FNG Datasheet](https://www.sparkfun.com/datasheets/Robotics/TB6612FNG.pdf)

## 🧪 Testing

---

### Hardware Test

**Happy Racing! 🏁🤖**```bash

# Connect via mpremote
mpremote connect /dev/ttyACM0

# In MicroPython REPL:
>>> import motor
>>> m = motor.initialize()
>>> m.enable()
>>> m.test_sequence()  # WARNING: Secure robot first!
```

### Network Test
```bash
# Ping robot
ping 10.42.0.123

# Check latency
./scripts/setup_hotspot.sh scan
```

### Controller Test
```bash
# Test without robot (will retry connection)
python3 controller/controller_xbox.py 10.42.0.999
# Verify controller input is detected
```

---

## 🔧 Configuration

### Changing Network Settings

Edit `firmware/config.py`:
```python
WIFI_SSID = "YourSSID"
WIFI_PASSWORD = "YourPassword"
```

Edit `setup_hotspot.sh`:
```bash
SSID="YourSSID"
PASSWORD="YourPassword"
```

### Adjusting Control Parameters

Edit `firmware/config.py`:
```python
WATCHDOG_TIMEOUT_MS = 200  # Fail-safe timeout
MAX_SPEED = 1.0            # Speed multiplier
TURN_RATE = 0.8            # Steering sensitivity
DEAD_ZONE = 0.08           # Joystick dead zone
```

---

## 📊 Performance Metrics

| Metric | Target | Typical |
|--------|--------|---------|
| Control Latency | ≤ 20 ms | 10-15 ms |
| Packet Rate | 30 Hz | 30 Hz |
| Wi-Fi Range | ≥ 10 m | 15-20 m |
| Fail-safe Response | ≤ 250 ms | 200 ms |
| Battery Runtime | ≥ 30 min | 45-60 min |

---

## 🐛 Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

**Common Issues:**

- **No LCD output** → Check SPI wiring and 3.3V power
- **Motors don't move** → Verify STBY pin is HIGH (GP6)
- **Wi-Fi won't connect** → Check SSID/password in config.py
- **Controller lag** → Reduce Wi-Fi interference, move closer

---

## 📚 Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - 5-minute setup walkthrough
- [Hardware Guide](docs/HARDWARE.md) - Wiring, assembly, power
- [Networking Guide](docs/NETWORKING.md) - LAN setup, troubleshooting
- [LCD Display Guide](docs/LCD_GUIDE.md) - Display states and indicators
- [Multi-Robot Setup](docs/MULTI_ROBOT_SETUP.md) - Running multiple robots
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Advanced development reference
- [Engineering Reference](docs/REFERENCE.md) - Complete technical specifications
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common problems & solutions

---

## 🤝 Contributing

Contributions welcome! This is an educational project from the St. Clair College Robotics Club.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📜 License

- **Firmware & Controller Code**: MIT License
- **Hardware Designs**: CERN-OHL-P (Permissive)
- **Documentation**: CC BY-SA 4.0

---

## 👥 Credits

**Lead Engineer**: Jeremy Dueck  
**Organization**: St. Clair College Robotics Club  
**Collaboration**: Optimotive Robotics Project

---

## 🔗 Resources

- [Raspberry Pi Pico W Documentation](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)
- [MicroPython Documentation](https://docs.micropython.org/)
- [Waveshare Pico-Go Wiki](https://www.waveshare.com/wiki/Pico-Go)
- [TB6612FNG Datasheet](https://www.sparkfun.com/datasheets/Robotics/TB6612FNG.pdf)

---

## 📧 Contact

Questions? Issues? Join the discussion:
- **GitHub Issues**: [Report a bug](https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot/issues)
- **Email**: robotics@stclaircollege.ca

---

**Happy Building! 🤖**
