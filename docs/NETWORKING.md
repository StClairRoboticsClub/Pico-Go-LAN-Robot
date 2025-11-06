# Networking Guide - Pico-Go LAN Robot

## 🌐 Network Architecture

```
┌──────────────────────────────────────────────────────┐
│             Ubuntu Laptop (Hotspot Host)             │
│  ┌────────────────────────────────────────────────┐  │
│  │     NetworkManager Hotspot (PicoLAN)           │  │
│  │     IP: 10.42.0.1                              │  │
│  │     DHCP Server: 10.42.0.50 - 10.42.0.150     │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │     Controller Application                      │  │
│  │     Port: 8765 (client)                        │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
                          │
                      Wi-Fi LAN
                          │
┌──────────────────────────────────────────────────────┐
│           Raspberry Pi Pico W (Robot)                │
│  ┌────────────────────────────────────────────────┐  │
│  │     Wi-Fi Client (STA Mode)                    │  │
│  │     DHCP Assigned: 10.42.0.x                   │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │     TCP Server                                  │  │
│  │     Port: 8765 (server)                        │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## 🔧 Ubuntu Hotspot Setup

### Method 1: Using Setup Script (Recommended)

```bash
# Start hotspot
sudo ./setup_hotspot.sh start

# Check status
./setup_hotspot.sh status

# Stop hotspot
sudo ./setup_hotspot.sh stop

# Scan for connected devices
sudo ./setup_hotspot.sh scan
```

### Method 2: Manual Setup via NetworkManager

```bash
# Create hotspot
nmcli dev wifi hotspot ifname wlan0 ssid PicoLAN password "pico1234"

# Check connection
nmcli connection show PicoLAN

# Verify IP address
ip addr show wlan0
# Should show: inet 10.42.0.1/24

# Delete hotspot
nmcli connection delete PicoLAN
```

### Method 3: GUI Method

1. Open **Settings** → **Wi-Fi**
2. Click **☰** menu → **Turn On Wi-Fi Hotspot**
3. Configure:
   - Network Name: `PicoLAN`
   - Password: `pico1234`
   - Security: WPA2
4. Click **Turn On**

---

## 📡 Network Configuration

### Default Settings

| Parameter | Value | Configurable In |
|-----------|-------|-----------------|
| SSID | PicoLAN | `setup_hotspot.sh`, `firmware/config.py` |
| Password | pico1234 | `setup_hotspot.sh`, `firmware/config.py` |
| Laptop IP | 10.42.0.1 | Auto (NetworkManager) |
| Robot IP Range | 10.42.0.50-150 | Auto (DHCP) |
| TCP Port | 8765 | `firmware/config.py`, `controller_xbox.py` |
| Wi-Fi Band | 2.4 GHz | `setup_hotspot.sh` |

### Changing Network Settings

**On Laptop** (`setup_hotspot.sh`):
```bash
SSID="MyRobotLAN"
PASSWORD="mypassword123"
```

**On Robot** (`firmware/config.py`):
```python
WIFI_SSID = "MyRobotLAN"
WIFI_PASSWORD = "mypassword123"
WEBSOCKET_PORT = 8765
```

**On Controller** (`controller/controller_xbox.py`):
```python
DEFAULT_ROBOT_IP = "10.42.0.123"  # Update after checking robot IP
ROBOT_PORT = 8765
```

---

## 🔍 Finding Robot IP Address

### Method 1: LCD Display (Best)

Robot displays IP on LCD after connecting:
```
NET UP
10.42.0.123
```

### Method 2: Serial Monitor

Connect via USB and monitor output:
```bash
mpremote connect /dev/ttyACM0
# Look for: "Connected! IP: 10.42.0.123"
```

### Method 3: Network Scan

```bash
# Using setup script
sudo ./setup_hotspot.sh scan

# Manual nmap scan
sudo nmap -sn 10.42.0.0/24

