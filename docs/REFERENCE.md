# 🤖 Pico-Go LAN Robot — Engineering Reference v2  
### Raspberry Pi Pico W (MicroPython) • Waveshare Pico-Go v2 • Ubuntu 22.04

---

## 📘 Overview

The **Pico-Go LAN Robot** is a LAN-controlled sumo robot built on the **Waveshare Pico-Go v2** platform using a **Raspberry Pi Pico W** running **MicroPython**.  
It operates entirely over a **local Wi-Fi network** created by an **Ubuntu laptop**, which also serves as the control host and development workstation.

This guide consolidates **all technical, hardware, software, and networking information** required for engineering, reproduction, and maintenance of the system.

---

## 🎯 Core Objectives

- Enable **real-time LAN teleoperation** of the Pico-Go robot (no Internet dependency).  
- Stream **Xbox controller input** at 30 Hz using **WebSockets** for low-latency control.  
- Implement an automatic **fail-safe stop** if no valid packet received within 200 ms.  
- Display robot connection and system state on the **ST7789 LCD**.  
- Provide a **modular, extensible** architecture suitable for education and R&D.

---

## 🧩 System Overview

```
[Xbox Controller]
     │  (USB/Bluetooth)
     ▼
[Laptop Controller App]
  Python 3.11 + asyncio + websockets + pygame
     │  Wi-Fi LAN (hosted on Ubuntu)
     ▼
[Raspberry Pi Pico W]
  MicroPython WebSocket server on port 8765
  PWM motor control + LCD status + watchdog safety
```

---

## 🌐 Network Architecture (Ubuntu Hotspot)

| Device | Role | Function | IP Range |
|--------|------|-----------|----------|
| Laptop | Access Point + Controller | Hosts Wi-Fi hotspot, DHCP server, and controller app | 10.42.0.1 |
| Pico W | Robot Client | Connects to SSID, runs WebSocket server | 10.42.0.x |

**LAN Procedure**

1. Create hotspot: `PicoLAN`, password `pico1234`.  
2. Pico W connects (STA mode) → obtains DHCP IP.  
3. Controller app connects to `ws://10.42.0.x:8765`.  
4. Packets stream at 30 Hz; watchdog enforces stop if no packets > 200 ms.  
5. LCD displays state transitions (`BOOT`, `NET_UP`, `LINK_LOST`).

---

## ⚙️ Hardware Architecture

| Subsystem | Component | Notes / Pin Map |
|------------|------------|----------------|
| MCU | Raspberry Pi Pico W | Dual-core RP2040 + CYW43439 Wi-Fi |
| Motor Driver | TB6612FNG | PWMA GP0, AIN1 GP1, AIN2 GP2 / PWMB GP3, BIN1 GP4, BIN2 GP5 / STBY GP6 |
| LCD | ST7789 1.3″ SPI (240×240) | SCK GP18, MOSI GP19, DC GP16, RST GP20, CS GP17, BL GP21 |
| Power | 7.4 V Li-ion → 5 V regulator | Add 470 µF bulk capacitor across 5 V rail |
| Sensors | (optional) HC-SR04 | Trig GP10, Echo GP11 |
| E-Stop | Software only | Stops after 200 ms no-link |

---

## ⚡ Electrical Budget

| Component | Qty | Voltage | Current (typ) | Current (max) | Notes |
|------------|-----|----------|----------------|----------------|-------|
| Pico W MCU | 1 | 5V USB | 100 mA | 300 mA | Wi-Fi active peak |
| TB6612FNG | 1 | 5V | 20 mA | 1.2 A per channel | Motor current dependent |
| Motors (TT gear) | 2 | 6V | 300 mA | 1.5 A stall each | Check gearbox ratio |
| LCD ST7789 | 1 | 3.3V | 25 mA | 50 mA | Backlight heavy draw |
| Regulator (5V) | 1 | 7.4V in | 1.5 A | — | Recommend LM2596 or equivalent |
| **Total Estimated Draw** |  |  | 745 mA | 3.6 A peak | Requires 2A+ 5V regulator |

