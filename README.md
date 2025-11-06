# 🤖 Pico-Go LAN Robot

**Real-time LAN-controlled sumo robot using Raspberry Pi Pico W and Waveshare Pico-Go v2**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MicroPython](https://img.shields.io/badge/MicroPython-1.22+-green.svg)](https://micropython.org/)

---

## 📘 Overview

The **Pico-Go LAN Robot** is a teleoperated robot platform built on the Waveshare Pico-Go v2 chassis, featuring:

- **Real-time control** over local Wi-Fi (no internet required)
- **Xbox controller** input at 30 Hz via WebSocket/TCP
- **Automatic fail-safe** - motors stop if connection lost > 200ms
- **Live status display** on ST7789 LCD
- **Modular architecture** - easy to extend and customize

Perfect for robotics education, competitions, and R&D projects.

---

## 🎯 Quick Start

### 1. Setup Ubuntu Hotspot (Laptop)

```bash
# Create the Wi-Fi hotspot
sudo ./scripts/setup_hotspot.sh start

# Verify it's running
./scripts/setup_hotspot.sh status
```

### 2. Flash Firmware (Pico W)

```bash
# Install MicroPython on Pico W (if not already installed)
# Download from: https://micropython.org/download/RPI_PICO_W/

# Upload firmware files
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :
mpremote reset
```

### 3. Run Controller (Laptop)

```bash
# Install dependencies
pip install -r controller/requirements.txt

# Connect Xbox controller via USB or Bluetooth

# Run controller (update robot IP if needed)
python3 controller/controller_xbox.py 10.42.0.123
```

---

## 🧩 System Architecture

```
┌─────────────────┐
│ Xbox Controller │
└────────┬────────┘
         │ USB/Bluetooth
         ▼
┌─────────────────────┐      Wi-Fi LAN       ┌──────────────────┐
│ Laptop Controller   │◄───────────────────►│ Raspberry Pi     │
│ • Python 3.11       │   10.42.0.x:8765    │ Pico W           │
│ • pygame            │                      │ • MicroPython    │
│ • asyncio           │                      │ • Motor Control  │
└─────────────────────┘                      │ • LCD Display    │
                                              │ • Safety Systems │
                                              └──────────────────┘
```

---

## 🛠️ Hardware Requirements

| Component | Specification | Notes |
|-----------|---------------|-------|
| **Microcontroller** | Raspberry Pi Pico W | RP2040 + CYW43439 Wi-Fi |
| **Platform** | Waveshare Pico-Go v2 | Includes motors, LCD, motor driver |
| **Motor Driver** | TB6612FNG | Dual H-bridge |
| **Display** | ST7789 240×240 LCD | 1.3" SPI display |
| **Battery** | 7.4V Li-ion | 2S with protection |
| **Controller** | Xbox Controller | Wired or Bluetooth |
| **Laptop** | Ubuntu 22.04+ | Hosts hotspot + controller app |

### Pin Assignments

**Motor Driver (TB6612FNG)**
- PWMA: GP0, AIN1: GP1, AIN2: GP2
- PWMB: GP3, BIN1: GP4, BIN2: GP5
- STBY: GP6

**LCD (ST7789)**
- SCK: GP18, MOSI: GP19, DC: GP16
- RST: GP20, CS: GP17, BL: GP21

---

## 📦 Software Requirements

### Firmware (Pico W)
- MicroPython 1.22+
- Built-in libraries: `uasyncio`, `network`, `machine`, `json`
- Optional: `uwebsocket` (for WebSocket support)

### Controller (Laptop)
- Python 3.11+
- pygame >= 2.5
- asyncio (built-in)

---

## 🚀 Installation Guide

### Step 1: Laptop Setup

```bash
# Clone repository
git clone https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot.git
cd Pico-Go-LAN-Robot

# Install Python dependencies
pip install -r controller/requirements.txt

# Install system packages (Ubuntu)
sudo apt update
sudo apt install network-manager python3-pygame

# Setup hotspot
sudo ./scripts/setup_hotspot.sh start
```

### Step 2: Pico W Firmware

```bash
# Install mpremote (MicroPython remote control)
pip install mpremote

# Connect Pico W via USB
# Upload all firmware files
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :

# Optional: Upload st7789 LCD driver if not included
# mpremote mip install st7789

# Reset to start
mpremote reset
```

### Step 3: Verify Connection

```bash
# Check hotspot status
./scripts/setup_hotspot.sh status

# Scan for robot
./scripts/setup_hotspot.sh scan

# Monitor Pico serial output
mpremote connect /dev/ttyACM0
```

---

## 🎮 Usage

### Starting the System

1. **Power on the robot** - Pico W should boot and connect to PicoLAN
2. **Check LCD** - Should display IP address (e.g., 10.42.0.123)
3. **Connect Xbox controller** to laptop
4. **Run controller app**:
   ```bash
   python3 controller/controller_xbox.py [robot_ip]
   ```

### Controls

- **Left Stick Y-axis**: Forward/Reverse throttle
- **Left Stick X-axis**: Steering
- **START button**: Exit controller app

### Safety Features

- **Watchdog Timer**: Automatically stops motors if no packet received for 200ms
- **Dead Zone**: 8% joystick dead zone to prevent drift
- **E-Stop Ready**: Software emergency stop capability
- **Connection Monitoring**: Auto-reconnect on link loss

---

## 📂 Project Structure

```
Pico-Go-LAN-Robot/
├── firmware/              # MicroPython code for Pico W
│   ├── main.py           # Main entry point
│   ├── config.py         # Pin definitions & settings
│   ├── wifi.py           # Wi-Fi connection manager
│   ├── motor.py          # Motor control & differential drive
│   ├── lcd_status.py     # LCD status display
│   ├── watchdog.py       # Safety watchdog timer
│   ├── ws_server.py      # WebSocket/TCP server
│   └── utils.py          # Helper functions
├── controller/           # Python controller application
│   ├── controller_xbox.py
│   └── requirements.txt
├── scripts/              # Utility scripts
│   ├── setup_hotspot.sh  # Ubuntu hotspot management
│   └── install_lcd_driver.sh
├── docs/                 # Documentation
│   ├── QUICKSTART.md
│   ├── HARDWARE.md
│   ├── NETWORKING.md
│   └── TROUBLESHOOTING.md
├── examples/             # Reference code from Waveshare
├── schematics/           # Wiring diagrams
├── init.md               # Unified context file
└── README.md
```

---

## 🧪 Testing

### Hardware Test
```bash
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
