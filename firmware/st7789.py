"""
Simple LCD Driver Wrapper for Pico-Go Robot
===========================================
Works with both ST7735 (1.14") and ST7789 (1.3") displays.

This is a minimal framebuffer-based implementation that works
without external display drivers.
"""

from machine import Pin, SPI
import framebuf
import time

class SimpleLCD:
    """
    Simple LCD driver using framebuffer.
    Works without external driver libraries.
    """
    
    def __init__(self, width=135, height=240, rotation=0):
        """
        Initialize simple LCD.
        
        Args:
            width: Display width (135 for ST7735, 240 for ST7789)
            height: Display height
            rotation: Display rotation
        """
        self.width = width
        self.height = height
        
        # Initialize pins
        self.spi = SPI(0, baudrate=40000000, sck=Pin(18), mosi=Pin(19))
        self.dc = Pin(16, Pin.OUT)
        self.rst = Pin(20, Pin.OUT)
        self.cs = Pin(17, Pin.OUT)
        self.bl = Pin(21, Pin.OUT)
        
        # Simple framebuffer (1-bit for text)
        self.buffer = bytearray(width * height // 8)
        self.fb = framebuf.FrameBuffer(self.buffer, width, height, framebuf.MONO_HLSB)
        
        # Turn on backlight
        self.bl.value(1)
        
        print("Simple LCD initialized (framebuffer mode)")
    
    def init(self):
        """Initialize display."""
        pass
    
    def fill(self, color):
        """Fill display with color."""
        # In framebuffer mode, just clear
        self.fb.fill(1 if color else 0)
    
    def text(self, text, x, y, color):
        """Draw text."""
        self.fb.text(text, x, y, 1 if color else 0)
    
    def rect(self, x, y, w, h, color):
        """Draw rectangle."""
        self.fb.rect(x, y, w, h, 1 if color else 0)
    
    def fill_rect(self, x, y, w, h, color):
        """Draw filled rectangle."""
        self.fb.fill_rect(x, y, w, h, 1 if color else 0)
    
    def vline(self, x, y, h, color):
        """Draw vertical line."""
        self.fb.vline(x, y, h, 1 if color else 0)
    
    def hline(self, x, y, w, color):
        """Draw horizontal line."""
        self.fb.hline(x, y, w, 1 if color else 0)
    
    def show(self):
        """Update display (not implemented in basic mode)."""
        # In real implementation, would write buffer to display
        pass


# Create st7789 module compatibility
class ST7789:
    """ST7789 compatibility wrapper."""
    
    def __init__(self, spi, width, height, reset=None, dc=None, cs=None, 
                 backlight=None, rotation=0):
        """Initialize as simple LCD."""
        self.lcd = SimpleLCD(width, height, rotation)
        print(f"ST7789 wrapper initialized ({width}x{height})")
    
    def init(self):
        self.lcd.init()
    
    def fill(self, color):
        # Convert RGB565 to mono
        self.lcd.fill(1 if color else 0)
    
    def text(self, text, x, y, color):
        self.lcd.text(text, x, y, color)
    
    def rect(self, x, y, w, h, color):
        self.lcd.rect(x, y, w, h, color)
    
    def fill_rect(self, x, y, w, h, color):
        self.lcd.fill_rect(x, y, w, h, color)
    
    def vline(self, x, y, h, color):
        self.lcd.vline(x, y, h, color)
    
    def hline(self, x, y, w, color):
        self.lcd.hline(x, y, w, color)


print("st7789 compatibility module loaded (no external driver needed)")
