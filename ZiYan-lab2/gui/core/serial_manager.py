#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Serial Port Manager

Handles serial port communication with STM32 device.
Features:
- Auto-detection of CH340/STM devices
- Background thread for non-blocking I/O
- Qt signals for data reception
- Connection management
"""

import serial
import serial.tools.list_ports
from serial import Serial, SerialException
import threading
import time
from typing import Optional, List, Callable
from PyQt6.QtCore import QObject, pyqtSignal


class SerialManager(QObject):
    """Serial port manager with thread-safe operations"""
    
    # Qt Signals
    data_received = pyqtSignal(str)  # Emitted when data line received
    connection_changed = pyqtSignal(bool)  # Emitted when connection status changes
    error_occurred = pyqtSignal(str)  # Emitted when error occurs
    
    def __init__(self):
        super().__init__()
        self.serial_port: Optional[Serial] = None
        self.is_connected = False
        self.is_running = False
        self.read_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    @staticmethod
    def list_available_ports() -> List[dict]:
        """
        List all available serial ports
        
        Returns:
            List of dicts containing port info (device, name, description)
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'name': port.name,
                'description': port.description,
                'hwid': port.hwid
            })
        return ports
    
    @staticmethod
    def find_stm32_port(keywords: List[str] = None) -> Optional[str]:
        """
        Auto-detect STM32/CH340 device port
        
        Args:
            keywords: List of keywords to search in port description
            
        Returns:
            Port device name (e.g., 'COM3') or None if not found
        """
        if keywords is None:
            keywords = ["CH340", "STM", "USB-SERIAL", "USB Serial"]
        
        for port in serial.tools.list_ports.comports():
            port_info = f"{port.description} {port.hwid}".upper()
            
            for keyword in keywords:
                if keyword.upper() in port_info:
                    return port.device
        
        return None
    
    def connect(self, port: str, baudrate: int = 115200, timeout: float = 1.0) -> bool:
        """
        Connect to serial port
        
        Args:
            port: Port name (e.g., 'COM3')
            baudrate: Baud rate (default: 115200)
            timeout: Read timeout in seconds
            
        Returns:
            bool: True if connected successfully
        """
        if self.is_connected:
            self.error_occurred.emit("Already connected. Disconnect first.")
            return False
        
        try:
            self.serial_port = Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )
            
            self.is_connected = True
            self.is_running = True
            
            # Start background read thread
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            
            self.connection_changed.emit(True)
            print(f"✓ Connected to {port} at {baudrate} baud")
            return True
            
        except SerialException as e:
            self.error_occurred.emit(f"Connection failed: {str(e)}")
            print(f"✗ Connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from serial port"""
        if not self.is_connected:
            return
        
        # Stop read thread
        self.is_running = False
        
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=2.0)
        
        # Close serial port
        with self._lock:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
                self.serial_port = None
        
        self.is_connected = False
        self.connection_changed.emit(False)
        print("✓ Disconnected from serial port")
    
    def _read_loop(self) -> None:
        """Background thread to read serial data"""
        buffer = ""
        
        while self.is_running and self.is_connected:
            try:
                with self._lock:
                    if self.serial_port and self.serial_port.in_waiting > 0:
                        # Read available bytes
                        data = self.serial_port.read(self.serial_port.in_waiting)
                        
                        try:
                            # Decode as UTF-8
                            text = data.decode('utf-8', errors='ignore')
                            buffer += text
                            
                            # Process complete lines
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = line.strip()
                                
                                if line:  # Emit non-empty lines
                                    self.data_received.emit(line)
                        
                        except UnicodeDecodeError:
                            pass  # Ignore decode errors
                
                # Small sleep to prevent CPU hogging
                time.sleep(0.01)
                
            except SerialException as e:
                self.error_occurred.emit(f"Read error: {str(e)}")
                self.is_running = False
                break
            except Exception as e:
                self.error_occurred.emit(f"Unexpected error: {str(e)}")
                break
        
        # Cleanup on thread exit
        if self.is_connected:
            self.disconnect()
    
    def write(self, data: str) -> bool:
        """
        Write data to serial port
        
        Args:
            data: String to write (will be encoded as UTF-8)
            
        Returns:
            bool: True if successful
        """
        if not self.is_connected or not self.serial_port:
            self.error_occurred.emit("Not connected")
            return False
        
        try:
            with self._lock:
                self.serial_port.write(data.encode('utf-8'))
            return True
        except SerialException as e:
            self.error_occurred.emit(f"Write error: {str(e)}")
            return False
    
    def is_port_available(self, port: str) -> bool:
        """
        Check if a port is available
        
        Args:
            port: Port name to check
            
        Returns:
            bool: True if port exists
        """
        available_ports = [p['device'] for p in self.list_available_ports()]
        return port in available_ports
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.disconnect()


if __name__ == "__main__":
    """Test serial manager"""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    print("=== Serial Manager Test ===\n")
    
    app = QApplication(sys.argv)
    manager = SerialManager()
    
    # Test 1: List ports
    print("1. Available ports:")
    ports = manager.list_available_ports()
    for port in ports:
        print(f"   - {port['device']}: {port['description']}")
    
    # Test 2: Auto-detect
    print("\n2. Auto-detect STM32/CH340:")
    auto_port = manager.find_stm32_port()
    if auto_port:
        print(f"   ✓ Found: {auto_port}")
    else:
        print("   ✗ Not found")
    
    # Test 3: Connect (if port available)
    if auto_port:
        print(f"\n3. Testing connection to {auto_port}:")
        
        def on_data(line):
            print(f"   RX: {line}")
        
        def on_error(msg):
            print(f"   ERROR: {msg}")
        
        manager.data_received.connect(on_data)
        manager.error_occurred.connect(on_error)
        
        if manager.connect(auto_port):
            print("   Listening for 5 seconds...")
            
            # Run event loop for 5 seconds
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(5000, lambda: (manager.disconnect(), app.quit()))
            sys.exit(app.exec())
        else:
            print("   Connection failed")
    else:
        print("\n3. Skipping connection test (no device found)")
    
    print("\n✓ Test completed!")