# ARP scan
sudo arp-scan --interface=wlan0 --localnet
```

### Method 4: Check DHCP Leases

```bash
# View NetworkManager DHCP leases
cat /var/lib/NetworkManager/dnsmasq-wlan0.leases

# Or use nmcli
nmcli device show wlan0 | grep IP4
```

---

## 📊 Network Diagnostics

### Connectivity Testing

```bash
# Ping robot
ping -c 5 10.42.0.123

# Check latency
ping -c 100 10.42.0.123 | tail -1

# Test TCP connection
nc -zv 10.42.0.123 8765

# Monitor packets (tcpdump)
sudo tcpdump -i wlan0 host 10.42.0.123
```

### Signal Strength

**On Robot** (MicroPython REPL):
```python
import network
wlan = network.WLAN(network.STA_IF)
print(f"RSSI: {wlan.status('rssi')} dBm")
```

**On Laptop**:
```bash
# Check connected devices signal
sudo iw dev wlan0 station dump
```

### Bandwidth Testing

```bash
# Install iperf3
sudo apt install iperf3

# On laptop (server mode)
iperf3 -s

# On robot - not easily possible on Pico W
# Alternative: measure actual control packet throughput in controller app
```

---

## 🔒 Security Considerations

### Current Setup (Basic)

- **Encryption**: WPA2-PSK (shared password)
- **Isolation**: No internet access (air-gapped)
- **Authentication**: Password only

### Recommendations

1. **Change default password** from `pico1234`
2. **Use strong password** (12+ chars, mixed case, numbers)
3. **Disable when not in use** - turn off hotspot
4. **Physical security** - robot operates in controlled environment

### Advanced Security (Future)

- Client certificate authentication
- VPN tunnel for encrypted comms
- MAC address filtering on hotspot
- Custom encryption layer in application protocol

---

## ⚡ Performance Optimization

### Latency Reduction

1. **Reduce Physical Distance**: Keep laptop ≤10m from robot
2. **Minimize Interference**: Avoid 2.4 GHz devices (Bluetooth, microwaves)
3. **Clear Line of Sight**: Reduce obstacles between laptop and robot
4. **Disable Power Saving**: 
   ```bash
   sudo iw dev wlan0 set power_save off
   ```

### Throughput Optimization

1. **Control Packet Rate**: Default 30 Hz is optimal
   - Too fast: Unnecessary CPU load
   - Too slow: Jerky control
2. **JSON Minimization**: Already compact, no further optimization needed
3. **TCP Nagle Disable**: Already disabled in asyncio streams

### Connection Stability

1. **Fixed IP for Robot** (optional):
   ```bash
   # Add to NetworkManager config
   nmcli connection modify PicoLAN ipv4.addresses "10.42.0.123/24"
   ```

2. **Increase Wi-Fi TX Power** (if supported):
   ```bash
   sudo iw dev wlan0 set txpower fixed 2000  # 20 dBm
   ```

3. **Monitor Connection**:
   ```bash
   watch -n 1 'ping -c 1 -W 1 10.42.0.123 | tail -1'
   ```

---

## 🐛 Network Troubleshooting

### Issue: Robot Won't Connect to Hotspot

**Symptoms**: Robot LCD shows "BOOT" but never "NET UP"

**Checks**:
1. Verify hotspot is active: `./setup_hotspot.sh status`
2. Check SSID/password in `firmware/config.py`
3. Verify Pico W (not regular Pico): Look for Wi-Fi chip
4. Check serial output: `mpremote connect /dev/ttyACM0`
5. Manually test Wi-Fi:
   ```python
   # In MicroPython REPL
   import network
   wlan = network.WLAN(network.STA_IF)
   wlan.active(True)
   wlan.scan()  # Should list "PicoLAN"
   ```

**Solutions**:
- Re-flash MicroPython firmware
- Verify no typos in SSID/password
- Try different Wi-Fi channel in `setup_hotspot.sh`

---

### Issue: Controller Can't Connect to Robot

**Symptoms**: Controller shows "Connection failed"

**Checks**:
1. Ping robot: `ping 10.42.0.123`
2. Verify robot IP on LCD
3. Test TCP port: `nc -zv 10.42.0.123 8765`
4. Check firewall: 
   ```bash
   sudo ufw status
   # If active, allow port: sudo ufw allow 8765
   ```

**Solutions**:
- Update robot IP in controller command
- Restart robot (power cycle)
- Check robot serial for errors

---

### Issue: High Latency (>50ms)

**Symptoms**: Laggy control, delayed response

**Checks**:
```bash
# Measure latency
ping -c 100 10.42.0.123 | grep avg
# Should be <20 ms average

