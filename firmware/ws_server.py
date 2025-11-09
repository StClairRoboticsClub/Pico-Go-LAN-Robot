"""
Pico-Go LAN Robot - WebSocket Server Module
===========================================
Async WebSocket server for receiving control commands.

Author: Jeremy Dueck
Organization: St. Clair College Robotics Club
License: MIT

Note: Requires uwebsocket library for MicroPython WebSocket support.
Install via: mpremote mip install uwebsocket
"""

import json
import uasyncio as asyncio
from config import WEBSOCKET_PORT, WEBSOCKET_HOST, STATE_CLIENT_OK, STATE_DRIVING, STATE_LINK_LOST
from utils import debug_print


class WebSocketServer:
    """
    WebSocket server for robot control.
    """
    
    def __init__(self, motor_controller, safety_controller, lcd_display, underglow=None):
        """
        Initialize WebSocket server.
        
        Args:
            motor_controller: Motor controller instance
            safety_controller: Safety controller instance
            lcd_display: LCD display instance
            underglow: Underglow LED controller instance (optional)
        """
        self.motor_controller = motor_controller
        self.safety_controller = safety_controller
        self.lcd_display = lcd_display
        self.underglow = underglow
        self.server = None
        self.client = None
        self.running = False
        self.packets_received = 0
        self.last_seq = 0
        
        debug_print("WebSocket server initialized")
    
    async def start(self):
        """Start the WebSocket server."""
        try:
            debug_print(f"Starting WebSocket server on {WEBSOCKET_HOST}:{WEBSOCKET_PORT}", force=True)
            
            # Start server (implementation depends on uwebsocket library)
            # This is a simplified version - actual implementation will use uwebsocket
            asyncio.create_task(self._accept_connections())
            
            self.running = True
            debug_print("WebSocket server started", force=True)
            
        except Exception as e:
            debug_print(f"Error starting WebSocket server: {e}", force=True)
    
    async def _accept_connections(self):
        """Accept incoming WebSocket connections."""
        # Placeholder for actual WebSocket server implementation
        # In production, use uwebsocket library
        debug_print("Waiting for client connections...")
        
        while self.running:
            # TODO: Implement actual WebSocket server using uwebsocket
            # server = await websocket.serve(self._handle_client, WEBSOCKET_HOST, WEBSOCKET_PORT)
            await asyncio.sleep(1)
    
    async def handle_client(self, reader, writer):
        """
        Handle connected client.
        
        Args:
            reader: Async stream reader
            writer: Async stream writer
        """
        try:
            debug_print("Client connected", force=True)
            self.client = (reader, writer)
            
            if self.lcd_display:
                self.lcd_display.set_state(STATE_CLIENT_OK)
            
            # Read loop
            while self.running:
                try:
                    # Read message (simplified - actual WebSocket framing needed)
                    data = await reader.read(1024)
                    if not data:
                        break
                    
                    # Process message
                    await self._process_message(data.decode())
                    
                except Exception as e:
                    debug_print(f"Error reading message: {e}")
                    break
            
        except Exception as e:
            debug_print(f"Client handler error: {e}", force=True)
        
        finally:
            debug_print("Client disconnected", force=True)
            self.client = None
            if writer:
                writer.close()
                await writer.wait_closed()
    
    async def _process_message(self, message):
        """
        Process received WebSocket message.
        
        Args:
            message: JSON message string
        """
        try:
            # Parse JSON
            packet = json.loads(message)
            
            # Validate packet
            if not self._validate_packet(packet):
                debug_print("Invalid packet received")
                return
            
            # Extract command
            cmd = packet.get("cmd")
            
            if cmd == "drive":
                await self._handle_drive_command(packet)
            elif cmd == "stop":
                await self._handle_stop_command(packet)
            elif cmd == "ping":
                await self._handle_ping_command(packet)
            else:
                debug_print(f"Unknown command: {cmd}")
            
            # Send acknowledgment
            await self._send_ack(packet)
            
        except json.JSONDecodeError as e:
            debug_print(f"JSON decode error: {e}")
        except Exception as e:
            debug_print(f"Message processing error: {e}")
    
    def _validate_packet(self, packet):
        """
        Validate incoming packet structure.
        
        Args:
            packet: Parsed JSON packet
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["cmd", "seq"]
        return all(field in packet for field in required_fields)
    
    async def _handle_drive_command(self, packet):
        """
        Handle drive command.
        
        Args:
            packet: Drive command packet
        """
        try:
            # Check timestamp to reject stale commands (max age: 500ms)
            timestamp = packet.get("ts", 0)
            if timestamp > 0:
                import time
                current_time = int(time.time() * 1000)  # Current time in milliseconds
                age_ms = current_time - timestamp
                
                if age_ms > 500:  # Reject commands older than 500ms
                    debug_print(f"Stale command rejected (age: {age_ms}ms)")
                    return
                elif age_ms < -1000:  # Clock skew detected
                    debug_print(f"Clock skew detected: {age_ms}ms")
                    # Continue anyway, but warn
            
            axes = packet.get("axes", {})
            throttle = axes.get("throttle", 0.0)
            steer = axes.get("steer", 0.0)
            
            # Feed watchdog
            self.safety_controller.feed_watchdog()
            
            # Update motor control
            if not self.motor_controller.enabled:
                self.motor_controller.enable()
            
            self.motor_controller.drive(throttle, steer)
            
            # Update display
            if self.lcd_display:
                self.lcd_display.set_state(STATE_DRIVING, throttle=throttle, steer=steer)
            
            self.packets_received += 1
            self.last_seq = packet.get("seq", 0)
            
        except Exception as e:
            debug_print(f"Drive command error: {e}")
    
    async def _handle_stop_command(self, packet):
        """
        Handle stop command.
        
        Args:
            packet: Stop command packet
        """
        debug_print("Stop command received")
        self.motor_controller.stop()
        self.safety_controller.feed_watchdog()
    
    async def _handle_ping_command(self, packet):
        """
        Handle ping command.
        
        Args:
            packet: Ping command packet
        """
        # Just send acknowledgment
        self.safety_controller.feed_watchdog()
    
    async def _send_ack(self, packet):
        """
        Send acknowledgment to client.
        
        Args:
            packet: Original packet to acknowledge
        """
        if not self.client:
            return
        
        try:
            reader, writer = self.client
            
            # Get current status
            motor_status = self.motor_controller.get_status()
            safety_status = self.safety_controller.get_status()
            
            # Build response
            response = {
                "seq_ack": packet.get("seq", 0),
                "state": "DRIVING" if not safety_status["watchdog"]["timed_out"] else "LINK_LOST",
                "motor_enabled": motor_status["enabled"],
                "packets_received": self.packets_received
            }
            
            # Send response (simplified - actual WebSocket framing needed)
            message = json.dumps(response) + "\n"
            writer.write(message.encode())
            await writer.drain()
            
        except Exception as e:
            debug_print(f"Error sending ACK: {e}")
    
    def stop(self):
        """Stop the WebSocket server."""
        debug_print("Stopping WebSocket server...")
        self.running = False
        if self.client:
            _, writer = self.client
            if writer:
                writer.close()
    
    def get_status(self):
        """
        Get server status.
        
        Returns:
            Dictionary with server status
        """
        return {
            "running": self.running,
            "client_connected": self.client is not None,
            "packets_received": self.packets_received,
            "last_seq": self.last_seq
        }


# Simple TCP-based implementation (fallback if uwebsocket not available)
async def udp_server(motor_controller, safety_controller, lcd_display, underglow=None):
    """
    Optimized UDP server for low-latency control (fire-and-forget protocol).
    
    Args:
        motor_controller: Motor controller instance
        safety_controller: Safety controller instance  
        lcd_display: LCD display instance
        underglow: Underglow LED controller instance (optional)
    """
    import socket
    import select
    
    debug_print("Starting UDP server (low latency mode)", force=True)
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((WEBSOCKET_HOST, WEBSOCKET_PORT))
    sock.setblocking(False)  # Non-blocking for async operation
    
    debug_print(f"UDP server listening on {WEBSOCKET_HOST}:{WEBSOCKET_PORT}", force=True)
    
    client_connected = False
    last_seq = 0
    packets_received = 0
    packets_lost = 0
    
    # Main receive loop
    while True:
        try:
            # Use select to check if data is available (proper way for non-blocking)
            ready = select.select([sock], [], [], 0)  # 0 = non-blocking poll
            
            if ready[0]:  # If socket has data ready
                # Receive data
                data, addr = sock.recvfrom(1024)
                
                if not client_connected:
                    debug_print(f"UDP client connected from {addr}", force=True)
                    client_connected = True
                    if lcd_display:
                        lcd_display.set_state(STATE_CLIENT_OK)
                    if underglow:
                        underglow.set_state(STATE_CLIENT_OK)
                
                try:
                    packet = json.loads(data.decode().strip())
                    
                    # Track packet loss
                    seq = packet.get("seq", 0)
                    if seq > last_seq + 1:
                        packets_lost += seq - last_seq - 1
                    last_seq = seq
                    packets_received += 1
                    
                    cmd = packet.get("cmd")
                    if cmd == "discover":
                        # Respond to broadcast discovery requests
                        try:
                            from config import ROBOT_ID, MDNS_HOSTNAME
                            response = json.dumps({
                                "type": "robot_info",
                                "robot_id": ROBOT_ID,
                                "hostname": MDNS_HOSTNAME,
                                "version": "1.0"
                            }) + "\n"
                            sock.sendto(response.encode(), addr)
                            debug_print(f"Discovery response sent to {addr}", force=True)
                        except Exception as e:
                            debug_print(f"Discovery response error: {e}", force=True)
                        continue
                    
                    elif cmd == "drive":
                        axes = packet.get("axes", {})
                        throttle = axes.get("throttle", 0.0)
                        steer = axes.get("steer", 0.0)
                        
                        # DEBUG: Print every 30th packet
                        if packets_received % 30 == 0:
                            debug_print(f"Drive cmd: T={throttle:.2f} S={steer:.2f} PKT={packets_received}")
                        
                        # Feed watchdog FIRST (critical for safety)
                        safety_controller.feed_watchdog()
                        
                        # Enable motors if needed
                        if not motor_controller.enabled:
                            motor_controller.enable()
                            debug_print("Motors enabled", force=True)
                        
                        # Execute drive command
                        motor_controller.drive(throttle, steer)
                        
                        # Update LCD (throttled internally)
                        if lcd_display:
                            lcd_display.set_state(STATE_DRIVING, throttle=throttle, steer=steer)
                        
                        # Update underglow on first drive command only (avoid overhead)
                        if underglow and not motor_controller.enabled:
                            underglow.set_state(STATE_DRIVING)
                    
                except Exception as e:
                    debug_print(f"Packet processing error: {e}", force=True)
            
        except Exception as e:
            debug_print(f"UDP receive error: {e}", force=True)
        
        # Yield control to other tasks
        await asyncio.sleep_ms(1)  # 1ms yield for better responsiveness


async def handle_tcp_client(reader, writer, motor_controller, safety_controller, lcd_display):
    """
    Handle TCP client connection.
    
    Args:
        reader: Stream reader
        writer: Stream writer
        motor_controller: Motor controller instance
        safety_controller: Safety controller instance
        lcd_display: LCD display instance
    """
    addr = writer.get_extra_info('peername')
    debug_print(f"TCP client connected from {addr}", force=True)
    
    # Enable TCP_NODELAY for low latency (if supported)
    # Note: MicroPython may not support all socket options
    try:
        import socket
        sock = writer.get_extra_info('socket')
        if sock and hasattr(socket, 'TCP_NODELAY'):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            debug_print("TCP_NODELAY enabled", force=True)
    except (AttributeError, OSError) as e:
        # MicroPython doesn't support TCP_NODELAY, continue anyway
        debug_print(f"TCP_NODELAY not available: {e}")
    
    if lcd_display:
        lcd_display.set_state(STATE_CLIENT_OK)
    
    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            
            try:
                packet = json.loads(data.decode().strip())
                
                cmd = packet.get("cmd")
                if cmd == "drive":
                    # Check timestamp to reject stale commands (max age: 200ms)
                    timestamp = packet.get("ts", 0)
                    if timestamp > 0:
                        import time
                        current_time = int(time.time() * 1000)  # Current time in milliseconds
                        age_ms = current_time - timestamp
                        
                        if age_ms > 200:  # Reject commands older than 200ms
                            debug_print(f"Stale command rejected (age: {age_ms}ms)")
                            continue  # Skip this command, don't feed watchdog
                        elif age_ms < -1000:  # Clock skew detected
                            debug_print(f"Clock skew detected: {age_ms}ms")
                            # Continue anyway, but warn
                    
                    axes = packet.get("axes", {})
                    throttle = axes.get("throttle", 0.0)
                    steer = axes.get("steer", 0.0)
                    
                    safety_controller.feed_watchdog()
                    
                    if not motor_controller.enabled:
                        motor_controller.enable()
                    
                    motor_controller.drive(throttle, steer)
                    
                    if lcd_display:
                        lcd_display.set_state(STATE_DRIVING, throttle=throttle, steer=steer)
                
                # No ACK needed - fire and forget for maximum performance
                # Removing ACK reduces latency significantly
                
            except Exception as e:
                debug_print(f"Packet processing error: {e}")
    
    except Exception as e:
        debug_print(f"Client error: {e}", force=True)
    
    finally:
        debug_print("TCP client disconnected", force=True)
        
        # Stop motors immediately on disconnect
        motor_controller.stop()
        debug_print("Motors stopped due to disconnect")
        
        # Update display to show link lost
        if lcd_display:
            lcd_display.set_state(STATE_LINK_LOST)
        
        writer.close()
        await writer.wait_closed()


# Global server instance
ws_server = None


def initialize(motor_controller, safety_controller, lcd_display, underglow=None):
    """
    Initialize the global WebSocket server.
    
    Args:
        motor_controller: Motor controller instance
        safety_controller: Safety controller instance
        lcd_display: LCD display instance
        underglow: Underglow LED controller instance (optional)
    
    Returns:
        WebSocketServer instance
    """
    global ws_server
    ws_server = WebSocketServer(motor_controller, safety_controller, lcd_display, underglow)
    return ws_server


def get_server():
    """
    Get the global WebSocket server instance.
    
    Returns:
        WebSocketServer instance or None
    """
    return ws_server
