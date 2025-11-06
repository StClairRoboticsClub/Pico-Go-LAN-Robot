"""
Working LCD Display for Pico-Go Robot
=====================================
Uses ST7735 driver for 1.14" display with simple text overlay.
"""

from machine import Pin, SPI
import st7735
import time
from config import (
    PIN_LCD_SCK, PIN_LCD_MOSI, PIN_LCD_DC,
    PIN_LCD_RST, PIN_LCD_CS, PIN_LCD_BL,
    STATE_BOOT, STATE_NET_UP, STATE_CLIENT_OK,
    STATE_DRIVING, STATE_LINK_LOST, STATE_E_STOP
)
from utils import debug_print

# ST7735 colors (RGB565)
BLACK = st7735.TFTColor(0, 0, 0)
WHITE = st7735.TFTColor(255, 255, 255)
RED = st7735.TFTColor(255, 0, 0)
GREEN = st7735.TFTColor(0, 255, 0)
BLUE = st7735.TFTColor(0, 0, 255)
YELLOW = st7735.TFTColor(255, 255, 0)
CYAN = st7735.TFTColor(0, 255, 255)
MAGENTA = st7735.TFTColor(255, 0, 255)
ORANGE = st7735.TFTColor(255, 165, 0)
DARK_GREEN = st7735.TFTColor(0, 128, 0)


