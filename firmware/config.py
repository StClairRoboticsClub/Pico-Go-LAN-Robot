"""
Pico-Go LAN Robot - Configuration Module
========================================
Hardware pin definitions, network settings, and system constants.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

# ============================================================================
# NETWORK CONFIGURATION
# ============================================================================

WIFI_SSID = "DevNet-2.4G"  # Phone hotspot
WIFI_PASSWORD = "DevPass**99"  # Phone hotspot password
WIFI_TIMEOUT_MS = 15000  # 15 seconds to connect
WIFI_RETRY_DELAY_MS = 5000  # 5 seconds between retries

WEBSOCKET_PORT = 8765
WEBSOCKET_HOST = "0.0.0.0"  # Listen on all interfaces

# Robot ID Configuration - for multiple robots on same network
# Change this to a unique number for each robot (1, 2, 3, etc.)
ROBOT_ID = 1

# Robot Name - Cool racing names to spark interest!
# Change for each robot to give them personality
ROBOT_NAMES = {
    1: "THUNDER",
    2: "BLITZ",
    3: "NITRO",
    4: "TURBO",
    5: "SPEED"
}
ROBOT_NAME = ROBOT_NAMES.get(ROBOT_ID, f"RACER-{ROBOT_ID}")

# mDNS Configuration - allows connection via hostname instead of IP
MDNS_HOSTNAME = f"picogo{ROBOT_ID}"  # Robot will be accessible as picogo1.local, picogo2.local, etc.
MDNS_ENABLED = True

# ============================================================================
# SAFETY & TIMING
# ============================================================================

WATCHDOG_TIMEOUT_MS = 500  # Stop motors if no packet for 500ms (increased from 200ms)
CONTROL_RATE_HZ = 30  # Expected control packet rate
MAIN_LOOP_MS = 50  # Main loop update rate

# LCD Configuration
LCD_ENABLED = True  # Re-enabled now that motors are fixed
LCD_UPDATE_INTERVAL_MS = 100  # Update LCD every 100ms (10 Hz)

# ============================================================================
# MOTOR DRIVER (TB6612FNG) - Pin Definitions
# ============================================================================

# Motor A (Left) - Waveshare Pico-Go v2 Pinout
PIN_MOTOR_A_PWM = 16  # PWMA
PIN_MOTOR_A_IN1 = 18  # AIN1
PIN_MOTOR_A_IN2 = 17  # AIN2

# Motor B (Right) - Waveshare Pico-Go v2 Pinout
PIN_MOTOR_B_PWM = 21  # PWMB
PIN_MOTOR_B_IN1 = 19  # BIN1
PIN_MOTOR_B_IN2 = 20  # BIN2

# Standby - Not used on Waveshare Pico-Go v2
PIN_MOTOR_STBY = None  # No STBY pin on this platform

# Motor parameters - Waveshare uses 1kHz
MOTOR_PWM_FREQ = 1000   # 1 kHz PWM frequency (per Waveshare example)
MOTOR_MAX_DUTY = 65535  # 16-bit PWM resolution (0xFFFF)

# ============================================================================
# LCD (ST7789) - Pin Definitions
# ============================================================================

PIN_LCD_SCK = 18   # SPI Clock
PIN_LCD_MOSI = 19  # SPI Data Out
PIN_LCD_DC = 16    # Data/Command
PIN_LCD_RST = 20   # Reset
PIN_LCD_CS = 17    # Chip Select
PIN_LCD_BL = 21    # Backlight

LCD_WIDTH = 240
LCD_HEIGHT = 240
LCD_ROTATION = 0  # 0, 90, 180, or 270 degrees

# ============================================================================
# OPTIONAL SENSORS
# ============================================================================

# Ultrasonic Sensor (HC-SR04)
PIN_ULTRASONIC_TRIG = 10
PIN_ULTRASONIC_ECHO = 11

# ============================================================================
# UNDERGLOW LEDs (WS2812B)
# ============================================================================

PIN_UNDERGLOW = 6  # GPIO pin for WS2812B data line (Waveshare Pico-Go v2)
UNDERGLOW_NUM_LEDS = 4  # Number of LEDs on Waveshare Pico-Go v2
UNDERGLOW_ENABLED = True  # Enable/disable underglow
UNDERGLOW_BRIGHTNESS = 255  # Full brightness (0-255) - always 100%

# Robot colors (RGB) - unique color per robot ID for identification
ROBOT_COLORS = {
    1: (255, 140, 0),    # THUNDER - Dark Orange (yellow-orange)
    2: (0, 191, 255),    # BLITZ - Deep Sky Blue
    3: (255, 69, 0),     # NITRO - Orange Red
    4: (50, 205, 50),    # TURBO - Lime Green
    5: (138, 43, 226)    # SPEED - Blue Violet
}
ROBOT_COLOR = ROBOT_COLORS.get(ROBOT_ID, (255, 255, 255))  # Default to white

# ============================================================================
# POWER & ELECTRICAL
# ============================================================================

BATTERY_VOLTAGE_PIN = 26  # ADC0 for battery voltage monitoring (optional)
LOW_BATTERY_THRESHOLD = 6.5  # Volts - warning threshold

# ============================================================================
# DRIVE PARAMETERS
# ============================================================================

DEAD_ZONE = 0.08  # Joystick dead zone threshold
MAX_SPEED = 1.0   # Maximum motor speed multiplier
TURN_RATE = 0.8   # Steering sensitivity multiplier

# ============================================================================
# DEBUG & LOGGING
# ============================================================================

DEBUG_MODE = True  # Enable/disable debug prints
LOG_TELEMETRY = False  # Log telemetry to file (not implemented yet)

# ============================================================================
# SYSTEM STATES
# ============================================================================

STATE_BOOT = "BOOT"
STATE_NET_UP = "NET_UP"
STATE_CLIENT_OK = "CLIENT_OK"
STATE_DRIVING = "DRIVING"
STATE_LINK_LOST = "LINK_LOST"
STATE_E_STOP = "E_STOP"
