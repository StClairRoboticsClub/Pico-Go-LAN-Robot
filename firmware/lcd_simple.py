"""
Simplified LCD for Pico-Go Robot - Working Version
==================================================
Uses direct SPI commands without external dependencies.
Displays colored backgrounds for connection status.
"""

from machine import Pin, SPI
import time
from config import (
    PIN_LCD_SCK, PIN_LCD_MOSI, PIN_LCD_DC,
    PIN_LCD_RST, PIN_LCD_CS, PIN_LCD_BL,
    STATE_BOOT, STATE_NET_UP, STATE_CLIENT_OK,
    STATE_DRIVING, STATE_LINK_LOST, STATE_E_STOP
)
from utils import debug_print

# ST7735 Commands
ST7735_NOP = 0x00
ST7735_SWRESET = 0x01
ST7735_SLPOUT = 0x11
ST7735_DISPOFF = 0x28
ST7735_DISPON = 0x29
ST7735_CASET = 0x2A
ST7735_RASET = 0x2B
ST7735_RAMWR = 0x2C
ST7735_COLMOD = 0x3A
ST7735_MADCTL = 0x36

# RGB565 Colors
BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
YELLOW = 0xFFE0
CYAN = 0x07FF
MAGENTA = 0xF81F


class LCDStatus:
    """Simple LCD status display with colored backgrounds."""
    
    def __init__(self):
        """Initialize LCD."""
        self.display = None
        self.current_state = None
        self.ip_address = None
        self.rssi = None
        self.packets_received = 0
        self.last_packet_time = 0
        self.throttle = 0
        self.steer = 0
        self.width = 135
        self.height = 240
        
        try:
            # Initialize SPI
            self.spi = SPI(
                0,
                baudrate=10000000,  # 10 MHz for stability
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
            
            # Hardware reset
            self.rst.value(0)
            time.sleep_ms(50)
            self.rst.value(1)
            time.sleep_ms(50)
            
            # Initialize display
            self._init_display()
            
            # Turn on backlight
            self.bl.value(1)
            
            # Clear to black
            self.fill(BLACK)
            
            self.display = True  # Mark as initialized
            debug_print("LCD initialized successfully (ST7735 direct)", force=True)
            
        except Exception as e:
            debug_print(f"LCD initialization error: {e}", force=True)
            self.display = None
    
    def _write_cmd(self, cmd):
        """Write command to display."""
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)
    
    def _write_data(self, data):
        """Write data to display."""
        self.dc.value(1)
        self.cs.value(0)
        if isinstance(data, int):
            self.spi.write(bytearray([data]))
        else:
            self.spi.write(data)
        self.cs.value(1)
    
    def _init_display(self):
        """Initialize ST7735 display."""
        # Software reset
        self._write_cmd(ST7735_SWRESET)
        time.sleep_ms(150)
        
        # Out of sleep mode
        self._write_cmd(ST7735_SLPOUT)
        time.sleep_ms(500)
        
        # Set color mode to 16-bit
        self._write_cmd(ST7735_COLMOD)
        self._write_data(0x05)
        
        # Memory access control (rotation)
        self._write_cmd(ST7735_MADCTL)
        self._write_data(0x08)  # RGB order
        
        # Display on
        self._write_cmd(ST7735_DISPON)
        time.sleep_ms(100)
    
    def fill(self, color):
        """Fill entire display with color."""
        if not self.display:
            return
        
        try:
            # Set column address
            self._write_cmd(ST7735_CASET)
            self._write_data(bytearray([0, 0, 0, self.width - 1]))
            
            # Set row address
            self._write_cmd(ST7735_RASET)
            self._write_data(bytearray([0, 0, 0, self.height - 1]))
            
            # Write to RAM
            self._write_cmd(ST7735_RAMWR)
            
            # Create color buffer (2 bytes per pixel)
            color_high = (color >> 8) & 0xFF
            color_low = color & 0xFF
            pixel = bytearray([color_high, color_low])
            
            # Write pixels
            self.dc.value(1)
            self.cs.value(0)
            for _ in range(self.width * self.height):
                self.spi.write(pixel)
            self.cs.value(1)
            
        except Exception as e:
            debug_print(f"Fill error: {e}")
    
    def set_state(self, state, **kwargs):
        """Update display based on state."""
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
            debug_print(f"State display error: {e}")
    
    def _show_boot(self):
        """Blue screen - booting."""
        debug_print("LCD: BOOT")
        self.fill(BLUE)
    
    def _show_net_up(self):
        """Yellow screen - network ready, waiting for controller."""
        debug_print(f"LCD: NET_UP - IP: {self.ip_address}")
        self.fill(YELLOW)
    
    def _show_client_ok(self):
        """Green screen - controller connected."""
        debug_print("LCD: CLIENT_OK")
        self.fill(GREEN)
    
    def _show_driving(self):
        """Dynamic color based on connection quality."""
        if not self.display:
            return
        
        # Determine connection color
        bg_color = self._get_connection_color()
        self.fill(bg_color)
    
    def _show_link_lost(self):
        """Red screen - connection lost."""
        debug_print("LCD: LINK LOST", force=True)
        self.fill(RED)
    
    def _show_e_stop(self):
        """Red screen - emergency stop."""
        debug_print("LCD: E-STOP", force=True)
        self.fill(RED)
    
    def _get_connection_color(self):
        """Determine connection quality color."""
        if self.last_packet_time == 0:
            return RED
        
        elapsed = time.ticks_diff(time.ticks_ms(), self.last_packet_time)
        
        if elapsed > 200:
            return RED  # Disconnected
        elif elapsed > 100:
            return YELLOW  # Laggy
        else:
            return GREEN  # Good
    
    def update_telemetry(self, rssi=None, battery=None, latency=None):
        """Update telemetry values."""
        if rssi is not None:
            self.rssi = rssi
    
    def show_error(self, message):
        """Display error - red screen."""
        debug_print(f"LCD Error: {message}", force=True)
        self.fill(RED)
    
    def backlight_on(self):
        """Turn backlight on."""
        if hasattr(self, 'bl'):
            self.bl.value(1)
    
    def backlight_off(self):
        """Turn backlight off."""
        if hasattr(self, 'bl'):
            self.bl.value(0)


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
