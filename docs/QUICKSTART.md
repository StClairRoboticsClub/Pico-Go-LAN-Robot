# Quick Start Guide - Pico-Go LAN Robot

## ⚡ 5-Minute Setup

### Prerequisites
- ✅ Waveshare Pico-Go v2 with Raspberry Pi Pico W
- ✅ Ubuntu 22.04+ laptop with Wi-Fi
- ✅ Xbox controller (USB or Bluetooth)
- ✅ Charged 7.4V battery

---

## Step 1: Setup Laptop (2 minutes)

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

---

## Step 2: Flash Firmware (2 minutes)

```bash
# Install mpremote if not already installed
pip install mpremote

# Connect Pico W via USB

# Upload firmware
cd firmware
mpremote connect /dev/ttyACM0 cp *.py :

# Reset Pico
mpremote reset
```

**Watch for:**
- LCD shows "BOOT" → "NET_UP" → displays IP address

---

## Step 3: Run Controller (1 minute)

```bash
# Connect Xbox controller to laptop

# Run controller (replace with your robot's IP from LCD)
python3 controller/controller_xbox.py 10.42.0.123
```

**Expected Output:**
```
🤖 Pico-Go LAN Robot - Xbox Controller
============================================================
Target Robot IP: 10.42.0.123:8765
============================================================

✅ Controller connected: Xbox Wireless Controller
🔌 Connecting to robot at 10.42.0.123:8765...
✅ Connected to robot!

============================================================
🎮 CONTROLLER ACTIVE
============================================================
```

---

## 🎮 Controls

| Input | Action |
|-------|--------|
| Left Stick Y | Forward/Reverse |
| Left Stick X | Steering |
| START Button | Exit |

---

## ✅ Verification Checklist

- [ ] Hotspot shows as active: `./scripts/setup_hotspot.sh status`
- [ ] Robot LCD displays IP address
- [ ] Laptop can ping robot: `ping 10.42.0.123`
- [ ] Controller detects Xbox controller
- [ ] Controller connects to robot
- [ ] Robot responds to joystick input

---

## 🐛 Common Quick Fixes

**Robot won't connect to Wi-Fi**
```bash
# Restart hotspot
sudo ./scripts/setup_hotspot.sh restart
# Power cycle robot
```

**Controller can't connect**
```bash
# Verify robot IP on LCD
# Ping robot: ping 10.42.0.123
# Try with updated IP: python3 controller/controller_xbox.py <actual_ip>
```

**No controller detected**
```bash
# Check USB connection
ls /dev/input/js*
# Should show /dev/input/js0

# Test controller
jstest /dev/input/js0
```

---

## 📚 Next Steps

- Read [README.md](../README.md) for detailed documentation
- See [HARDWARE.md](HARDWARE.md) for pin assignments
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for issues

---

## 🚀 You're Ready!

Drive your robot and have fun! Remember:
- **Safety**: Motors stop automatically if connection lost >200ms
- **Range**: Stay within ~15m for best performance
- **Battery**: ~45-60 min runtime

**Happy robotics! 🤖**
