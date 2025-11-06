# Multi-Robot LAN Setup Guide

## Overview
This guide explains how to run multiple Pico-Go robots on the same network with unique identities.

## How It Works

### Robot Configuration
Each robot has a **ROBOT_ID** in `firmware/config.py` that gives it a unique hostname:
- Robot 1 → `picogo1.local` 
- Robot 2 → `picogo2.local`
- Robot 3 → `picogo3.local`
- etc.

### Controller Usage
The controller can connect to robots by:
1. **Hostname**: `python3 controller/controller_xbox.py picogo1`
2. **Full hostname**: `python3 controller/controller_xbox.py picogo2.local`
3. **IP address**: `python3 controller/controller_xbox.py 10.145.146.98`

## Setup for Multiple Robots

### Step 1: Configure Each Robot

For **Robot 1**, edit `firmware/config.py`:
```python
ROBOT_ID = 1  # This robot is picogo1.local
```

For **Robot 2**, edit `firmware/config.py`:
```python
ROBOT_ID = 2  # This robot is picogo2.local
```

For **Robot 3**, edit `firmware/config.py`:
```python
ROBOT_ID = 3  # This robot is picogo3.local
```

### Step 2: Upload Firmware

For each robot, connect via USB and upload:
```bash
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :
mpremote connect /dev/ttyACM0 exec "import machine; machine.soft_reset()"
```

### Step 3: Connect Controller

Once all robots are powered on and connected to WiFi:

**Connect to Robot 1:**
```bash
python3 controller/controller_xbox.py picogo1
```

**Connect to Robot 2:**
```bash
python3 controller/controller_xbox.py picogo2
```

**Connect to Robot 3:**
```bash
python3 controller/controller_xbox.py picogo3
```

## Network Independence

### mDNS (hostname-based discovery)
- **Pros**: Works on any network automatically
- **Cons**: Requires mDNS/Bonjour support (available on most networks)
- **Use when**: Moving between different WiFi networks frequently

### IP Address (direct connection)
- **Pros**: Always works, no DNS needed
- **Cons**: Need to find IP each time (check LCD or serial output)
- **Use when**: mDNS not available or debugging

## Finding Robot IP Address

If hostname resolution fails, find the robot's IP:

**Method 1 - Check LCD Screen:**
The robot displays its IP address on the LCD after connecting to WiFi.

**Method 2 - Serial Monitor:**
```bash
mpremote connect /dev/ttyACM0 exec "import network; wlan = network.WLAN(network.STA_IF); print('IP:', wlan.ifconfig()[0])"
```

**Method 3 - Network Scan:**
```bash
nmap -sn 192.168.1.0/24  # Adjust subnet to match your network
```

## Troubleshooting

### Hostname not resolving
1. Check mDNS is enabled: `MDNS_ENABLED = True` in `config.py`
2. Verify network supports mDNS (most home networks do)
3. Try `.local` suffix: `picogo1.local` instead of `picogo1`
4. Fall back to IP address

### Multiple robots same ID
If two robots have the same `ROBOT_ID`, they'll have hostname conflicts. Ensure each robot has a unique ID.

### Robot not on network
1. Check LCD shows IP address (not "LINK LOST")
2. Verify WiFi credentials in `config.py` match your network
3. Check robot is in range of WiFi
4. Try serial monitor to see boot messages

## Example Multi-Robot Competition Setup

**Scenario**: 4 robots competing on same WiFi network

1. Program robots with IDs 1-4
2. Upload firmware to each
3. Connect controllers:
   - Laptop 1: `python3 controller/controller_xbox.py picogo1`
   - Laptop 2: `python3 controller/controller_xbox.py picogo2`
   - Laptop 3: `python3 controller/controller_xbox.py picogo3`  
   - Laptop 4: `python3 controller/controller_xbox.py picogo4`

Each controller will only communicate with its assigned robot, even though all are on the same network and port 8765.

## Advanced: Custom Hostnames

To use custom names instead of `picogo1`, edit `config.py`:

```python
ROBOT_ID = 1
MDNS_HOSTNAME = "redteam"  # Robot will be redteam.local
```

or

```python
ROBOT_ID = 2
MDNS_HOSTNAME = "blueteam"  # Robot will be blueteam.local
```

Then connect with:
```bash
python3 controller/controller_xbox.py redteam
python3 controller/controller_xbox.py blueteam
```