---

## 🧠 Firmware Environment

| Parameter | Value |
|------------|--------|
| Language | MicroPython 1.22+ |
| IDE | VS Code + Copilot + mpremote |
| Scheduler | `uasyncio` |
| Network | `network.WLAN(STA_IF)` |
| WebSocket | `uwebsocket` (port 8765) |
| LCD Driver | `st7789py_mpy` |
| PWM Frequency | 20 kHz |
| Timeout | 200 ms |

---

## 🗂️ Firmware Directory Structure

```
/firmware
 ├── main.py
 ├── config.py
 ├── wifi.py
 ├── ws_server.py
 ├── motor.py
 ├── lcd_status.py
 ├── watchdog.py
 ├── utils.py
 └── st7789.py
```

| Module | Purpose |
|---------|----------|
| main.py | Initializes Wi-Fi, LCD, WebSocket, watchdog. |
| config.py | Defines pins, SSID, timeouts. |
| wifi.py | Connects to Ubuntu hotspot + handles reconnects. |
| ws_server.py | WebSocket async server, JSON parsing. |
| motor.py | Motor class; throttle/steer → PWM outputs. |
| lcd_status.py | Updates LCD with system states. |
| watchdog.py | Monitors packet timing, stops on timeout. |
| utils.py | Helpers for clamping, logging, etc. |

---

## 🔄 Firmware State Machine

| State | Entry Condition | Behavior | Exit Condition |
|--------|-----------------|-----------|----------------|
| BOOT | Power-on | LCD “BOOT” | Wi-Fi connected |
| NET_UP | Wi-Fi OK | Show IP + RSSI | WebSocket connect |
| CLIENT_OK | WS connected | Await commands | First `drive` packet |
| DRIVING | Receiving packets | PWM @ 30 Hz | Timeout |
| LINK_LOST | Timeout > 200 ms | Motors off, LCD red | Packet resumes |
| E-STOP | Commanded stop | Latch off | Manual reset |

---

## 📜 Firmware Pseudocode (Main Components)

### `main.py`
```python
async def main():
    lcd.set_state("BOOT")
    ip = await wifi.connect()
    lcd.set_state("NET_UP", ip=ip)
    ws_server.start(on_packet=handle_packet)
    while True:
        await watchdog.check()
        lcd.update()
        await asyncio.sleep_ms(50)
```

### `motor.py`
```python
def drive(throttle, steer):
    left = clamp(throttle + steer, -1, 1)
    right = clamp(throttle - steer, -1, 1)
    set_pwm(left_motor, left)
    set_pwm(right_motor, right)
```

### `watchdog.py`
```python
async def check():
    if ticks_diff(ticks_ms(), last_rx) > TIMEOUT_MS:
        motor.stop()
        lcd.set_state("LINK_LOST")
```

---

## 📡 JSON Command Protocol

**Client → Robot**
```json
{
  "t_ms": 1730774000000,
  "seq": 42,
  "cmd": "drive",
  "axes": { "throttle": 0.6, "steer": -0.2 },
  "hb_ms": 100
}
```

**Robot → Client**
```json
{
  "seq_ack": 42,
  "state": "DRIVING",
  "rssi": -57,
  "vbat": 7.9
}
```

---

## 💻 Controller Application (Ubuntu)

| Component | Function |
|------------|-----------|
| Language | Python 3.11+ |
| Libraries | `pygame`, `asyncio`, `websockets` |
| Input | Xbox controller (SDL) |
| Output | JSON packets @ 30 Hz |
| Reconnect | Auto retry every 1 s |
| Dead Zone | ±0.08 |

**Install**
```bash
sudo apt install python3-pip python3-pygame -y
pip install websockets asyncio
```

**Run**
```bash
python3 controller_xbox.py
```

---

## 🌐 Ubuntu Hotspot Setup

**CLI Method**
```bash
nmcli dev wifi hotspot ifname wlan0 ssid PicoLAN password "pico1234"
```
**Verify**
```bash
ip addr show wlan0
```