class LCDStatus:
    """LCD status display for Pico-Go robot."""
    
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
        
        try:
            # Initialize SPI
            spi = SPI(
                0,
                baudrate=20000000,  # 20 MHz
                polarity=0,
                phase=0,
                sck=Pin(PIN_LCD_SCK),
                mosi=Pin(PIN_LCD_MOSI)
            )
            
            # Initialize control pins
            dc = Pin(PIN_LCD_DC, Pin.OUT)
            rst = Pin(PIN_LCD_RST, Pin.OUT)
            cs = Pin(PIN_LCD_CS, Pin.OUT)
            bl = Pin(PIN_LCD_BL, Pin.OUT)
            
            # Initialize ST7735 display (1.14" 135x240)
            self.display = st7735.TFT(spi, dc, rst, cs)
            self.display.init()
            
            # Turn on backlight
            bl.value(1)
            
            # Clear to black
            self.display.fill(BLACK)
            
            debug_print("LCD initialized successfully (ST7735 1.14\")", force=True)
            
        except Exception as e:
            debug_print(f"LCD initialization error: {e}", force=True)
            self.display = None
    
    def set_state(self, state, **kwargs):
        """Update display to show current system state."""
        if not self.display:
            return
        
        self.current_state = state
        
        try:
            if state == STATE_BOOT:
                self._show_boot()
            elif state == STATE_NET_UP:
                self.ip_address = kwargs.get('ip', None)
                self.rssi = kwargs.get('rssi', None)
                self._show_net_up()
            elif state == STATE_CLIENT_OK:
                self._show_client_ok()
            elif state == STATE_DRIVING:
                self.throttle = kwargs.get('throttle', 0)
                self.steer = kwargs.get('steer', 0)
                self.last_packet_time = time.ticks_ms()
                self.packets_received += 1
                self._show_driving()
            elif state == STATE_LINK_LOST:
                self._show_link_lost()
            elif state == STATE_E_STOP:
                self._show_e_stop()
        except Exception as e:
            debug_print(f"LCD display error: {e}")
    
    def _show_boot(self):
        """Display boot screen."""
        debug_print("LCD: BOOT")
        if not self.display:
            return
        
        self.display.fill(BLUE)
        self.display.text((10, 60), "PICO-GO", WHITE, size=2)
        self.display.text((10, 90), "ROBOT", WHITE, size=2)
        self.display.text((10, 130), "Booting...", WHITE)
    
    def _show_net_up(self):
        """Display network connected screen."""
        debug_print(f"LCD: NET_UP - IP: {self.ip_address}")
        if not self.display:
            return
        
        self.display.fill(YELLOW)
        self.display.text((5, 20), "NETWORK", BLACK, size=2)
        self.display.text((5, 45), "READY", BLACK, size=2)
        
        if self.ip_address:
            ip_str = str(self.ip_address)
            self.display.text((5, 80), "IP:", BLACK)
            self.display.text((5, 95), ip_str, BLUE, size=1)
        
        if self.rssi:
            rssi_str = f"RSSI:{self.rssi}"
            self.display.text((5, 115), rssi_str, BLACK)
        
        self.display.text((5, 140), "Waiting for", BLACK)
        self.display.text((5, 155), "controller", BLACK)
    
    def _show_client_ok(self):
        """Display client connected screen."""
        debug_print("LCD: CLIENT_OK")
        if not self.display:
            return
        
        self.display.fill(GREEN)
        self.display.text((5, 60), "CONTROLLER", WHITE, size=2)
        self.display.text((5, 90), "CONNECTED", WHITE, size=2)
        self.display.text((15, 130), "READY", YELLOW, size=3)
    
    def _show_driving(self):
        """Display driving state with metrics."""
        if not self.display:
            return
        
        # Determine connection color
        bg_color = self._get_connection_color()
        text_color = WHITE if bg_color != YELLOW else BLACK
        
        # Fill background
        self.display.fill(bg_color)
        
        # Title
        self.display.text((5, 5), "DRIVING", text_color, size=2)
        
        # IP address (small, top-right)
        if self.ip_address:
            ip_short = str(self.ip_address).split('.')[-1]  # Just last octet
            self.display.text((95, 5), f".{ip_short}", text_color)
        
        # Throttle
        self.display.text((5, 40), "THR:", text_color)
        thr_str = f"{self.throttle:+.2f}"
        self.display.text((50, 40), thr_str, CYAN)
        self._draw_bar(5, 55, 125, 15, self.throttle, CYAN)
        
        # Steering
        self.display.text((5, 80), "STR:", text_color)
        str_str = f"{self.steer:+.2f}"
        self.display.text((50, 80), str_str, MAGENTA)
        self._draw_bar(5, 95, 125, 15, self.steer, MAGENTA)
        
        # Debug info
        self.display.text((5, 120), f"PKT:{self.packets_received}", text_color)
        
        if self.rssi:
            self.display.text((5, 135), f"RSSI:{self.rssi}", text_color)
        
        if self.latency_ms > 0:
            self.display.text((5, 150), f"LAT:{self.latency_ms}ms", text_color)
    
    def _show_link_lost(self):
        """Display link lost warning."""
        debug_print("LCD: LINK LOST", force=True)
        if not self.display:
            return
        
        self.display.fill(RED)
        self.display.text((5, 60), "CONNECTION", WHITE, size=2)
        self.display.text((15, 90), "LOST!", YELLOW, size=3)
        self.display.text((5, 140), "Motors Stopped", WHITE)
    
    def _show_e_stop(self):
        """Display emergency stop screen."""
        debug_print("LCD: E-STOP", force=True)
        if not self.display:
            return
        
        self.display.fill(RED)
        self.display.text((5, 60), "EMERGENCY", WHITE, size=2)
        self.display.text((15, 100), "STOP!", YELLOW, size=3)
    
    def _get_connection_color(self):
        """Determine connection status color."""
        if self.last_packet_time == 0:
            return RED
        
        elapsed = time.ticks_diff(time.ticks_ms(), self.last_packet_time)
        
        if elapsed > 200:
            return RED
        elif elapsed > 100:
            return YELLOW
        else:
            return GREEN
    
    def _draw_bar(self, x, y, width, height, value, color):
        """Draw a horizontal bar for -1.0 to +1.0 values."""
        if not self.display:
            return
        
        try:
            # Draw outline
            self.display.rect((x, y), (width, height), WHITE)
            
            # Center line
            center_x = x + width // 2
            self.display.line((center_x, y), (center_x, y + height), WHITE)
            
            # Fill bar
            if abs(value) > 0.01:
                bar_width = int(abs(value) * (width // 2))
                if value > 0:
                    # Right from center
                    self.display.fillrect((center_x + 1, y + 1), (bar_width, height - 2), color)
                else:
                    # Left from center
                    self.display.fillrect((center_x - bar_width, y + 1), (bar_width, height - 2), color)
        except Exception as e:
            debug_print(f"Bar draw error: {e}")
    
    def update_telemetry(self, rssi=None, battery=None, latency=None):
        """Update telemetry values."""
        if rssi is not None:
            self.rssi = rssi
        if latency is not None:
            self.latency_ms = latency
    
    def show_error(self, message):
        """Display error message."""
        debug_print(f"LCD Error: {message}", force=True)
        if not self.display:
            return
        
        self.display.fill(RED)
        self.display.text((5, 60), "ERROR", WHITE, size=2)
        self.display.text((5, 100), message[:20], WHITE)  # Truncate if too long
    
    def backlight_on(self):
        """Turn backlight on (handled in init)."""
        pass
    
    def backlight_off(self):
        """Turn backlight off (handled in init)."""
        pass


# Global LCD instance
lcd_display = None


def initialize():
    """Initialize the global LCD display."""
    global lcd_display
    lcd_display = LCDStatus()
    return lcd_display


def get_display():
    """Get the global LCD display instance."""
    return lcd_display
