# Example Code

This directory contains **reference code from Waveshare** for the Pico-Go v2 platform.

## Contents

### `PicoGo_Code_V2/`

Original example code provided by Waveshare for the Pico-Go v2 robot platform. These examples demonstrate:

- Motor control (Motor.py)
- LCD display (ST7789.py)
- Line tracking sensors (TRSensor.py, Line-Tracking.py)
- Infrared sensors (Infrared_obstacle_Avoidance.py)
- Ultrasonic sensors (Ultrasonic_Ranging.py, Ultrasonic_Obstacle_Avoidance.py)
- Battery voltage monitoring (Battery_Voltage.py)
- LED control (ws2812.py)
- IR remote control (IRremote.py)
- Bluetooth functionality (bluetooth.py)

### Purpose

These files are kept for **reference only** and are **not used by the main robot firmware**.

The actual robot firmware is in `/firmware/` and is a complete rewrite with:
- Modular architecture
- Async/await patterns
- LAN-based control
- Safety systems (watchdog)
- Real-time telemetry

### Usage

You can reference these examples if you want to:
- Understand Waveshare's original pin assignments
- See alternative approaches to motor/sensor control
- Port additional sensors to the main firmware
- Learn about the hardware capabilities

### Firmware Files Included

The `uf2/` subdirectory contains official MicroPython firmware for:
- Raspberry Pi Pico (RPI_PICO-20250415-v1.25.0.uf2)
- Raspberry Pi Pico 2 (RPI_PICO2-20250415-v1.25.0.uf2)

**Note**: For Pico W, download firmware from [micropython.org/download/RPI_PICO_W/](https://micropython.org/download/RPI_PICO_W/)

---

**Do not modify these files**—they are historical reference from the manufacturer.

For the actual robot code, see `/firmware/`.