# Check signal strength
sudo iw dev wlan0 station dump | grep signal
# Should be >-60 dBm
```

**Solutions**:
- Move laptop closer to robot
- Reduce Wi-Fi interference (turn off Bluetooth)
- Change Wi-Fi channel to less congested one:
  ```bash
  # Edit setup_hotspot.sh
  CHANNEL="6"  # Try 1, 6, or 11
  ```
- Disable power saving: `sudo iw dev wlan0 set power_save off`

---

### Issue: Frequent Disconnections

**Symptoms**: Connection drops, watchdog timeout frequently

**Checks**:
```bash
# Monitor connection
watch -n 0.5 'ping -c 1 -W 1 10.42.0.123'

# Check laptop power settings
cat /sys/module/iwlwifi/parameters/power_save  # Should be N
```

**Solutions**:
- Ensure laptop plugged in (not on battery)
- Disable Wi-Fi power management:
  ```bash
  sudo iw dev wlan0 set power_save off
  ```
- Check for USB power issues (robot side):
  - Use powered USB hub or external battery

---

## 📈 Performance Metrics

### Expected Performance

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Ping Latency | <15 ms | <30 ms | >50 ms |
| Signal Strength | >-50 dBm | >-65 dBm | <-70 dBm |
| Packet Loss | 0% | <1% | >5% |
| Control Rate | 30 Hz | 25-30 Hz | <20 Hz |

### Measuring Performance

**Controller Statistics**:
The controller app prints statistics every second:
```
📊 Packets: 300 | Rate: 30.1 Hz | T: +0.75 | S: -0.20
```

**Custom Telemetry** (add to controller):
```python
# In controller app
latencies = []
start = time.time()

# In send loop
send_time = time.time()
# ... send packet ...
# ... receive ack ...
rtt = (time.time() - send_time) * 1000
latencies.append(rtt)

# Print stats
avg_latency = sum(latencies) / len(latencies)
print(f"Average RTT: {avg_latency:.1f} ms")
```

---

## 🔬 Advanced Topics

### Packet Structure

**Controller → Robot** (Drive Command):
```json
{
  "t_ms": 1730774000000,
  "seq": 42,
  "cmd": "drive",
  "axes": {
    "throttle": 0.6,
    "steer": -0.2
  }
}
```

**Robot → Controller** (Acknowledgment):
```json
{
  "seq_ack": 42,
  "state": "DRIVING",
  "motor_enabled": true,
  "packets_received": 300
}
```

### Protocol Alternatives

**WebSocket** (future enhancement):
- Lower latency than TCP
- Binary frame support
- Requires `uwebsocket` library on Pico

**UDP** (not recommended):
- Lower latency but unreliable
- Packet loss problematic for safety-critical control
- No built-in ordering

---

## 🔗 Additional Resources

- [NetworkManager Hotspot Documentation](https://networkmanager.dev/)
- [MicroPython Network Module](https://docs.micropython.org/en/latest/library/network.html)
- [Wi-Fi Troubleshooting Guide](https://help.ubuntu.com/community/WifiDocs/WiFiHowTo)
- [TCP/IP Performance Tuning](https://www.kernel.org/doc/html/latest/networking/scaling.html)
