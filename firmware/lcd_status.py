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

# RGB565 Colors (BGR format for this display)
# Note: This display uses BGR order, not RGB!
WHITE = 0xFFFF
BLACK = 0x0000
RED = 0x001F      # Actually blue in RGB565, but shows as red on this display
GREEN = 0xF800    # Actually red in RGB565, but shows as green on this display  
BLUE = 0x07E0     # Actually green in RGB565, but shows as blue on this display
YELLOW = 0x07FF   # Cyan in RGB565, yellow on display
CYAN = 0xFFE0     # Yellow in RGB565, cyan on display
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
        
        # Display update throttling (only update every N ms to avoid blocking)
        self.last_display_update = 0
        self.display_update_interval = 100  # Update LCD every 100ms (10 Hz) instead of 30 Hz
        self.pending_update = False
        
        try:
            self.display = ST7789Display()
            
            # Initial clear
            self.display.fill(BLACK)
            self.display.show()
            self.last_display_update = time.ticks_ms()
            
            debug_print("LCD initialized successfully (Waveshare ST7789)", force=True)
            
        except Exception as e:
            debug_print(f"LCD initialization error: {e}", force=True)
            self.display = None
    
    def set_state(self, state, **kwargs):
        """Update display based on state (NO updates during DRIVING to avoid latency)."""
        if not self.display:
            return
        
        prev_state = self.current_state
        self.current_state = state
        
        # Update data immediately
        if state == STATE_DRIVING:
            self.throttle = kwargs.get('throttle', 0)
            self.steer = kwargs.get('steer', 0)
            self.last_packet_time = time.ticks_ms()
            self.packets_received += 1
            
            # Show "ACTIVE DRIVING" screen ONCE on first transition to driving
            if prev_state != STATE_DRIVING and self.packets_received == 1:
                try:
                    self._show_driving_active()
                except Exception as e:
                    debug_print(f"Drive active screen error: {e}")
            
            # CRITICAL: Do NOT update display during driving - causes 23ms latency!
            return
        elif state == STATE_NET_UP:
            self.ip_address = kwargs.get('ip', None)
            self.rssi = kwargs.get('rssi', None)
        
        # Render the display (only for non-driving states)
        try:
            if state == STATE_BOOT:
                self._show_boot()
            elif state == STATE_NET_UP:
                self._show_net_up()
            elif state == STATE_CLIENT_OK:
                self._show_client_ok()
            elif state == STATE_LINK_LOST:
                self._show_link_lost()
            elif state == STATE_E_STOP:
                self._show_e_stop()
        except Exception as e:
            debug_print(f"State display error: {e}")
    
    def _draw_large_text(self, text, x, y, color, scale=2):
        """Draw larger text by drawing each character multiple times with offset."""
        for i in range(scale):
            for j in range(scale):
                self.display.text(text, x + i, y + j, color)
    
    def _show_boot(self):
        """Blue screen - booting."""
        debug_print("LCD: BOOT")
        self.display.fill(BLUE)
        self._draw_large_text("PICO-GO", 60, 35, WHITE, 2)
        self._draw_large_text("ROBOT", 70, 60, CYAN, 2)
        self.display.text("Booting...", 70, 95, WHITE)
        self.display.show()
    
    def _show_net_up(self):
        """Cyan screen - WiFi connected, waiting for controller."""
        debug_print(f"LCD: NET_UP - IP: {self.ip_address}")
        self.display.fill(CYAN)
        
        # Title
        self._draw_large_text("WiFi", 85, 5, WHITE, 2)
        self._draw_large_text("CONNECTED", 50, 27, BLUE, 2)
        
        # Separator
        self.display.fill_rect(5, 52, 230, 2, BLUE)
        
        # IP Address - large and centered
        if self.ip_address:
            ip_str = str(self.ip_address)
            self.display.text("Robot IP:", 70, 60, BLACK)
            self._draw_large_text(ip_str, 15, 72, BLACK, 2)
        
        # Signal strength with visual bar
        if self.rssi:
            signal_strength = min(100, max(0, int((self.rssi + 100) * 2)))  # -100 to -50 -> 0 to 100
            self.display.text(f"Signal: {self.rssi}dBm", 10, 95, BLACK)
            # Signal bar
            bar_width = int(signal_strength * 2.2)  # Max 220px
            bar_color = BLUE if signal_strength > 60 else YELLOW if signal_strength > 30 else RED
            self.display.fill_rect(10, 108, bar_width, 12, bar_color)
            self.display.rect(10, 108, 220, 12, BLACK)
        
        self.display.text("Waiting for controller...", 30, 126, BLACK)
        self.display.show()
    
    def _show_client_ok(self):
        """Green screen - client connected. Rich info dashboard."""
        debug_print("LCD: CLIENT OK")
        self.display.fill(GREEN)
        
        # Title
        self._draw_large_text("READY", 75, 5, WHITE, 2)
        self._draw_large_text("TO DRIVE", 55, 27, YELLOW, 2)
        
        # Connection status bar
        self.display.fill_rect(5, 52, 230, 2, WHITE)
        
        # IP Address - prominent
        if self.ip_address:
            self.display.text("IP:", 5, 60, WHITE)
            ip_str = str(self.ip_address)
            self._draw_large_text(ip_str, 30, 58, BLACK, 1)
        
        # RSSI - signal strength
        if self.rssi:
            self.display.text("Signal:", 5, 80, WHITE)
            rssi_str = f"{self.rssi} dBm"
            signal_quality = "EXCELLENT" if self.rssi > -50 else "GOOD" if self.rssi > -70 else "WEAK"
            signal_color = CYAN if self.rssi > -50 else YELLOW if self.rssi > -70 else RED
            self._draw_large_text(rssi_str, 65, 78, signal_color, 1)
            self.display.text(signal_quality, 165, 80, signal_color)
        
        # Status indicators
        self.display.text("Controller: CONNECTED", 15, 100, WHITE)
        self.display.text("Motors: ENABLED", 25, 113, WHITE)
        self.display.text("Safety: ARMED", 30, 126, CYAN)
        
        self.display.show()
    
    def _show_driving_active(self):
        """Show ACTIVE DRIVING screen once, then freeze."""
        debug_print("LCD: ACTIVE DRIVING - Display will freeze for performance")
        self.display.fill(GREEN)
        
        # Large title
        self._draw_large_text("ACTIVE", 70, 20, WHITE, 3)
        self._draw_large_text("DRIVING", 60, 55, YELLOW, 3)
        
        # Status
        self.display.text("Display frozen for", 50, 100, WHITE)
        self.display.text("zero-latency control", 35, 113, CYAN)
        
        self.display.show()
    
    def _show_driving(self):
        """Dynamic color based on connection quality (UNUSED - kept for reference)."""
        if not self.display:
            return
        
        # Determine connection color
        bg_color = self._get_connection_color()
        text_color = WHITE if bg_color != YELLOW else BLACK
        
        # Fill background
        self.display.fill(bg_color)
        
        # Title - larger
        self._draw_large_text("DRIVE", 75, 3, text_color, 2)
        
        # IP (small, corner)
        if self.ip_address:
            ip_short = str(self.ip_address).split('.')[-1]
            self.display.text(f".{ip_short}", 200, 5, text_color)
        
        # Throttle - larger labels
        self._draw_large_text("THR:", 5, 28, text_color, 1)
        thr_str = f"{self.throttle:+.2f}"
        self._draw_large_text(thr_str, 50, 28, CYAN, 1)
        self._draw_bar(5, 45, 230, 14, self.throttle, CYAN)
        
        # Steering - larger labels
        self._draw_large_text("STR:", 5, 68, text_color, 1)
        str_str = f"{self.steer:+.2f}"
        self._draw_large_text(str_str, 50, 68, MAGENTA, 1)
        self._draw_bar(5, 85, 230, 14, self.steer, MAGENTA)
        
        # Debug info
        self.display.text(f"PKT:{self.packets_received}", 5, 108, text_color)
        
        if self.rssi:
            self.display.text(f"RSSI:{self.rssi}", 5, 122, text_color)
        
        self.display.show()
    
    def _show_link_lost(self):
        """Red screen - connection lost."""
        debug_print("LCD: LINK LOST", force=True)
        self.display.fill(RED)
        self._draw_large_text("LINK", 85, 35, WHITE, 2)
        self._draw_large_text("LOST!", 75, 60, YELLOW, 2)
        self.display.text("Motors Stopped", 55, 100, WHITE)
        self.display.show()
    
    def _show_e_stop(self):
        """Red screen - emergency stop."""
        debug_print("LCD: E-STOP", force=True)
        self.display.fill(RED)
        self._draw_large_text("EMERGENCY", 50, 40, WHITE, 2)
        self._draw_large_text("STOP!", 75, 70, YELLOW, 2)
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
        """Update telemetry values (does NOT trigger display refresh)."""
        if rssi is not None:
            self.rssi = rssi
        # Never refresh display here - would cause latency
    
    def force_update(self):
        """Force update disabled - causes latency during driving."""
        # DISABLED: LCD updates during driving cause 23ms latency
        pass
    
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
    
    # Check if LCD is enabled in config
    try:
        from config import LCD_ENABLED
        if not LCD_ENABLED:
            from utils import debug_print
            debug_print("LCD disabled in config - skipping initialization", force=True)
            return None
    except ImportError:
        pass  # If config doesn't have LCD_ENABLED, initialize anyway
    
    lcd_display = LCDStatus()
    return lcd_display


def get_display():
    """Get the global LCD display instance."""
    return lcd_display
