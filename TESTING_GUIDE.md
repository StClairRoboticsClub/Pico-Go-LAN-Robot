# Testing Guide - Post-Flash Verification

## ✅ Firmware Successfully Flashed

All firmware files have been uploaded to the robot. Now let's test the features.

## 🔍 Step-by-Step Testing

### 1. Check Robot Boot Sequence

**Watch the LCD and LED underglow:**

1. **BOOT State** (Purple LED flash)
   - LCD should show: Robot name, ID, "RACE ROBOT" text
   - LED: Flashing between robot color and RED

2. **NET_UP State** (Blue LED, solid robot color)
   - LCD should show: Robot IP address
   - LED: Solid robot color (no flash)
   - **Note the IP address displayed!**

3. **CLIENT_OK State** (When controller connects)
   - LED: **Flashing between robot color and ORANGE** ⚠️ (NEW FIX!)
   - LCD: Shows "CLIENT OK" or connection status

4. **DRIVING State** (When driving)
   - LED: Solid robot color (no flash)
   - LCD: Shows robot name with unique graphic (THUNDER=lightning, BLITZ=speed lines, etc.)

### 2. Test Robot Discovery

```bash
# From the project directory
python3 controller/controller_xbox.py
```

**Expected behavior:**
- Controller scans network and finds robot
- Discovery response includes:
  - Robot ID
  - Hostname
  - IP address
  - **Calibration data** ⚠️ (NEW!)
  - Robot color

### 3. Test Calibration System

**During connection:**
- Controller automatically requests calibration
- You should see: `✅ Calibration loaded: trim=+0.000, L=1.00, R=1.00`

**Test calibration tool:**
```bash
python3 controller/calibrate.py <robot_ip>
```

**Expected:**
- Can adjust steering trim with D-Pad Up/Down
- Can adjust motor balance with D-Pad Left/Right and LB/RB
- Can save calibration with A button
- Robot applies calibration to motor commands

### 4. Test LED Color Changes

**Watch the underglow LEDs during connection:**

1. **Before connection:** Solid robot color (NET_UP state)
2. **During connection (CLIENT_OK):** **Robot color + ORANGE flash** ⚠️ (FIXED!)
3. **After connection (DRIVING):** Solid robot color

### 5. Test LCD Screen Transitions

**Verify LCD shows:**
- Boot screen with robot name
- NET_UP screen with IP address
- Drive screen with:
  - Robot name at top
  - Unique graphic based on robot name:
    - THUNDER: Lightning bolt
    - BLITZ: Speed lines
    - NITRO: Flames
    - TURBO: Spinning pattern
    - SPEED: Arrows

### 6. Test Motor Control

**Drive the robot and verify:**
- Motors respond to controller input
- Steering trim is applied (if calibrated)
- Motor balance is applied (if calibrated)
- Watchdog stops motors if connection lost

## 🐛 Troubleshooting

### Robot Not Found in Discovery

1. **Check WiFi connection:**
   - Phone hotspot must be on: `DevNet-2.4G`
   - Password: `DevPass**99`
   - Must be 2.4 GHz (Pico W doesn't support 5 GHz)

2. **Check robot LCD:**
   - Should show IP address in NET_UP state
   - If stuck on BOOT, check serial output

3. **Check network:**
   - Laptop must be on same network as robot
   - Try manual connection: `python3 controller/controller_xbox.py <robot_ip>`

### Calibration Not Working

1. **Check serial output:**
   ```bash
   mpremote connect /dev/ttyACM0
   ```
   - Look for calibration request/response messages

2. **Verify calibration commands:**
   - Check for "get_calibration" and "set_calibration" in logs

### LED Colors Wrong

1. **Check underglow.py:**
   - CLIENT_OK should flash ORANGE (255, 140, 0)
   - Not GREEN (that was the bug we fixed)

2. **Verify state transitions:**
   - BOOT → NET_UP → CLIENT_OK → DRIVING

## 📊 Expected Test Results

✅ **Discovery:** Robot responds with calibration data  
✅ **Calibration:** Controller requests and receives calibration  
✅ **LED:** CLIENT_OK shows robot color + ORANGE flash  
✅ **LCD:** Shows robot name and unique graphic on drive screen  
✅ **Motors:** Respond correctly with calibration applied  
✅ **UDP:** All communication uses UDP (low latency)

## 🎯 Quick Test Command

```bash
# Test discovery and calibration
python3 -c "
import socket, json, time
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.settimeout(2.0)
sock.sendto(json.dumps({'cmd': 'discover'}).encode(), ('255.255.255.255', 8765))
data, addr = sock.recvfrom(1024)
resp = json.loads(data.decode())
print('Robot:', resp.get('hostname'), 'at', addr[0])
print('Calibration:', resp.get('calibration', 'MISSING!'))
"
```

---

**Ready to test!** Start with checking the LCD for the IP address, then run the controller.

