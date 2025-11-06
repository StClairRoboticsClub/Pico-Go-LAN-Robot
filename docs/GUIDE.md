# Pico-Go LAN Robot - Complete Guide

**Real-time LAN-controlled robot using Raspberry Pi Pico W and Waveshare Pico-Go v2**

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Hardware](#hardware)
4. [Software Architecture](#software-architecture)
5. [Network Setup](#network-setup)
6. [Development](#development)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The **Pico-Go LAN Robot** is a teleoperated robot platform featuring:

- **Real-time control** over local Wi-Fi (no internet required)
- **Xbox controller** input at 30 Hz via TCP
- **Automatic fail-safe** - motors stop if connection lost > 200ms
- **Live status display** on ST7789 LCD with color-coded connection status
- **Modular architecture** - easy to extend and customize

Perfect for robotics education, sumo competitions, and R&D projects.

### System Architecture

```
[Xbox Controller] ──USB/Bluetooth──► [Laptop Controller]
                                           │
                                       Wi-Fi LAN
                                      (10.42.0.x)
                                           │
                                           ▼
                                    [Raspberry Pi Pico W]
                                           │
                                    [Motor Controller]
                                           │
                                       [Motors]
```

**Control Flow:**
1. Xbox controller input read at 30 Hz (pygame)
2. Commands sent via TCP to robot (JSON format)
3. Pico W receives and validates commands
4. Motor controller applies throttle/steering
5. Watchdog enforces 200ms safety timeout
6. LCD displays real-time connection status

---

## Quick Start

### Prerequisites
- Waveshare Pico-Go v2 with Raspberry Pi Pico W
- Ubuntu 22.04+ laptop with Wi-Fi
- Xbox controller (USB or Bluetooth)
- Charged 7.4V battery

### Step 1: Setup Laptop (2 minutes)

```bash
# Clone repository
git clone https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot.git
cd Pico-Go-LAN-Robot

# Install Python dependencies
pip install -r controller/requirements.txt

# Create Wi-Fi hotspot
sudo ./scripts/setup_hotspot.sh start
```

**Expected Output:**
```
✅ Hotspot started successfully!
Network Information:
  SSID:     PicoLAN
  Password: pico1234
  IP:       10.42.0.1
```

### Step 2: Configure & Flash Firmware (3 minutes)

```bash
# Install mpremote if not already installed
pip install mpremote

# Edit firmware/config.py and set your WiFi credentials
# WIFI_SSID = "PicoLAN"
# WIFI_PASSWORD = "pico1234"

# Connect Pico W via USB and upload firmware
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :
mpremote reset
```

**Watch for:** LCD shows "BOOT" → "NET_UP" → displays IP address

### Step 3: Run Controller (1 minute)

```bash
# Connect Xbox controller to laptop

# Run controller (replace with your robot's IP from LCD)
python3 controller/controller_xbox.py 10.42.0.123
```

**Expected Output:**
```
🤖 Pico-Go LAN Robot - Xbox Controller
Target Robot IP: 10.42.0.123:8765
✅ Controller connected: Xbox Wireless Controller
✅ Connected to robot!
🎮 CONTROLLER ACTIVE
```

### Controls

| Input | Action |
|-------|--------|
| Left Stick Y | Forward/Reverse |
| Left Stick X | Steering |
| START Button | Exit |

---

## Hardware

### Bill of Materials

| Component | Specification | Cost |
|-----------|---------------|------|
| Raspberry Pi Pico W | RP2040 + CYW43439 Wi-Fi | $6 |
| Waveshare Pico-Go v2 | Includes motors, LCD, driver | $25 |
| Li-ion Battery | 7.4V 2S 1000mAh+ | $15 |
| Xbox Controller | Wired or Bluetooth | $30-60 |
| **Total** | (excluding laptop) | **~$75-100** |

### Pin Assignments

**Motor Driver (TB6612FNG):**
- Motor A: PWMA=GP16, AIN1=GP18, AIN2=GP17
- Motor B: PWMB=GP21, BIN1=GP19, BIN2=GP20
- PWM Frequency: 1 kHz

**LCD (ST7789):**
- SPI: SCK=GP18, MOSI=GP19
- Control: DC=GP16, RST=GP20, CS=GP17, BL=GP21
- Resolution: 240×240 pixels

**Power Distribution:**
```
7.4V Battery ──► 5V Regulator ──► Pico W (VSYS)
             │                ──► Motor Driver (VCC)
             └──► Motor Driver (VM, direct) ──► Motors
```

### Electrical Budget

| Component | Typical | Peak |
|-----------|---------|------|
| Pico W MCU | 100 mA | 300 mA |
| LCD Backlight | 25 mA | 50 mA |
| Motors (both) | 600 mA | 3.0 A |
| **Total** | **725 mA** | **3.35 A** |

**Minimum battery:** 1000 mAh (30-45 min runtime)

---

## Software Architecture

### Firmware (Pico W - MicroPython)

**Core Modules:**
- `main.py` - Entry point, orchestrates all subsystems
- `config.py` - Hardware pins, network settings, constants
- `wifi.py` - WiFi connection management
- `ws_server.py` - TCP server for receiving commands
- `motor.py` - Motor control (TB6612FNG driver)
- `lcd_status.py` - LCD display with color-coded status
- `watchdog.py` - Safety system (200ms timeout)
- `utils.py` - Helper functions and classes

**Key Features:**
- `uasyncio` cooperative multitasking
- TCP server on port 8765 (JSON protocol)
- Automatic motor cutoff if no commands for 200ms
- mDNS hostname support (picogo1.local, picogo2.local)
- Real-time LCD status with connection quality indicators

### Controller (Laptop - Python 3.11+)

**Single Module:**
- `controller_xbox.py` - Xbox controller input via pygame, TCP client

**Key Features:**
- Reads Xbox controller at 30 Hz
- Applies deadzone (0.08) to joystick input
- Sends JSON commands: `{cmd, throttle, steer, seq}`
- Automatic reconnection on connection loss
- Robot discovery via mDNS or cached IP

### Communication Protocol

**TCP Socket (Port 8765):**
```json
{
  "cmd": "drive",
  "throttle": 0.75,
  "steer": -0.25,
  "seq": 12345
}
```

- `throttle`: -1.0 to 1.0 (reverse to forward)
- `steer`: -1.0 to 1.0 (left to right)
- `seq`: Sequence number for packet loss detection

---

## Network Setup

### Ubuntu Hotspot Configuration

The laptop creates a WiFi hotspot that the robot connects to.

**Default Settings:**
- SSID: `PicoLAN`
- Password: `pico1234`
- Laptop IP: `10.42.0.1`
- Robot IP: `10.42.0.x` (DHCP assigned)

**Hotspot Management:**
```bash
# Start hotspot
sudo ./scripts/setup_hotspot.sh start

# Check status
./scripts/setup_hotspot.sh status

# Stop hotspot
sudo ./scripts/setup_hotspot.sh stop

# Scan for connected devices
sudo ./scripts/setup_hotspot.sh scan
```

**Manual NetworkManager Setup:**
```bash
# Create hotspot
nmcli dev wifi hotspot ifname wlan0 ssid PicoLAN password "pico1234"

# Check connection
nmcli connection show PicoLAN

# Delete hotspot
nmcli connection delete PicoLAN
```

### Multi-Robot Setup

Each robot can have a unique ID for operating multiple robots on the same network.

**Configure Robot ID in `firmware/config.py`:**
```python
ROBOT_ID = 1  # Robot will be picogo1.local
ROBOT_ID = 2  # Robot will be picogo2.local
# etc.
```

**Connect to Specific Robot:**
```bash
python3 controller/controller_xbox.py picogo1  # By hostname
python3 controller/controller_xbox.py 10.42.0.123  # By IP
```

### LCD Status Display

The LCD shows connection status with color-coded backgrounds:

| Color | Status | Description |
|-------|--------|-------------|
| 🔵 Blue | BOOT | Robot starting up |
| 🟡 Yellow | NET_UP | Connected to WiFi, waiting for controller |
| 🟢 Green | CONNECTED | Good connection (<100ms between packets) |
| 🟡 Yellow | LAG | Connection lag (100-200ms) |
| 🔴 Red | TIMEOUT | Connection lost (>200ms) |

**Display Information:**
- IP address (for controller connection)
- RSSI signal strength
- Current throttle/steering values
- Connection quality

---

## Development

### Project Structure

```
Pico-Go-LAN-Robot/
├── firmware/              # MicroPython code for Pico W
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration
│   ├── wifi.py           # WiFi management
│   ├── ws_server.py      # TCP server
│   ├── motor.py          # Motor control
│   ├── lcd_status.py     # LCD display
│   ├── watchdog.py       # Safety system
│   └── utils.py          # Helper functions
├── controller/            # Python controller app
│   ├── controller_xbox.py
│   └── requirements.txt
├── scripts/              # Setup scripts
│   ├── setup_hotspot.sh  # WiFi hotspot management
│   └── install_lcd_driver.sh
├── schematics/           # Hardware diagrams
└── docs/                 # Documentation
```

### Building and Deploying

**Install Dependencies:**
```bash
# Laptop controller dependencies
pip install -r controller/requirements.txt

# MicroPython remote tool
pip install mpremote
```

**Deploy Firmware:**
```bash
# Upload all firmware files
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :

# Reset to run
mpremote reset

# View serial output
mpremote connect /dev/ttyACM0
```

**Test Motor Control:**
```bash
# Connect via serial
mpremote connect /dev/ttyACM0 exec "import motor; m = motor.initialize(); m.test_sequence()"
```

### Coding Guidelines

**Python Style:**
- Follow PEP 8
- Use type hints
- Google-style docstrings
- 4-space indentation

**MicroPython Firmware:**
- Keep functions small (<50 lines)
- Use `const()` for fixed values
- Minimize heap allocations in hot loops
- Use `uasyncio` for cooperative multitasking

**Naming Conventions:**
- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Git branches: `feature/description`

### Testing

**Controller Testing:**
```bash
# Dry run locally
python3 controller/controller_xbox.py 127.0.0.1
```

**Network Testing:**
```bash
# Check latency
ping -c 100 <robot-ip>

# Monitor connection
sudo tcpdump -i wlan0 port 8765
```

**Motor Testing:**
With wheels lifted, connect via serial:
```python
import motor
m = motor.initialize()
m.test_sequence()  # Runs through motor patterns
```

### Configuration

**WiFi Settings (`firmware/config.py`):**
```python
WIFI_SSID = "YourNetwork"
WIFI_PASSWORD = "YourPassword"
ROBOT_ID = 1  # Unique per robot
```

**Safety Parameters:**
```python
WATCHDOG_TIMEOUT_MS = 200  # Motor cutoff timeout
CONTROL_RATE_HZ = 30       # Expected packet rate
```

**Motor Parameters:**
```python
MOTOR_PWM_FREQ = 1000      # PWM frequency (Hz)
DEAD_ZONE = 0.08           # Joystick deadzone
MAX_SPEED = 1.0            # Speed multiplier
TURN_RATE = 0.8            # Steering sensitivity
```

---

## Troubleshooting

### Robot Won't Power On

**Check:**
- Battery voltage (should be 7.0-8.4V for 2S Li-ion)
- Power connections tight
- 5V regulator output (4.9-5.1V)
- Try USB power to isolate issue

**Test:**
```bash
mpremote connect /dev/ttyACM0
# If REPL appears, MCU is fine - check power circuit
```

### LCD Shows Nothing

**Solutions:**
1. Check physical connection - reseat LCD connector
2. Test backlight:
   ```python
   from machine import Pin
   bl = Pin(21, Pin.OUT)
   bl.value(1)  # Should see backlight
   ```
3. Verify pin mappings in `config.py`
4. Install driver: `mpremote mip install st7789`

### Motors Don't Move

**Check:**
1. Motors connected to correct terminals
2. Battery charged
3. Try test sequence:
   ```bash
   mpremote connect /dev/ttyACM0 exec "import motor; m = motor.initialize(); m.test_sequence()"
   ```
4. Verify pin assignments in `config.py`

### WiFi Won't Connect

**Solutions:**
1. Verify hotspot is running:
   ```bash
   ./scripts/setup_hotspot.sh status
   ```
2. Check credentials in `firmware/config.py` match hotspot
3. Verify 2.4 GHz WiFi (Pico W doesn't support 5 GHz)
4. Check serial output:
   ```bash
   mpremote connect /dev/ttyACM0
   ```
5. Try manual connection:
   ```python
   import network
   wlan = network.WLAN(network.STA_IF)
   wlan.active(True)
   wlan.connect("PicoLAN", "pico1234")
   ```

### Controller Won't Connect

**Check:**
1. Robot IP correct (check LCD display)
2. Both on same network
3. Port 8765 not blocked
4. Test connectivity: `ping <robot-ip>`
5. Try IP instead of hostname

**Find Robot IP:**
```bash
# Method 1: Check LCD screen
# Method 2: Serial monitor
mpremote connect /dev/ttyACM0 exec "import network; wlan = network.WLAN(network.STA_IF); print('IP:', wlan.ifconfig()[0])"

# Method 3: Network scan
nmap -sn 10.42.0.0/24
```

### Motors Stop Unexpectedly

**Cause:** Watchdog timeout (no commands received for 200ms)

**Solutions:**
1. Check controller is running and connected
2. Verify network stability: `ping -c 100 <robot-ip>`
3. Check for packet loss or high latency
4. Ensure controller update rate matches (30 Hz)
5. If persistent, increase timeout in `config.py`:
   ```python
   WATCHDOG_TIMEOUT_MS = 300  # Increase if needed
   ```

### High Latency / Lag

**Solutions:**
1. Move closer to laptop (improve WiFi signal)
2. Check RSSI on LCD (should be > -70 dBm)
3. Reduce WiFi interference (move away from other networks)
4. Check for background network activity on laptop
5. Use 2.4 GHz only (disable 5 GHz on laptop WiFi)

### Xbox Controller Not Detected

**Check:**
1. Controller connected (USB or paired via Bluetooth)
2. Test with `jstest /dev/input/js0`
3. Install pygame: `pip install pygame`
4. Try different USB port
5. Check controller in system settings

**Test Controller:**
```bash
# List joysticks
ls -l /dev/input/js*

# Test input
jstest /dev/input/js0
```

### Serial Connection Issues

**Solutions:**
1. Check USB cable (try different cable)
2. Verify device: `ls /dev/ttyACM*`
3. Check permissions:
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in
   ```
4. Try `screen` instead of mpremote:
   ```bash
   screen /dev/ttyACM0 115200
   ```

---

## Additional Resources

### Useful Commands

**Firmware Development:**
```bash
# Upload single file
mpremote connect /dev/ttyACM0 cp firmware/motor.py :motor.py

# Run REPL
mpremote connect /dev/ttyACM0 repl

# Execute Python code
mpremote connect /dev/ttyACM0 exec "print('Hello')"

# View filesystem
mpremote connect /dev/ttyACM0 ls

# Remove file
mpremote connect /dev/ttyACM0 rm motor.py
```

**Network Diagnostics:**
```bash
# Check WiFi interface
ip addr show wlan0

# Monitor traffic
sudo tcpdump -i wlan0 -n port 8765

# Scan network
nmap -sn 10.42.0.0/24

# Check route table
ip route show
```

**System Monitoring:**
```bash
# Controller resource usage
top -p $(pgrep -f controller_xbox.py)

# Network statistics
ifconfig wlan0

# Check USB devices
lsusb
```

### References

- [MicroPython Documentation](https://docs.micropython.org/)
- [Raspberry Pi Pico W Datasheet](https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf)
- [Waveshare Pico-Go Wiki](https://www.waveshare.com/wiki/Pico-Go)
- [TB6612FNG Motor Driver Datasheet](https://www.sparkfun.com/datasheets/Robotics/TB6612FNG.pdf)
- [ST7789 LCD Driver](https://github.com/devbis/st7789py_mpy)

---

## License

MIT License - See LICENSE file for details.

**Author:** Jeremy Dueck  
**Organization:** St. Clair College Robotics Club  
**Repository:** https://github.com/StClairRoboticsClub/Pico-Go-LAN-Robot