---

## 🧾 Dependency Summary

| Layer | Dependency | Source |
|--------|-------------|--------|
| Firmware | MicroPython 1.22 | official.uf2 |
| | `uasyncio`, `uwebsocket`, `machine`, `network`, `json` | built-in |
| | `st7789py_mpy` | Waveshare GitHub |
| Controller | Python 3.11+ | system |
| | `pygame >= 2.5`, `websockets >= 12` | pip |

---

## 🧰 Electrical Safety and Design Notes

- Ensure 5V regulator rated ≥ 2A peak.  
- Include 470 µF + 100 nF capacitors on motor rail.  
- Use 22 AWG wires for motor power.  
- Add reverse-polarity diode across battery input.  
- For compliance testing, add physical E-Stop header inline with motor power.  

---

## 🧪 Testing and Telemetry Logging

| Test | Purpose | Procedure |
|------|----------|------------|
| Bench test | Validate Wi-Fi and LCD | USB power, check IP |
| Ping test | Network latency | `ping 10.42.0.x` |
| Drive test | Motion control | Run controller script |
| Fail-safe | Watchdog | Disconnect Wi-Fi |
| Reconnect | Resume | Re-enable Wi-Fi |

**Telemetry Example**
```csv
seq,rtt_ms,throttle,steer,state
1,15,0.55,-0.20,DRIVING
2,14,0.58,-0.21,DRIVING
3,300,0.00,0.00,LINK_LOST
```

Use `matplotlib` for visualization:
```python
import pandas as pd, matplotlib.pyplot as plt
df = pd.read_csv("telemetry.csv")
plt.plot(df['seq'], df['rtt_ms']); plt.show()
```

---

## ⚙️ Performance Metrics

| Metric | Target | Rationale |
|---------|---------|-----------|
| Latency | ≤ 20 ms | Smooth response |
| Timeout | 200 ms | Safety cutoff |
| Rate | 30 Hz | Human-like control |
| Range | ≥ 10 m | Indoor lab use |
| Runtime | ≥ 30 min | Battery cycle |

---

## 🧩 Troubleshooting

| Symptom | Possible Cause | Fix |
|----------|----------------|-----|
| No LCD output | Missing 3.3V or miswired SPI | Check pins + driver |
| Wi-Fi not connecting | Wrong SSID or password | Verify `config.py` |
| Motors twitch but no movement | STBY not enabled | Pull STBY high |
| Laggy control | Weak Wi-Fi signal | Move closer to AP |
| No controller input | SDL not detecting device | Check `pygame.joystick` list |
| Pico unresponsive | Flash corruption | Re-flash `.uf2` firmware |

---

## 🛠️ Version Roadmap

| Version | Milestone | Status |
|----------|------------|---------|
| **v1.0** | Tele-op control, watchdog, LCD UI | ✅ Current |
| **v2.0** | UDP discovery, telemetry dashboard | ☐ Planned |
| **v3.0** | ROS2 integration + OTA updates | ☐ Future |

---

## 📜 Licensing

- **Firmware & Controller Code:** MIT License  
- **Hardware Designs (PCB, Wiring):** CERN-OHL-P (Permissive)  
- **Documentation:** CC BY-SA 4.0  

---

## 🧩 Repository Layout

```
pico-go-lan-robot/
 ├── firmware/
 ├── controller/
 ├── docs/
 ├── schematics/
 ├── LICENSE
 └── README.md
```

---

## 📚 Summary

This guide provides **everything required to replicate, test, and extend** the Pico-Go LAN Robot.  
It unifies the software, hardware, and networking stack in a single, self-contained reference suitable for educational, club, and R&D use.

**Lead Engineer:** Jeremy Dueck  
**Organization:** St. Clair College Robotics Club / Optimotive Collaborative Project  
**License:** MIT / CERN-OHL-P / CC BY-SA  
**Version:** v2.0 Draft — Engineering Reference

---
