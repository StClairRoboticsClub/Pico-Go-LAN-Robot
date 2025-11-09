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
    STATE_DRIVING, STATE_LINK_LOST, STATE_E_STOP,
    ROBOT_NAME, ROBOT_ID
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
            # ALWAYS update packet time when driving (needed for connection status indicators)
            self.last_packet_time = time.ticks_ms()
            self.packets_received += 1
            
            # Show "ACTIVE DRIVING" screen on first transition to driving OR when recovering from any other state
            if prev_state != STATE_DRIVING:
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
    
    def _draw_thunder_icon(self, x, y):
        """Draw a lightning bolt for THUNDER."""
        # Lightning bolt shape
        points = [
            (x+10, y), (x+6, y+8), (x+10, y+8), 
            (x+4, y+16), (x+12, y+10), (x+8, y+10), (x+14, y)
        ]
        # Draw bolt outline
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            self.display.line(x1, y1, x2, y2, YELLOW)
        # Fill with yellow
        self.display.fill_rect(x+7, y+3, 4, 5, YELLOW)
        self.display.fill_rect(x+6, y+8, 6, 3, YELLOW)
    
    def _draw_flame_icon(self, x, y):
        """Draw a flame for NITRO/BLITZ/SPEED."""
        # Flame shape - simplified
        for i in range(5):
            h = 10 - i * 2
            self.display.vline(x + 5 + i, y + i, h, YELLOW if i < 2 else RED)
            self.display.vline(x + 5 - i, y + i, h, YELLOW if i < 2 else RED)
    
    def _draw_speed_lines(self, x, y, width):
        """Draw racing speed lines."""
        for i in range(5):
            y_pos = y + i * 6
            line_width = width - i * 10
            self.display.hline(x, y_pos, line_width, CYAN)
            self.display.hline(x, y_pos + 2, line_width - 5, CYAN)
    
    def _draw_robot_icon(self):
        """Draw a HUGE cool robot icon based on robot name - FULL SCREEN!"""
        center_x = 120
        center_y = 67
        
        if "THUNDER" in ROBOT_NAME:
            # Purple and black patterned background
            for y in range(20, 135):
                for x in range(0, 240, 3):
                    if (x + y) % 8 < 4:
                        self.display.pixel(x, y, MAGENTA)
            
            # ONE MASSIVE lightning bolt down the center - classic zigzag
            bolt_points = [
                (140, 20),   # Top right start
                (110, 45),   # Zag left
                (130, 50),   # Zig right
                (100, 75),   # Zag left
                (120, 80),   # Zig right
                (90, 105),   # Zag left
                (110, 110),  # Zig right
                (80, 135)    # Bottom left end
            ]
            
            # Draw THICK lightning bolt
            for i in range(len(bolt_points) - 1):
                x1, y1 = bolt_points[i]
                x2, y2 = bolt_points[i + 1]
                # Make it SUPER thick (20px wide)
                for thickness in range(20):
                    offset = thickness - 10
                    self.display.line(x1 + offset, y1, x2 + offset, y2, YELLOW)
            
            # White core in the center of the bolt for brightness
            for i in range(len(bolt_points) - 1):
                x1, y1 = bolt_points[i]
                x2, y2 = bolt_points[i + 1]
                for thickness in range(6):
                    offset = thickness - 3
                    self.display.line(x1 + offset, y1, x2 + offset, y2, WHITE)
            
            # Electric glow around the bolt
            glow_points = [(140, 20), (110, 45), (100, 75), (90, 105), (80, 135)]
            for x, y in glow_points:
                # Radial glow
                for dx in range(-15, 16, 3):
                    for dy in range(-15, 16, 3):
                        if dx*dx + dy*dy < 200:
                            self.display.pixel(x + dx, y + dy, CYAN)
            
            # HUGE text at bottom
            self.display.text("THUNDER", 70, 120, YELLOW)
            self.display.text("THUNDER", 71, 120, YELLOW)
            self.display.text("THUNDER", 70, 121, YELLOW)
            self.display.text("THUNDER", 71, 121, YELLOW)
            
        elif "BLITZ" in ROBOT_NAME:
            # MASSIVE Speed lines - full screen width
            for i in range(10):
                y_pos = 25 + i * 10
                line_start = 10 + i * 5
                line_width = 220 - i * 10
                # Triple thick lines
                for thickness in range(5):
                    self.display.hline(line_start, y_pos + thickness, line_width, CYAN)
                    self.display.hline(line_start + 5, y_pos + thickness + 3, line_width - 15, YELLOW)
            
            # HUGE text
            self.display.text("BLITZ", 85, 105, CYAN)
            self.display.text("BLITZ", 86, 105, CYAN)
            self.display.text("BLITZ", 85, 106, CYAN)
            self.display.text("BLITZ", 86, 106, CYAN)
            
        elif "NITRO" in ROBOT_NAME:
            # MASSIVE Flame wall across screen
            for i in range(12):
                x_pos = 10 + i * 18
                flame_height = 60 + (i % 3) * 15
                # Draw tall flames
                for y in range(25, 25 + flame_height, 3):
                    flame_color = YELLOW if y < 45 else RED if y < 70 else MAGENTA
                    width = 12 - ((y - 25) // 10)
                    self.display.hline(x_pos - width//2, y, max(2, width), flame_color)
            
            # HUGE text
            self.display.text("NITRO", 85, 105, RED)
            self.display.text("NITRO", 86, 105, RED)
            self.display.text("NITRO", 85, 106, RED)
            self.display.text("NITRO", 86, 106, RED)
            
        elif "TURBO" in ROBOT_NAME:
            # MASSIVE Spinning turbo pattern
            for r in range(5, 55, 8):
                self.display.ellipse(center_x, center_y, r, r, GREEN)
                self.display.ellipse(center_x, center_y, r+1, r+1, GREEN)
            # Radial spokes
            for angle in range(0, 360, 30):
                import math
                x_end = int(center_x + 50 * math.cos(math.radians(angle)))
                y_end = int(center_y + 50 * math.sin(math.radians(angle)))
                self.display.line(center_x, center_y, x_end, y_end, CYAN)
            
            # HUGE text
            self.display.text("TURBO", 85, 105, GREEN)
            self.display.text("TURBO", 86, 105, GREEN)
            self.display.text("TURBO", 85, 106, GREEN)
            self.display.text("TURBO", 86, 106, GREEN)
            
        elif "SPEED" in ROBOT_NAME:
            # MASSIVE Arrow pattern - full screen
            for i in range(8):
                x_start = 10 + i * 10
                y_center = 60 + (i % 2) * 10
                arrow_len = 40
                # Thick arrows
                for thickness in range(6):
                    self.display.line(x_start, y_center + thickness - 3, 
                                    x_start + arrow_len, y_center - 20 + thickness - 3, CYAN)
                    self.display.line(x_start, y_center + thickness - 3, 
                                    x_start + arrow_len, y_center + 20 + thickness - 3, CYAN)
            
            # HUGE text
            self.display.text("SPEED", 85, 105, CYAN)
            self.display.text("SPEED", 86, 105, CYAN)
            self.display.text("SPEED", 85, 106, CYAN)
            self.display.text("SPEED", 86, 106, CYAN)
        else:
            # Generic HUGE robot
            self.display.rect(center_x - 40, center_y - 40, 80, 80, WHITE)
            self.display.fill_rect(center_x - 15, center_y - 15, 10, 10, GREEN)
            self.display.fill_rect(center_x + 5, center_y - 15, 10, 10, GREEN)
            self.display.text("RACER", 90, 105, WHITE)
    
    def _draw_racing_header(self, state_text="", color=WHITE):
        """Draw consistent racing-style header with robot name on all screens."""
        # Robot name banner at top - ALWAYS VISIBLE
        self.display.fill_rect(0, 0, 240, 20, BLACK)
        self._draw_large_text(ROBOT_NAME, 10, 5, YELLOW, 2)
        
        # Robot ID badge
        id_text = f"#{ROBOT_ID}"
        self.display.text(id_text, 210, 7, CYAN)
        
        # State indicator if provided
        if state_text:
            self.display.text(state_text, 180, 7, color)
    
    def _draw_speed_gauge(self, x, y, width, height, value, label, color):
        """Draw racing-style speed gauge with filled bars."""
        # Label
        self.display.text(label, x, y - 10, WHITE)
        
        # Gauge border with racing stripes
        self.display.rect(x, y, width, height, WHITE)
        self.display.rect(x + 1, y + 1, width - 2, height - 2, color)
        
        # Fill based on value (-1.0 to 1.0)
        center_x = x + width // 2
        self.display.vline(center_x, y, height, WHITE)
        
        if abs(value) > 0.01:
            bar_width = int(abs(value) * (width // 2))
            if value > 0:
                # Forward/Right
                for i in range(0, bar_width, 4):
                    bar_h = min(4, bar_width - i)
                    self.display.fill_rect(center_x + i, y + 2, bar_h - 1, height - 4, color)
            else:
                # Reverse/Left
                for i in range(0, bar_width, 4):
                    bar_h = min(4, bar_width - i)
                    self.display.fill_rect(center_x - i - bar_h, y + 2, bar_h - 1, height - 4, color)
        
        # Value display
        val_str = f"{value:+.1f}"
        self.display.text(val_str, x + width + 5, y + 3, color)
    
    def _draw_connection_icon(self, x, y, connected=True):
        """Draw WiFi/connection icon."""
        if connected:
            # WiFi connected icon - simplified bars
            for i in range(3):
                h = (i + 1) * 3
                self.display.fill_rect(x + i * 4, y + 9 - h, 3, h, GREEN)
        else:
            # Disconnected X
            for i in range(8):
                self.display.pixel(x + i, y + i, RED)
                self.display.pixel(x + 7 - i, y + i, RED)
    
    def _show_boot(self):
        """Racing-themed boot screen."""
        debug_print("LCD: BOOT")
        
        # Dark background
        self.display.fill(BLACK)
        
        # Racing checkered pattern (top border only - cleaner)
        for i in range(0, 240, 12):
            for j in range(0, 12, 6):
                if (i // 12 + j // 6) % 2 == 0:
                    self.display.fill_rect(i, j, 6, 6, WHITE)
        
        # Robot name - LARGE and centered (single layer, no bold)
        name_width = len(ROBOT_NAME) * 8  # Estimate width
        name_x = (240 - name_width) // 2
        self.display.text(ROBOT_NAME, name_x, 35, YELLOW)
        # Make it bigger with proper spacing
        self.display.text(ROBOT_NAME, name_x, 36, YELLOW)
        self.display.text(ROBOT_NAME, name_x + 1, 35, YELLOW)
        self.display.text(ROBOT_NAME, name_x + 1, 36, YELLOW)
        
        # Robot ID racing plate - cleaner, centered
        plate_x = 85
        self.display.fill_rect(plate_x, 55, 70, 22, WHITE)
        self.display.fill_rect(plate_x + 2, 57, 66, 18, BLACK)
        id_text = f"#{ROBOT_ID}"
        id_x = plate_x + 25
        self.display.text(id_text, id_x, 62, YELLOW)
        self.display.text(id_text, id_x + 1, 62, YELLOW)
        self.display.text(id_text, id_x, 63, YELLOW)
        
        # Subtitle - clean and readable
        self.display.text("RACE ROBOT", 80, 90, CYAN)
        
        # Loading bar - simple and clean
        self.display.rect(50, 110, 140, 10, GREEN)
        self.display.fill_rect(52, 112, 68, 6, GREEN)  # 50% loaded
        
        self.display.show()
    
    def _show_net_up(self):
        """Racing-themed network ready screen with robot name."""
        debug_print(f"LCD: NET_UP - IP: {self.ip_address}")
        
        # Clean dark background
        self.display.fill(BLACK)
        
        # Robot name header
        self._draw_racing_header("ONLINE", GREEN)
        
        # Connection status - clean and readable
        self.display.text("CONNECTED", 75, 30, GREEN)
        self.display.text("CONNECTED", 76, 30, GREEN)  # Make bolder
        
        # WiFi icon
        self._draw_connection_icon(105, 45, True)
        
        # IP Address - HUGE box, very clear
        if self.ip_address:
            ip_str = str(self.ip_address)
            self.display.fill_rect(15, 65, 210, 30, BLACK)
            self.display.rect(15, 65, 210, 30, YELLOW)
            self.display.rect(16, 66, 208, 28, YELLOW)  # Double border
            
            # Center the IP text
            ip_width = len(ip_str) * 8
            ip_x = (240 - ip_width) // 2
            self.display.text(ip_str, ip_x, 75, CYAN)
            self.display.text(ip_str, ip_x, 76, CYAN)  # Thicker
            self.display.text(ip_str, ip_x + 1, 75, CYAN)
        
        # Signal strength - simplified bar
        if self.rssi:
            signal_strength = min(100, max(0, int((self.rssi + 100) * 2)))
            self.display.text("SIGNAL:", 15, 105, WHITE)
            
            # Simple bar with better visibility
            bar_width = int(signal_strength * 2)  # Max 200px
            bar_color = GREEN if signal_strength > 60 else YELLOW if signal_strength > 30 else RED
            self.display.rect(15, 115, 200, 12, WHITE)
            if bar_width > 0:
                self.display.fill_rect(16, 116, bar_width, 10, bar_color)
            
            self.display.text(f"{self.rssi}dBm", 175, 105, CYAN)
        
        self.display.show()
    
    def _show_client_ok(self):
        """Racing-themed ready to race screen with robot name."""
        debug_print("LCD: CLIENT OK")
        
        # Clean background
        self.display.fill(BLACK)
        
        # Robot name header
        self._draw_racing_header("READY", GREEN)
        
        # "READY TO RACE!" message - clean and bold
        self.display.fill_rect(20, 30, 200, 35, BLACK)
        self.display.rect(20, 30, 200, 35, YELLOW)
        self.display.rect(21, 31, 198, 33, YELLOW)  # Double border
        
        self.display.text("READY TO", 70, 38, YELLOW)
        self.display.text("READY TO", 71, 38, YELLOW)
        self.display.text("RACE!", 85, 50, GREEN)
        self.display.text("RACE!", 86, 50, GREEN)
        self.display.text("RACE!", 85, 51, GREEN)
        
        # IP address - clear and centered
        if self.ip_address:
            ip_str = str(self.ip_address)
            self.display.text("IP:", 15, 75, WHITE)
            self.display.text(ip_str, 40, 75, CYAN)
            self.display.text(ip_str, 41, 75, CYAN)
        
        # WiFi status - simplified
        self._draw_connection_icon(15, 90, True)
        if self.rssi:
            quality = "GOOD" if self.rssi > -70 else "OK" if self.rssi > -80 else "WEAK"
            q_color = GREEN if self.rssi > -70 else YELLOW if self.rssi > -80 else RED
            self.display.text(quality, 35, 92, q_color)
            self.display.text(f"{self.rssi}dBm", 75, 92, q_color)
        
        # Racing start lights - clean design
        self.display.text("START:", 15, 110, WHITE)
        for i in range(5):
            self.display.fill_rect(60 + i * 25, 107, 18, 18, GREEN)
            self.display.rect(60 + i * 25, 107, 18, 18, YELLOW)
        
        self.display.text("WAITING...", 70, 130, YELLOW)
        
        self.display.show()
    
    def _show_driving_active(self):
        """Racing-themed active driving screen with FULL SCREEN robot icon and separate connection indicators."""
        debug_print("LCD: ACTIVE DRIVING - Showing full-screen robot icon")
        
        # High-energy background
        self.display.fill(BLACK)
        
        # Draw HUGE robot-themed icon filling entire screen
        self._draw_robot_icon()
        
        # Top status bar - compact black background for visibility
        self.display.fill_rect(0, 0, 240, 18, BLACK)
        
        # Left side: WiFi connection status
        self.display.text("WiFi:", 2, 5, WHITE)
        wifi_connected = self.ip_address is not None
        if wifi_connected:
            # WiFi signal strength bars - compact
            for i in range(3):
                h = (i + 1) * 2
                self.display.fill_rect(30 + i * 3, 11 - h, 2, h, GREEN)
            # Signal quality dot
            if self.rssi:
                sig_color = GREEN if self.rssi > -70 else YELLOW if self.rssi > -80 else RED
                self.display.fill_rect(40, 5, 2, 2, sig_color)
        else:
            # Disconnected X - compact
            for i in range(5):
                self.display.pixel(30 + i, 5 + i, RED)
                self.display.pixel(34 - i, 5 + i, RED)
        
        # Center: Robot name and ID
        name_text = f"{ROBOT_NAME} #{ROBOT_ID}"
        name_width = len(name_text) * 8
        name_x = (240 - name_width) // 2
        self.display.text(name_text, name_x, 5, YELLOW)
        
        # Right side: Controller connection status
        self.display.text("Ctrl:", 185, 5, WHITE)
        # Check if we're receiving packets
        if hasattr(self, 'last_packet_time'):
            elapsed = time.ticks_diff(time.ticks_ms(), self.last_packet_time)
            controller_connected = elapsed < 500  # Connected if packet within 500ms
            if controller_connected:
                # Connected indicator - green square
                self.display.fill_rect(218, 6, 4, 4, GREEN)
                self.display.rect(218, 6, 4, 4, WHITE)
            else:
                # Disconnected indicator - red X
                for i in range(4):
                    self.display.pixel(218 + i, 6 + i, RED)
                    self.display.pixel(221 - i, 6 + i, RED)
        else:
            # No packets yet - yellow waiting indicator
            self.display.fill_rect(218, 6, 4, 4, YELLOW)
            self.display.rect(218, 6, 4, 4, WHITE)
        
        # Bottom corner: IP last octet (very subtle)
        if self.ip_address:
            ip_short = str(self.ip_address).split('.')[-1]
            self.display.text(f".{ip_short}", 3, 128, CYAN)
        
        self.display.show()
    
    def _show_link_lost(self):
        """Racing-themed connection lost screen - SPECIFIC about which connection was lost."""
        debug_print("LCD: LINK LOST", force=True)
        
        # Alert background
        self.display.fill(RED)
        
        # Robot name header - ALWAYS VISIBLE
        self._draw_racing_header("ALERT", WHITE)
        
        # Warning border - simplified
        self.display.rect(10, 28, 220, 100, YELLOW)
        self.display.rect(12, 30, 216, 96, YELLOW)
        
        # Alert message - clean and bold
        self.display.fill_rect(20, 35, 200, 90, BLACK)
        
        # Check what's still connected
        wifi_connected = self.ip_address is not None
        controller_connected = False
        if hasattr(self, 'last_packet_time'):
            elapsed = time.ticks_diff(time.ticks_ms(), self.last_packet_time)
            controller_connected = elapsed < 1000  # Give 1 second grace period
        
        # Show which connection was lost
        self.display.text("CONNECTION LOST:", 40, 42, YELLOW)
        
        # WiFi status
        self.display.text("WiFi:", 30, 58, WHITE)
        if wifi_connected:
            self.display.text("OK", 80, 58, GREEN)
            # WiFi signal bars
            for i in range(3):
                h = (i + 1) * 2
                self.display.fill_rect(105 + i * 4, 63 - h, 3, h, GREEN)
        else:
            self.display.text("LOST!", 80, 58, RED)
            self.display.text("LOST!", 81, 58, RED)
            # Disconnected X
            for i in range(6):
                self.display.pixel(105 + i, 58 + i, RED)
                self.display.pixel(110 - i, 58 + i, RED)
        
        # Controller status
        self.display.text("Controller:", 30, 75, WHITE)
        if controller_connected:
            self.display.text("OK", 120, 75, GREEN)
            self.display.fill_rect(145, 76, 5, 5, GREEN)
            self.display.rect(145, 76, 5, 5, WHITE)
        else:
            self.display.text("LOST!", 120, 75, RED)
            self.display.text("LOST!", 121, 75, RED)
            # Disconnected X
            for i in range(5):
                self.display.pixel(145 + i, 76 + i, RED)
                self.display.pixel(149 - i, 76 + i, RED)
        
        # Status - clear
        self.display.text("MOTORS STOPPED", 60, 95, WHITE)
        
        # Last known IP - if available
        if self.ip_address:
            ip_str = str(self.ip_address)
            self.display.text(f"IP: {ip_str}", 50, 110, CYAN)
        
        self.display.show()
    
    def _show_e_stop(self):
        """Racing-themed emergency stop screen - clean and clear."""
        debug_print("LCD: E-STOP", force=True)
        
        # Critical alert background
        self.display.fill(RED)
        
        # Robot name header - ALWAYS VISIBLE
        self._draw_racing_header("E-STOP", WHITE)
        
        # Triple warning border - cleaner
        for offset in range(3):
            self.display.rect(8 + offset * 3, 28 + offset * 3, 224 - offset * 6, 100 - offset * 6, YELLOW)
        
        # Emergency message - bold and clear
        self.display.fill_rect(25, 40, 190, 45, BLACK)
        
        self.display.text("EMERGENCY", 60, 48, RED)
        self.display.text("EMERGENCY", 61, 48, RED)
        self.display.text("STOP!", 85, 62, YELLOW)
        self.display.text("STOP!", 86, 62, YELLOW)
        self.display.text("STOP!", 85, 63, YELLOW)
        
        # Status - clear
        self.display.text("ALL SYSTEMS HALTED", 48, 95, WHITE)
        self.display.text("RESTART REQUIRED", 55, 110, YELLOW)
        
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
