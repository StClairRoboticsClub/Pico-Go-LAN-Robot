"""
Pico-Go LAN Robot - Wi-Fi Connection Module
===========================================
Handles connection to Ubuntu hotspot with retry logic.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT
"""

import network
import time
import uasyncio as asyncio
from config import (
    WIFI_SSID,
    WIFI_PASSWORD,
    WIFI_TIMEOUT_MS,
    WIFI_RETRY_DELAY_MS,
    MDNS_HOSTNAME,
    MDNS_ENABLED
)
from utils import debug_print, format_ip, time_diff_ms


class WiFiManager:
    """
    Manages Wi-Fi connection to Ubuntu hotspot.
    """
    
    def __init__(self):
        """Initialize WiFi manager."""
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.ip = None
        self.connected = False
        self.rssi = 0
    
    async def connect(self, max_retries=3):
        """
        Connect to Wi-Fi network with retry logic.
        
        Args:
            max_retries: Maximum number of connection attempts
        
        Returns:
            IP address string if successful, None otherwise
        """
        retry_count = 0
        
        while retry_count < max_retries:
            debug_print(f"Attempting Wi-Fi connection (attempt {retry_count + 1}/{max_retries})...")
            
            if await self._attempt_connect():
                self.connected = True
                self.ip = self.wlan.ifconfig()[0]
                self.rssi = self._get_rssi()
                debug_print(f"Connected! IP: {self.ip}, RSSI: {self.rssi} dBm", force=True)
                
                # Setup mDNS if enabled
                if MDNS_ENABLED:
                    self._setup_mdns()
                
                return self.ip
            
            retry_count += 1
            if retry_count < max_retries:
                debug_print(f"Connection failed. Retrying in {WIFI_RETRY_DELAY_MS/1000}s...")
                await asyncio.sleep_ms(WIFI_RETRY_DELAY_MS)
        
        debug_print("Wi-Fi connection failed after all retries", force=True)
        return None
    
    async def _attempt_connect(self):
        """
        Single connection attempt.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            self.wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            
            start_time = time.ticks_ms()
            while not self.wlan.isconnected():
                if time_diff_ms(start_time, time.ticks_ms()) > WIFI_TIMEOUT_MS:
                    debug_print("Connection timeout")
                    return False
                await asyncio.sleep_ms(100)
            
            return True
        
        except Exception as e:
            debug_print(f"Connection error: {e}")
            return False
    
    def _setup_mdns(self):
        """
        Setup mDNS responder for hostname-based discovery.
        Allows robot to be found as picogo1.local, picogo2.local, etc.
        """
        try:
            import network
            mdns = network.mDNS()
            mdns.start(MDNS_HOSTNAME, "MicroPython Robot")
            mdns.add_service('_robot', '_udp', 8765, txt='robot')
            debug_print(f"mDNS enabled: {MDNS_HOSTNAME}.local", force=True)
        except ImportError:
            debug_print("mDNS not available on this MicroPython version", force=True)
        except Exception as e:
            debug_print(f"mDNS setup error: {e}", force=True)
    
    def _get_rssi(self):
        """
        Get current Wi-Fi signal strength.
        
        Returns:
            RSSI in dBm
        """
        try:
            # Note: RSSI retrieval may vary by MicroPython version
            # This is a placeholder - implement based on your MicroPython version
            return -50  # Placeholder value
        except:
            return -99
    
    def is_connected(self):
        """
        Check if Wi-Fi is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        self.connected = self.wlan.isconnected()
        return self.connected
    
    def get_ip(self):
        """
        Get current IP address.
        
        Returns:
            IP address string or None
        """
        if self.is_connected():
            return self.wlan.ifconfig()[0]
        return None
    
    def get_status(self):
        """
        Get comprehensive Wi-Fi status.
        
        Returns:
            Dictionary with connection status
        """
        if self.is_connected():
            ifconfig = self.wlan.ifconfig()
            return {
                "connected": True,
                "ip": ifconfig[0],
                "subnet": ifconfig[1],
                "gateway": ifconfig[2],
                "dns": ifconfig[3],
                "rssi": self._get_rssi(),
                "ssid": WIFI_SSID
            }
        else:
            return {
                "connected": False,
                "ip": None,
                "rssi": None,
                "ssid": WIFI_SSID
            }
    
    async def reconnect(self):
        """
        Attempt to reconnect if connection is lost.
        
        Returns:
            True if reconnected, False otherwise
        """
        debug_print("Attempting to reconnect Wi-Fi...")
        self.wlan.disconnect()
        await asyncio.sleep_ms(1000)
        return await self.connect(max_retries=3)
    
    def disconnect(self):
        """Disconnect from Wi-Fi network."""
        debug_print("Disconnecting Wi-Fi...")
        self.wlan.disconnect()
        self.wlan.active(False)
        self.connected = False
        self.ip = None


# Global WiFi manager instance
wifi_manager = None


async def initialize():
    """
    Initialize and connect Wi-Fi.
    
    Returns:
        WiFiManager instance
    """
    global wifi_manager
    wifi_manager = WiFiManager()
    await wifi_manager.connect()
    return wifi_manager


def get_manager():
    """
    Get the global WiFi manager instance.
    
    Returns:
        WiFiManager instance or None
    """
    return wifi_manager
