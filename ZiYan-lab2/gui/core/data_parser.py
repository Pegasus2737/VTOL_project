#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Parser

Parses incoming serial data from STM32 DHT11 sensor.
Expected format: DATA,<temperature>,<humidity>,<oled_state>
Example: DATA,25.3,61.0,1
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SensorData:
    """Parsed sensor data structure"""
    timestamp: datetime
    temperature: float
    humidity: float
    oled_state: bool
    raw_line: str
    
    def __str__(self) -> str:
        return (f"[{self.timestamp.strftime('%H:%M:%S')}] "
                f"Temp: {self.temperature:.1f}°C, "
                f"Humidity: {self.humidity:.1f}%, "
                f"OLED: {'ON' if self.oled_state else 'OFF'}")


class DataParser:
    """Parser for STM32 sensor data"""
    
    # Message type identifiers
    DATA_PREFIX = "DATA"
    DEBUG_PREFIX = "DEBUG"
    BOOT_PREFIX = "[BOOT]"
    
    def __init__(self):
        self.last_valid_data: Optional[SensorData] = None
        self.total_parsed = 0
        self.parse_errors = 0
    
    def parse(self, line: str) -> Optional[SensorData]:
        """
        Parse a line of serial data
        
        Args:
            line: Raw line from serial port (already stripped)
            
        Returns:
            SensorData object if successfully parsed, None otherwise
        """
        if not line:
            return None
        
        # Check if it's a DATA line
        if line.startswith(self.DATA_PREFIX):
            return self._parse_data_line(line)
        
        # Non-data lines (DEBUG, BOOT messages) are not parsed
        # They should be displayed in Terminal tab but not processed
        return None
    
    def _parse_data_line(self, line: str) -> Optional[SensorData]:
        """
        Parse DATA line: DATA,<temp>,<humidity>,<state>
        
        Args:
            line: Raw DATA line
            
        Returns:
            SensorData object if valid, None if parse error
        """
        try:
            # Remove prefix and split by comma
            # Expected: "DATA,25.3,61.0,1"
            parts = line.split(',')
            
            if len(parts) != 4:
                raise ValueError(f"Expected 4 parts, got {len(parts)}")
            
            prefix, temp_str, humi_str, state_str = parts
            
            if prefix != self.DATA_PREFIX:
                raise ValueError(f"Invalid prefix: {prefix}")
            
            # Parse values
            temperature = float(temp_str)
            humidity = float(humi_str)
            oled_state = bool(int(state_str))
            
            # Validate ranges (sanity check)
            if not (-40 <= temperature <= 125):
                raise ValueError(f"Temperature out of range: {temperature}")
            
            if not (0 <= humidity <= 100):
                raise ValueError(f"Humidity out of range: {humidity}")
            
            # Create data object
            data = SensorData(
                timestamp=datetime.now(),
                temperature=temperature,
                humidity=humidity,
                oled_state=oled_state,
                raw_line=line
            )
            
            self.last_valid_data = data
            self.total_parsed += 1
            
            return data
            
        except (ValueError, IndexError) as e:
            self.parse_errors += 1
            print(f"Parse error: {e} | Line: {line}")
            return None
    
    def is_data_line(self, line: str) -> bool:
        """
        Check if line is a DATA line
        
        Args:
            line: Line to check
            
        Returns:
            bool: True if DATA line
        """
        return line.startswith(self.DATA_PREFIX)
    
    def is_debug_line(self, line: str) -> bool:
        """
        Check if line is a DEBUG message
        
        Args:
            line: Line to check
            
        Returns:
            bool: True if DEBUG line
        """
        return self.DEBUG_PREFIX in line
    
    def is_boot_line(self, line: str) -> bool:
        """
        Check if line is a BOOT message
        
        Args:
            line: Line to check
            
        Returns:
            bool: True if BOOT line
        """
        return self.BOOT_PREFIX in line
    
    def get_stats(self) -> dict:
        """
        Get parser statistics
        
        Returns:
            dict: Statistics (total_parsed, parse_errors, success_rate)
        """
        total = self.total_parsed + self.parse_errors
        success_rate = (self.total_parsed / total * 100) if total > 0 else 0.0
        
        return {
            'total_parsed': self.total_parsed,
            'parse_errors': self.parse_errors,
            'total_lines': total,
            'success_rate': success_rate
        }
    
    def reset_stats(self) -> None:
        """Reset parser statistics"""
        self.total_parsed = 0
        self.parse_errors = 0


if __name__ == "__main__":
    """Test data parser"""
    print("=== Data Parser Test ===\n")
    
    parser = DataParser()
    
    # Test cases
    test_lines = [
        "DATA,25.3,61.0,1",           # Valid
        "DATA,24.8,58.5,0",           # Valid
        "DATA,35.2,75.3,1",           # Valid
        "DEBUG: [ERR -1] No Response", # Debug (not parsed)
        "[BOOT] Hello from STM32",    # Boot message (not parsed)
        "DATA,invalid,61.0,1",        # Invalid temperature
        "DATA,25.3",                  # Missing fields
        "DATA,25.3,150.0,1",          # Humidity out of range
        "",                           # Empty line
        "DATA,22.1,45.6,0",           # Valid
    ]
    
    print("1. Parsing test lines:\n")
    for i, line in enumerate(test_lines, 1):
        print(f"   [{i}] Input: {line!r}")
        
        result = parser.parse(line)
        if result:
            print(f"       ✓ {result}")
        elif parser.is_debug_line(line):
            print(f"       → DEBUG message (not parsed)")
        elif parser.is_boot_line(line):
            print(f"       → BOOT message (not parsed)")
        else:
            print(f"       ✗ Parse failed or empty")
        print()
    
    print("\n2. Parser statistics:")
    stats = parser.get_stats()
    print(f"   Total parsed: {stats['total_parsed']}")
    print(f"   Parse errors: {stats['parse_errors']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")
    
    print("\n3. Last valid data:")
    if parser.last_valid_data:
        print(f"   {parser.last_valid_data}")
    
    print("\n✓ Test completed!")
