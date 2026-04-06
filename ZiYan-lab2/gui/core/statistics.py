#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistics Module

Calculates real-time statistics for temperature and humidity data.
Features:
- Min/Max/Average calculations
- Packet counting
- Sample rate estimation
"""

from typing import Optional, Dict
from datetime import datetime
from collections import deque


class Statistics:
    """Real-time statistics calculator"""
    
    def __init__(self):
        # Temperature statistics
        self.temp_min: Optional[float] = None
        self.temp_max: Optional[float] = None
        self.temp_sum: float = 0.0
        
        # Humidity statistics
        self.humi_min: Optional[float] = None
        self.humi_max: Optional[float] = None
        self.humi_sum: float = 0.0
        
        # Counters
        self.packet_count: int = 0
        self.start_time: datetime = datetime.now()
        
        # For average calculation (sliding window)
        self.temp_history: deque = deque(maxlen=100)  # Last 100 samples
        self.humi_history: deque = deque(maxlen=100)
        
        # Sample rate tracking
        self.last_packet_time: Optional[datetime] = None
        self.sample_intervals: deque = deque(maxlen=10)  # Last 10 intervals
    
    def update(self, temperature: float, humidity: float) -> None:
        """
        Update statistics with new data point
        
        Args:
            temperature: Temperature value in Celsius
            humidity: Humidity value in percentage
        """
        now = datetime.now()
        
        # Update temperature stats
        if self.temp_min is None or temperature < self.temp_min:
            self.temp_min = temperature
        if self.temp_max is None or temperature > self.temp_max:
            self.temp_max = temperature
        
        self.temp_history.append(temperature)
        self.temp_sum += temperature
        
        # Update humidity stats
        if self.humi_min is None or humidity < self.humi_min:
            self.humi_min = humidity
        if self.humi_max is None or humidity > self.humi_max:
            self.humi_max = humidity
        
        self.humi_history.append(humidity)
        self.humi_sum += humidity
        
        # Update packet count
        self.packet_count += 1
        
        # Calculate sample interval
        if self.last_packet_time is not None:
            interval = (now - self.last_packet_time).total_seconds()
            if interval > 0:  # Avoid division by zero
                self.sample_intervals.append(interval)
        
        self.last_packet_time = now
    
    def get_temperature_stats(self) -> Dict[str, float]:
        """
        Get temperature statistics
        
        Returns:
            dict: {'min', 'max', 'avg'}
        """
        return {
            'min': self.temp_min if self.temp_min is not None else 0.0,
            'max': self.temp_max if self.temp_max is not None else 0.0,
            'avg': self._calculate_average(self.temp_history)
        }
    
    def get_humidity_stats(self) -> Dict[str, float]:
        """
        Get humidity statistics
        
        Returns:
            dict: {'min', 'max', 'avg'}
        """
        return {
            'min': self.humi_min if self.humi_min is not None else 0.0,
            'max': self.humi_max if self.humi_max is not None else 0.0,
            'avg': self._calculate_average(self.humi_history)
        }
    
    def get_packet_count(self) -> int:
        """Get total packet count"""
        return self.packet_count
    
    def get_sample_rate(self) -> float:
        """
        Get estimated sample rate in Hz
        
        Returns:
            float: Sample rate (packets per second)
        """
        if not self.sample_intervals:
            # Fallback: calculate from total time
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed > 0 and self.packet_count > 0:
                return self.packet_count / elapsed
            return 0.0
        
        # Use average of recent intervals
        avg_interval = sum(self.sample_intervals) / len(self.sample_intervals)
        if avg_interval > 0:
            return 1.0 / avg_interval
        
        return 0.0
    
    def get_all_stats(self) -> Dict[str, any]:
        """
        Get all statistics in one dict
        
        Returns:
            dict: All statistics
        """
        temp_stats = self.get_temperature_stats()
        humi_stats = self.get_humidity_stats()
        
        return {
            'temp_min': temp_stats['min'],
            'temp_max': temp_stats['max'],
            'temp_avg': temp_stats['avg'],
            'humi_min': humi_stats['min'],
            'humi_max': humi_stats['max'],
            'humi_avg': humi_stats['avg'],
            'packet_count': self.packet_count,
            'sample_rate': self.get_sample_rate()
        }
    
    def reset(self) -> None:
        """Reset all statistics"""
        self.temp_min = None
        self.temp_max = None
        self.temp_sum = 0.0
        
        self.humi_min = None
        self.humi_max = None
        self.humi_sum = 0.0
        
        self.packet_count = 0
        self.start_time = datetime.now()
        
        self.temp_history.clear()
        self.humi_history.clear()
        
        self.last_packet_time = None
        self.sample_intervals.clear()
    
    @staticmethod
    def _calculate_average(values: deque) -> float:
        """
        Calculate average from deque
        
        Args:
            values: Deque of values
            
        Returns:
            float: Average value
        """
        if not values:
            return 0.0
        return sum(values) / len(values)


if __name__ == "__main__":
    """Test statistics module"""
    import time
    
    print("=== Statistics Module Test ===\n")
    
    stats = Statistics()
    
    # Test 1: Add sample data
    print("1. Adding sample data points...")
    test_data = [
        (20.0, 50.0),
        (21.5, 52.0),
        (22.0, 54.0),
        (23.5, 56.0),
        (24.0, 58.0),
        (25.5, 60.0),
        (26.0, 62.0),
        (24.5, 59.0),
        (23.0, 57.0),
        (22.5, 55.0),
    ]
    
    for temp, humi in test_data:
        stats.update(temp, humi)
        time.sleep(0.01)  # Simulate 10ms interval
    
    print(f"   Added {len(test_data)} data points")
    
    # Test 2: Get temperature stats
    print("\n2. Temperature statistics:")
    temp_stats = stats.get_temperature_stats()
    print(f"   Min: {temp_stats['min']:.1f}°C")
    print(f"   Max: {temp_stats['max']:.1f}°C")
    print(f"   Avg: {temp_stats['avg']:.1f}°C")
    
    # Test 3: Get humidity stats
    print("\n3. Humidity statistics:")
    humi_stats = stats.get_humidity_stats()
    print(f"   Min: {humi_stats['min']:.1f}%")
    print(f"   Max: {humi_stats['max']:.1f}%")
    print(f"   Avg: {humi_stats['avg']:.1f}%")
    
    # Test 4: Get packet info
    print("\n4. Packet information:")
    print(f"   Total packets: {stats.get_packet_count()}")
    print(f"   Sample rate: {stats.get_sample_rate():.2f} Hz")
    
    # Test 5: Get all stats
    print("\n5. All statistics:")
    all_stats = stats.get_all_stats()
    for key, value in all_stats.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2f}")
        else:
            print(f"   {key}: {value}")
    
    # Test 6: Reset
    print("\n6. Resetting statistics...")
    stats.reset()
    print(f"   Packet count after reset: {stats.get_packet_count()}")
    
    print("\n✓ Test completed!")
