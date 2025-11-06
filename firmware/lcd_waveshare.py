"""
LCD Status Display for Pico-Go Robot
====================================
Based on Waveshare official ST7789 example code.
Uses framebuffer with show() method to update display.
"""

from machine import Pin, SPI
import framebuf
import time
from config import (
    STATE_BOOT, STATE_NET_UP, STATE_CLIENT_OK,
    STATE_DRIVING, STATE_LINK_LOST, STATE_E_STOP
)
from utils import debug_print

# RGB565 Colors
WHITE = 0xFFFF
BLACK = 0x0000
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
YELLOW = 0xFFE0
CYAN = 0x07FF
MAGENTA = 0xF81F


class ST7789Display(framebuf.FrameBuffer):
    """ST7789 display driver based on Waveshare example."""
    
    def __init__(self):
        self.width = 240
        self.height = 135
        
        # Initialize pins - using Waveshare Pico-Go pinout
        self.rst = Pin(12, Pin.OUT)
        self.bl = Pin(13, Pin.OUT)
        self.bl(1)  # Backlight on
        
        self.cs = Pin(9, Pin.OUT)
        self.cs(1)
        self.spi = SPI(1, 10000_000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=None)
        self.dc = Pin(8, Pin.OUT)
        self.dc(1)
        
        # Create framebuffer
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        
        # Initialize display
        self.init_display()
        
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        """Initialize display."""
        self.rst(1)
        time.sleep_ms(50)
        self.rst(0)
        time.sleep_ms(50)
        self.rst(1)
        time.sleep_ms(50)
        
        self.write_cmd(0x36)
        self.write_data(0x70)

        self.write_cmd(0x3A) 
        self.write_data(0x05)

        self.write_cmd(0xB2)
        self.write_data(0x0C)
        self.write_data(0x0C)
        self.write_data(0x00)
        self.write_data(0x33)
        self.write_data(0x33)

        self.write_cmd(0xB7)
        self.write_data(0x35) 

        self.write_cmd(0xBB)
        self.write_data(0x19)

        self.write_cmd(0xC0)
        self.write_data(0x2C)

        self.write_cmd(0xC2)
        self.write_data(0x01)

        self.write_cmd(0xC3)
        self.write_data(0x12)   

        self.write_cmd(0xC4)
        self.write_data(0x20)

        self.write_cmd(0xC6)
        self.write_data(0x0F) 

        self.write_cmd(0xD0)
        self.write_data(0xA4)
        self.write_data(0xA1)

        self.write_cmd(0xE0)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0D)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2B)
        self.write_data(0x3F)
        self.write_data(0x54)
        self.write_data(0x4C)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x0B)
        self.write_data(0x1F)
        self.write_data(0x23)

        self.write_cmd(0xE1)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0C)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2C)
        self.write_data(0x3F)
        self.write_data(0x44)
        self.write_data(0x51)
        self.write_data(0x2F)
        self.write_data(0x1F)
        self.write_data(0x1F)
        self.write_data(0x20)
        self.write_data(0x23)
        
        self.write_cmd(0x21)
        self.write_cmd(0x11)
        time.sleep_ms(120)
        self.write_cmd(0x29)

    def show(self):
        """Update the display with framebuffer contents."""
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x28)
        self.write_data(0x01)
        self.write_data(0x17)
        
        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x35)
        self.write_data(0x00)
        self.write_data(0xBB)
        
        self.write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)


