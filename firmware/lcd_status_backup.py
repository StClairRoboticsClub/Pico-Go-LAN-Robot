"""
Pico-Go LAN Robot - LCD Status Display Module
=============================================
ST7789 LCD display interface for system status visualization.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT

Features:
- Color-coded connection status (Red/Yellow/Green)
- IP address display
- Real-time debug metrics
- Throttle/steer visualization
"""

from machine import Pin, SPI
import time
from config import (
    PIN_LCD_SCK, PIN_LCD_MOSI, PIN_LCD_DC,
    PIN_LCD_RST, PIN_LCD_CS, PIN_LCD_BL,
    LCD_WIDTH, LCD_HEIGHT, LCD_ROTATION,
    STATE_BOOT, STATE_NET_UP, STATE_CLIENT_OK,
    STATE_DRIVING, STATE_LINK_LOST, STATE_E_STOP
)
from utils import debug_print

# Try to import display drivers (ST7735 for 1.14" or ST7789 for 1.3")
LCD_AVAILABLE = False
LCD_DRIVER = None

try:
    import st7735 as LCD_DRIVER
    LCD_AVAILABLE = True
    LCD_TYPE = "ST7735"
    debug_print("ST7735 driver loaded (1.14\" display)")
except ImportError:
    try:
        import st7789 as LCD_DRIVER
        LCD_AVAILABLE = True
        LCD_TYPE = "ST7789"
        debug_print("ST7789 driver loaded (1.3\" display)")
    except ImportError:
        LCD_AVAILABLE = False
        debug_print("No LCD driver found - display disabled", force=True)

# Color definitions (RGB565 format)
COLOR_BLACK = 0x0000
COLOR_WHITE = 0xFFFF
COLOR_RED = 0xF800
COLOR_GREEN = 0x07E0
COLOR_BLUE = 0x001F
COLOR_YELLOW = 0xFFE0
COLOR_ORANGE = 0xFD20
COLOR_CYAN = 0x07FF
COLOR_MAGENTA = 0xF81F
COLOR_DARK_GREEN = 0x03E0
COLOR_DARK_RED = 0x7800


