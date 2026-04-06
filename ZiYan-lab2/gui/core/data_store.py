#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Store

Manages sensor data storage using pandas DataFrame with circular buffer.
Provides efficient data access for charts and statistics.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from collections import deque
from core.data_parser import SensorData


class DataStore:
    """Circular buffer-based data store using pandas"""
    
    def __init__(self, max_history_minutes: int = 60):
        """
        Initialize data store
        
        Args:
            max_history_minutes: Maximum history to keep in memory (minutes)
        """
        self.max_history_minutes = max_history_minutes
        
        # Main data storage
        self.df = pd.DataFrame(columns=[
            'timestamp', 'temperature', 'humidity', 'oled_state'
        ])
        
        # Fast circular buffer for recent data
        self.max_buffer_size = max_history_minutes * 30  # Assuming 2-second interval
        self.buffer: deque = deque(maxlen=self.max_buffer_size)
        
        # Statistics cache
        self._stats_cache = None
        self._stats_cache_time = None
        self._cache_validity_sec = 1.0  # Cache valid for 1 second
        
        # Packet counter
        self.packet_count = 0
        self.start_time = datetime.now()
    
    def add(self, data: SensorData) -> None:
        """
        Add new sensor data point
        
        Args:
            data: SensorData object
        """
        # Add to buffer
        self.buffer.append({
            'timestamp': data.timestamp,
            'temperature': data.temperature,
            'humidity': data.humidity,
            'oled_state': data.oled_state
        })
        
        self.packet_count += 1
        
        # Invalidate stats cache
        self._stats_cache = None
        
        # Periodically rebuild DataFrame from buffer
        if len(self.buffer) % 50 == 0:  # Every 50 samples
            self._rebuild_dataframe()
    
    def _rebuild_dataframe(self) -> None:
        """Rebuild DataFrame from buffer (for efficient querying)"""
        if not self.buffer:
            return
        
        self.df = pd.DataFrame(list(self.buffer))
        
        # Remove old data beyond max_history
        if not self.df.empty:
            cutoff_time = datetime.now() - timedelta(minutes=self.max_history_minutes)
            self.df = self.df[self.df['timestamp'] >= cutoff_time]
    
    def get_recent(self, minutes: int = 5) -> pd.DataFrame:
        """
        Get recent data within specified time window
        
        Args:
            minutes: Number of minutes to retrieve
            
        Returns:
            DataFrame with recent data
        """
        if not self.buffer:
            return pd.DataFrame(columns=['timestamp', 'temperature', 'humidity', 'oled_state'])
        
        # Get data from buffer
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent_data = [
            item for item in self.buffer 
            if item['timestamp'] >= cutoff_time
        ]
        
        return pd.DataFrame(recent_data) if recent_data else pd.DataFrame()
    
    def get_all(self) -> pd.DataFrame:
        """
        Get all stored data
        
        Returns:
            DataFrame with all data
        """
        self._rebuild_dataframe()
        return self.df.copy()
    
    def get_latest(self) -> Optional[dict]:
        """
        Get the most recent data point
        
        Returns:
            dict: Latest data or None if empty
        """
        if not self.buffer:
            return None
        
        return dict(self.buffer[-1])
    
    def get_statistics(self, force_refresh: bool = False) -> dict:
        """
        Get statistical summary of stored data
        
        Args:
            force_refresh: If True, bypass cache
            
        Returns:
            dict: Statistics (temp_max, temp_min, temp_avg, humi_max, humi_min, humi_avg)
        """
        # Check cache
        now = datetime.now()
        if (not force_refresh and 
            self._stats_cache is not None and 
            self._stats_cache_time is not None):
            
            elapsed = (now - self._stats_cache_time).total_seconds()
            if elapsed < self._cache_validity_sec:
                return self._stats_cache
        
        # Calculate statistics
        if not self.buffer:
            return {
                'temp_max': 0.0,
                'temp_min': 0.0,
                'temp_avg': 0.0,
                'humi_max': 0.0,
                'humi_min': 0.0,
                'humi_avg': 0.0,
                'packet_count': 0,
                'sample_rate': 0.0
            }
        
        df = pd.DataFrame(list(self.buffer))
        
        stats = {
            'temp_max': float(df['temperature'].max()),
            'temp_min': float(df['temperature'].min()),
            'temp_avg': float(df['temperature'].mean()),
            'humi_max': float(df['humidity'].max()),
            'humi_min': float(df['humidity'].min()),
            'humi_avg': float(df['humidity'].mean()),
            'packet_count': self.packet_count,
            'sample_rate': self._calculate_sample_rate()
        }
        
        # Update cache
        self._stats_cache = stats
        self._stats_cache_time = now
        
        return stats
    
    def _calculate_sample_rate(self) -> float:
        """
        Calculate sampling rate (packets per second)
        
        Returns:
            float: Sample rate in Hz
        """
        if self.packet_count == 0:
            return 0.0
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed > 0:
            return self.packet_count / elapsed
        
        return 0.0
    
    def clear(self) -> None:
        """Clear all stored data"""
        self.buffer.clear()
        self.df = pd.DataFrame(columns=['timestamp', 'temperature', 'humidity', 'oled_state'])
        self.packet_count = 0
        self.start_time = datetime.now()
        self._stats_cache = None
        print("Data store cleared")
    
    def get_count(self) -> int:
        """Get number of data points in buffer"""
        return len(self.buffer)
    
    def is_empty(self) -> bool:
        """Check if data store is empty"""
        return len(self.buffer) == 0


if __name__ == "__main__":
    """Test data store"""
    from datetime import datetime
    from core.data_parser import SensorData
    import time
    
    print("=== Data Store Test ===\n")
    
    store = DataStore(max_history_minutes=5)
    
    # Test 1: Add data
    print("1. Adding test data points...")
    for i in range(10):
        data = SensorData(
            timestamp=datetime.now(),
            temperature=20.0 + i * 0.5,
            humidity=50.0 + i * 2.0,
            oled_state=(i % 2 == 0),
            raw_line=f"DATA,{20.0 + i * 0.5},{50.0 + i * 2.0},{i % 2}"
        )
        store.add(data)
        time.sleep(0.01)  # Small delay
    
    print(f"   ✓ Added {store.get_count()} data points")
    
    # Test 2: Get statistics
    print("\n2. Statistics:")
    stats = store.get_statistics()
    print(f"   Temperature: Min={stats['temp_min']:.1f}, Max={stats['temp_max']:.1f}, Avg={stats['temp_avg']:.1f}")
    print(f"   Humidity: Min={stats['humi_min']:.1f}, Max={stats['humi_max']:.1f}, Avg={stats['humi_avg']:.1f}")
    print(f"   Packets: {stats['packet_count']}")
    print(f"   Sample Rate: {stats['sample_rate']:.2f} Hz")
    
    # Test 3: Get latest
    print("\n3. Latest data point:")
    latest = store.get_latest()
    if latest:
        print(f"   Temp: {latest['temperature']:.1f}°C, Humi: {latest['humidity']:.1f}%")
    
    # Test 4: Get recent DataFrame
    print("\n4. Recent data (last 5 minutes):")
    df = store.get_recent(minutes=5)
    print(f"   Retrieved {len(df)} rows")
    if not df.empty:
        print(f"   First row: {df.iloc[0]['temperature']:.1f}°C")
        print(f"   Last row: {df.iloc[-1]['temperature']:.1f}°C")
    
    # Test 5: Clear
    print("\n5. Clearing data store...")
    store.clear()
    print(f"   Data count after clear: {store.get_count()}")
    
    print("\n✓ Test completed!")