class LCDStatus:
    """LCD status display wrapper for robot."""
    
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
        
        try:
            self.display = ST7789Display()
            
            # Initial clear
            self.display.fill(BLACK)
            self.display.show()
            
            debug_print("LCD initialized successfully (Waveshare ST7789)", force=True)
            
        except Exception as e:
            debug_print(f"LCD initialization error: {e}", force=True)
            self.display = None
    
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
        self.display.fill(BLUE)
        self.display.text("PICO-GO", 80, 40, WHITE)
        self.display.text("ROBOT", 85, 55, CYAN)
        self.display.text("Booting...", 70, 80, WHITE)
        self.display.show()
    
    def _show_net_up(self):
        """Yellow screen - network ready."""
        debug_print(f"LCD: NET_UP - IP: {self.ip_address}")
        self.display.fill(YELLOW)
        self.display.text("NETWORK", 75, 10, BLACK)
        self.display.text("READY", 85, 25, BLACK)
        
        if self.ip_address:
            ip_str = str(self.ip_address)
            self.display.text("IP:", 10, 50, BLACK)
            self.display.text(ip_str, 10, 65, BLUE)
        
        if self.rssi:
            rssi_str = f"RSSI:{self.rssi}"
            self.display.text(rssi_str, 10, 85, BLACK)
        
        self.display.text("Waiting for", 60, 105, BLACK)
        self.display.text("controller", 65, 120, BLACK)
        self.display.show()
    
    def _show_client_ok(self):
        """Green screen - controller connected."""
        debug_print("LCD: CLIENT_OK")
        self.display.fill(GREEN)
        self.display.text("CONTROLLER", 65, 45, WHITE)
        self.display.text("CONNECTED", 70, 60, WHITE)
        self.display.text("READY!", 80, 85, YELLOW)
        self.display.show()
    
    def _show_driving(self):
        """Dynamic color based on connection quality."""
        if not self.display:
            return
        
        # Determine connection color
        bg_color = self._get_connection_color()
        text_color = WHITE if bg_color != YELLOW else BLACK
        
        # Fill background
        self.display.fill(bg_color)
        
        # Title
        self.display.text("DRIVING", 80, 5, text_color)
        
        # IP (small, corner)
        if self.ip_address:
            ip_short = str(self.ip_address).split('.')[-1]
            self.display.text(f".{ip_short}", 200, 5, text_color)
        
        # Throttle
        self.display.text("THR:", 5, 30, text_color)
        thr_str = f"{self.throttle:+.2f}"
        self.display.text(thr_str, 50, 30, CYAN)
        self._draw_bar(5, 45, 230, 12, self.throttle, CYAN)
        
        # Steering
        self.display.text("STR:", 5, 70, text_color)
        str_str = f"{self.steer:+.2f}"
        self.display.text(str_str, 50, 70, MAGENTA)
        self._draw_bar(5, 85, 230, 12, self.steer, MAGENTA)
        
        # Debug info
        self.display.text(f"PKT:{self.packets_received}", 5, 110, text_color)
        
        if self.rssi:
            self.display.text(f"RSSI:{self.rssi}", 5, 123, text_color)
        
        self.display.show()
    
    def _show_link_lost(self):
        """Red screen - connection lost."""
        debug_print("LCD: LINK LOST", force=True)
        self.display.fill(RED)
        self.display.text("CONNECTION", 65, 40, WHITE)
        self.display.text("LOST!", 85, 60, YELLOW)
        self.display.text("Motors Stopped", 50, 100, WHITE)
        self.display.show()
    
    def _show_e_stop(self):
        """Red screen - emergency stop."""
        debug_print("LCD: E-STOP", force=True)
        self.display.fill(RED)
        self.display.text("EMERGENCY", 70, 45, WHITE)
        self.display.text("STOP!", 90, 70, YELLOW)
        self.display.show()
    
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
    
    def _draw_bar(self, x, y, width, height, value, color):
        """Draw a horizontal bar for -1.0 to +1.0 values."""
        try:
            # Draw outline
            self.display.rect(x, y, width, height, WHITE)
            
            # Center line
            center_x = x + width // 2
            self.display.vline(center_x, y, height, WHITE)
            
            # Fill bar
            if abs(value) > 0.01:
                bar_width = int(abs(value) * (width // 2))
                if value > 0:
                    # Right from center
                    self.display.fill_rect(center_x + 1, y + 1, bar_width, height - 2, color)
                else:
                    # Left from center
                    self.display.fill_rect(center_x - bar_width, y + 1, bar_width, height - 2, color)
        except Exception as e:
            debug_print(f"Bar draw error: {e}")
    
    def update_telemetry(self, rssi=None, battery=None, latency=None):
        """Update telemetry values."""
        if rssi is not None:
            self.rssi = rssi
    
    def show_error(self, message):
        """Display error message."""
        debug_print(f"LCD Error: {message}", force=True)
        if not self.display:
            return
        self.display.fill(RED)
        self.display.text("ERROR", 85, 50, WHITE)
        msg = message[:30]  # Truncate
        self.display.text(msg, 10, 70, WHITE)
        self.display.show()
    
    def backlight_on(self):
        """Turn backlight on."""
        if self.display:
            self.display.bl(1)
    
    def backlight_off(self):
        """Turn backlight off."""
        if self.display:
            self.display.bl(0)


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