class LCDStatus:
    """
    LCD status display manager with color-coded connection status.
    
    Connection Colors:
    - Red: Disconnected
    - Yellow: Intermittent/Lag
    - Green: Connected
    """
    
    def __init__(self):
        """Initialize LCD display."""
        self.display = None
        self.current_state = None
        self.ip_address = None
        self.rssi = None
        self.packets_received = 0
        self.last_packet_time = 0
        self.throttle = 0
        self.steer = 0
        self.latency_ms = 0
        
        if not LCD_AVAILABLE:
            debug_print("LCD disabled - driver not available")
            return
            
        try:
            # Initialize SPI
            self.spi = SPI(
                0,
                baudrate=40000000,
                polarity=0,
                phase=0,
                sck=Pin(PIN_LCD_SCK),
                mosi=Pin(PIN_LCD_MOSI)
            )
            
            # Initialize control pins
            self.dc = Pin(PIN_LCD_DC, Pin.OUT)
            self.rst = Pin(PIN_LCD_RST, Pin.OUT)
            self.cs = Pin(PIN_LCD_CS, Pin.OUT)
            self.bl = Pin(PIN_LCD_BL, Pin.OUT)
            
            # Initialize display based on driver type
            if LCD_TYPE == "ST7735":
                # ST7735 1.14" display (135x240) - Waveshare Pico-Go default
                self.display = LCD_DRIVER.ST7735(
                    self.spi,
                    self.dc,
                    self.rst,
                    self.cs
                )
                self.actual_width = 135
                self.actual_height = 240
            else:
                # ST7789 1.3" display (240x240)
                self.display = LCD_DRIVER.ST7789(
                    self.spi,
                    LCD_WIDTH,
                    LCD_HEIGHT,
                    reset=self.rst,
                    dc=self.dc,
                    cs=self.cs,
                    backlight=self.bl,
                    rotation=LCD_ROTATION
                )
                self.actual_width = LCD_WIDTH
                self.actual_height = LCD_HEIGHT
            
            # Initialize display
            self.backlight_on()
            self.clear(COLOR_BLACK)
            
            debug_print("LCD initialized successfully", force=True)
            
        except Exception as e:
            debug_print(f"LCD initialization error: {e}", force=True)
            self.display = None
    
    def backlight_on(self):
        """Turn backlight on."""
        self.bl.value(1)
    
    def backlight_off(self):
        """Turn backlight off."""
        self.bl.value(0)
    
    def clear(self, color=COLOR_BLACK):
        """
        Clear the display with specified color.
        
        Args:
            color: RGB565 color value
        """
        if self.display:
            self.display.fill(color)
    
    def set_state(self, state, **kwargs):
        """
        Update display to show current system state.
        
        Args:
            state: System state (from config.py)
            **kwargs: Additional state-specific parameters
        """
        self.current_state = state
        
        if state == STATE_BOOT:
            self._show_boot()
        elif state == STATE_NET_UP:
            self.ip_address = kwargs.get('ip', None)
            self.rssi = kwargs.get('rssi', None)
            self._show_net_up()
        elif state == STATE_CLIENT_OK:
            self._show_client_ok()
        elif state == STATE_DRIVING:
            throttle = kwargs.get('throttle', 0)
            steer = kwargs.get('steer', 0)
            self._show_driving(throttle, steer)
        elif state == STATE_LINK_LOST:
            self._show_link_lost()
        elif state == STATE_E_STOP:
            self._show_e_stop()
    
    def _show_boot(self):
        """Display boot screen."""
        debug_print("LCD: BOOT")
        if not self.display:
            return
        
        # Dark blue background
        self.clear(COLOR_BLUE)
        
        # Title
        self._draw_text_centered("PICO-GO", 60, COLOR_WHITE, scale=3)
        self._draw_text_centered("ROBOT", 100, COLOR_CYAN, scale=2)
        self._draw_text_centered("Booting...", 160, COLOR_WHITE, scale=1)
    
    def _show_net_up(self):
        """Display network connected screen with IP and RSSI."""
        debug_print(f"LCD: NET_UP - IP: {self.ip_address}")
        if not self.display:
            return
        
        # Yellow background (waiting for controller)
        self.clear(COLOR_YELLOW)
        
        # Title
        self._draw_text_centered("NETWORK", 20, COLOR_BLACK, scale=2)
        self._draw_text_centered("CONNECTED", 50, COLOR_BLACK, scale=2)
        
        # IP Address (most important!)
        self._draw_text("IP:", 10, 100, COLOR_BLACK, scale=2)
        if self.ip_address:
            self._draw_text(str(self.ip_address), 10, 130, COLOR_BLUE, scale=2)
        
        # RSSI if available
        if self.rssi:
            rssi_text = f"RSSI: {self.rssi} dBm"
            self._draw_text(rssi_text, 10, 180, COLOR_BLACK, scale=1)
        
        # Waiting message
        self._draw_text_centered("Waiting for", 210, COLOR_BLACK, scale=1)
        self._draw_text_centered("controller...", 225, COLOR_BLACK, scale=1)
    
    def _show_client_ok(self):
        """Display client connected screen."""
        debug_print("LCD: CLIENT_OK")
        if not self.display:
            return
        
        # Green background - connected!
        self.clear(COLOR_GREEN)
        
        # Title
        self._draw_text_centered("CONTROLLER", 60, COLOR_WHITE, scale=2)
        self._draw_text_centered("CONNECTED", 90, COLOR_WHITE, scale=2)
        
        # Ready indicator
        self._draw_text_centered("READY", 140, COLOR_YELLOW, scale=3)
    
    def _show_driving(self, throttle, steer):
        """
        Display driving state with live metrics.
        
        Args:
            throttle: Current throttle value (-1.0 to 1.0)
            steer: Current steering value (-1.0 to 1.0)
        """
        if not self.display:
            return
        
        # Store values
        self.throttle = throttle
        self.steer = steer
        self.last_packet_time = time.ticks_ms()
        self.packets_received += 1
        
        # Determine connection quality
        bg_color = self._get_connection_color()
        
        # Clear with connection status color
        self.clear(bg_color)
        
        # Title
        text_color = COLOR_WHITE if bg_color != COLOR_YELLOW else COLOR_BLACK
        self._draw_text_centered("DRIVING", 10, text_color, scale=2)
        
        # IP in corner (small)
        if self.ip_address:
            self._draw_text(str(self.ip_address), 5, 225, text_color, scale=1)
        
        # Throttle display
        self._draw_text("THR:", 10, 50, text_color, scale=2)
        throttle_str = f"{throttle:+.2f}"
        self._draw_text(throttle_str, 90, 50, COLOR_CYAN, scale=2)
        self._draw_bar(10, 80, 220, 20, throttle, COLOR_CYAN)
        
        # Steering display
        self._draw_text("STR:", 10, 115, text_color, scale=2)
        steer_str = f"{steer:+.2f}"
        self._draw_text(steer_str, 90, 115, COLOR_MAGENTA, scale=2)
        self._draw_bar(10, 145, 220, 20, steer, COLOR_MAGENTA)
        
        # Debug metrics
        self._draw_text(f"PKT: {self.packets_received}", 10, 180, text_color, scale=1)
        
        if self.rssi:
            self._draw_text(f"RSSI: {self.rssi}", 10, 195, text_color, scale=1)
        
        if self.latency_ms > 0:
            self._draw_text(f"LAT: {self.latency_ms}ms", 140, 180, text_color, scale=1)
    
    def _show_link_lost(self):
        """Display link lost warning - RED background."""
        debug_print("LCD: LINK LOST", force=True)
        if not self.display:
            return
        
        # Red background - disconnected!
        self.clear(COLOR_RED)
        
        # Warning
        self._draw_text_centered("CONNECTION", 70, COLOR_WHITE, scale=2)
        self._draw_text_centered("LOST!", 100, COLOR_YELLOW, scale=3)
        
        # Info
        self._draw_text_centered("Motors Stopped", 160, COLOR_WHITE, scale=1)
        
        # Last known values
        self._draw_text(f"Last THR: {self.throttle:+.2f}", 10, 190, COLOR_WHITE, scale=1)
        self._draw_text(f"Last STR: {self.steer:+.2f}", 10, 205, COLOR_WHITE, scale=1)
        
        if self.ip_address:
            self._draw_text(str(self.ip_address), 10, 225, COLOR_WHITE, scale=1)
    
    def _show_e_stop(self):
        """Display emergency stop screen - RED background."""
        debug_print("LCD: E-STOP", force=True)
        if not self.display:
            return
        
        # Red background - emergency!
        self.clear(COLOR_RED)
        
        # Large warning
        self._draw_text_centered("EMERGENCY", 80, COLOR_WHITE, scale=2)
        self._draw_text_centered("STOP!", 110, COLOR_YELLOW, scale=4)
        
        # Instructions
        self._draw_text_centered("Reset Required", 180, COLOR_WHITE, scale=1)
    
    def _get_connection_color(self):
        """
        Determine connection status color based on packet timing.
        
        Returns:
            Color code (RED, YELLOW, or GREEN)
        """
        if self.last_packet_time == 0:
            return COLOR_RED  # Never received
        
        # Check time since last packet
        elapsed = time.ticks_diff(time.ticks_ms(), self.last_packet_time)
        
        if elapsed > 200:  # Timeout threshold
            return COLOR_RED  # Disconnected
        elif elapsed > 100:  # Getting laggy
            return COLOR_YELLOW  # Intermittent
        else:
            return COLOR_GREEN  # Good connection
    
    def _draw_text(self, text, x, y, color, scale=2):
        """
        Draw text at specific position.
        
        Args:
            text: Text to draw
            x: X coordinate
            y: Y coordinate
            color: Text color
            scale: Text size multiplier
        """
        if not self.display:
            return
        
        try:
            self.display.text(text, x, y, color)
        except Exception as e:
            debug_print(f"Text draw error: {e}")
    
    def _draw_text_centered(self, text, y, color, scale=2):
        """
        Draw text centered horizontally.
        
        Args:
            text: Text to draw
            y: Y coordinate
            color: Text color
            scale: Text size multiplier
        """
        if not self.display:
            return
        
        # Approximate character width (8 pixels per char in default font)
        char_width = 8
        text_width = len(text) * char_width
        x = (LCD_WIDTH - text_width) // 2
        
        self._draw_text(text, x, y, color, scale)
    
    def _draw_bar(self, x, y, width, height, value, color):
        """
        Draw a horizontal bar representing a value from -1.0 to +1.0.
        
        Args:
            x: X coordinate
            y: Y coordinate
            width: Bar width
            height: Bar height
            value: Value (-1.0 to +1.0)
            color: Bar color
        """
        if not self.display:
            return
        
        try:
            # Draw outline
            self.display.rect(x, y, width, height, COLOR_WHITE)
            
            # Calculate filled portion
            center_x = x + width // 2
            
            if abs(value) < 0.01:  # Dead zone
                # Just draw center line
                self.display.vline(center_x, y, height, COLOR_WHITE)
            else:
                # Draw filled bar from center
                bar_width = int(abs(value) * (width // 2))
                if value > 0:
                    # Positive - fill right from center
                    self.display.fill_rect(center_x, y + 1, bar_width, height - 2, color)
                else:
                    # Negative - fill left from center
                    self.display.fill_rect(center_x - bar_width, y + 1, bar_width, height - 2, color)
                
                # Draw center line
                self.display.vline(center_x, y, height, COLOR_WHITE)
        except Exception as e:
            debug_print(f"Bar draw error: {e}")
    
    def update_telemetry(self, rssi=None, battery=None, latency=None):
        """
        Update telemetry values (call before refreshing driving display).
        
        Args:
            rssi: Wi-Fi signal strength in dBm
            battery: Battery voltage (not yet implemented)
            latency: Control latency in ms
        """
        if rssi is not None:
            self.rssi = rssi
        
        if latency is not None:
            self.latency_ms = latency
        
        # Telemetry updates are displayed automatically in _show_driving()
    
    def show_error(self, message):
        """
        Display error message.
        
        Args:
            message: Error message to display
        """
        debug_print(f"LCD Error: {message}", force=True)
        self._simple_display(f"ERROR\n{message}", COLOR_RED)
    
    def test_display(self):
        """Run display test sequence."""
        debug_print("Starting LCD test sequence", force=True)
        
        states = [
            (STATE_BOOT, {}),
            (STATE_NET_UP, {"ip": "10.42.0.123", "rssi": -50}),
            (STATE_CLIENT_OK, {}),
            (STATE_DRIVING, {"throttle": 0.5, "steer": -0.2}),
            (STATE_LINK_LOST, {}),
        ]
        
        for state, kwargs in states:
            self.set_state(state, **kwargs)
            time.sleep(2)
        
        debug_print("LCD test complete", force=True)


# Global LCD instance
lcd_display = None


def initialize():
    """
    Initialize the global LCD display.
    
    Returns:
        LCDStatus instance
    """
    global lcd_display
    lcd_display = LCDStatus()
    return lcd_display


def get_display():
    """
    Get the global LCD display instance.
    
    Returns:
        LCDStatus instance or None
    """
    return lcd_display
