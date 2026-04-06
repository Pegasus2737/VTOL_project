#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alarm Manager

Manages temperature and humidity alarms:
- Threshold checking
- Alarm latch mechanism
- Alarm event logging to CSV
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import csv
from PyQt6.QtCore import QObject, pyqtSignal
from utils.file_utils import FileUtils


class AlarmType:
    """Alarm type constants"""
    TEMPERATURE_HIGH = "Temperature High"
    HUMIDITY_HIGH = "Humidity High"


class AlarmManager(QObject):
    """Alarm management system"""
    
    # Signals
    alarm_triggered = pyqtSignal(str, float, float, str)  # type, value, threshold, message
    alarm_cleared = pyqtSignal(str)  # type
    
    def __init__(self, base_path: str = "./data"):
        """
        Initialize alarm manager
        
        Args:
            base_path: Base path for alarm log files
        """
        super().__init__()
        self.base_path = base_path
        
        # Thresholds
        self.temp_high_threshold: float = 35.0
        self.humi_high_threshold: float = 80.0
        
        # Latch states
        self.latch_enabled: bool = True
        self.temp_alarm_latched: bool = False
        self.humi_alarm_latched: bool = False
        
        # Alarm log file
        self.alarm_log_path: Optional[Path] = None
        self._ensure_alarm_log()
    
    def _ensure_alarm_log(self) -> None:
        """Ensure alarm log file exists"""
        daily_folder = FileUtils.create_daily_folder(self.base_path)
        self.alarm_log_path = daily_folder / "Alarm_Log.csv"
        
        # Create file with header if not exists
        if not self.alarm_log_path.exists():
            with open(self.alarm_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp', 'Type', 'Value', 'Threshold', 'Message'
                ])
    
    def set_thresholds(self, temp_high: float, humi_high: float) -> None:
        """
        Set alarm thresholds
        
        Args:
            temp_high: Temperature high threshold (°C)
            humi_high: Humidity high threshold (%)
        """
        self.temp_high_threshold = temp_high
        self.humi_high_threshold = humi_high
    
    def set_latch_enabled(self, enabled: bool) -> None:
        """
        Enable or disable alarm latch
        
        Args:
            enabled: True to enable latch
        """
        self.latch_enabled = enabled
        
        # Clear latches if disabled
        if not enabled:
            self.temp_alarm_latched = False
            self.humi_alarm_latched = False
    
    def check_temperature(self, temperature: float) -> None:
        """
        Check temperature against threshold
        
        Args:
            temperature: Current temperature value
        """
        if temperature > self.temp_high_threshold:
            # Temperature exceeds threshold
            if not self.latch_enabled or not self.temp_alarm_latched:
                # Trigger alarm
                message = f"Temperature {temperature:.1f}°C exceeds threshold {self.temp_high_threshold:.1f}°C"
                self._log_alarm(AlarmType.TEMPERATURE_HIGH, temperature, 
                               self.temp_high_threshold, message)
                self.alarm_triggered.emit(
                    AlarmType.TEMPERATURE_HIGH, 
                    temperature, 
                    self.temp_high_threshold, 
                    message
                )
                
                # Set latch
                if self.latch_enabled:
                    self.temp_alarm_latched = True
        else:
            # Temperature normal, clear latch
            if self.temp_alarm_latched:
                self.temp_alarm_latched = False
                self.alarm_cleared.emit(AlarmType.TEMPERATURE_HIGH)
    
    def check_humidity(self, humidity: float) -> None:
        """
        Check humidity against threshold
        
        Args:
            humidity: Current humidity value
        """
        if humidity > self.humi_high_threshold:
            # Humidity exceeds threshold
            if not self.latch_enabled or not self.humi_alarm_latched:
                # Trigger alarm
                message = f"Humidity {humidity:.1f}% exceeds threshold {self.humi_high_threshold:.1f}%"
                self._log_alarm(AlarmType.HUMIDITY_HIGH, humidity, 
                               self.humi_high_threshold, message)
                self.alarm_triggered.emit(
                    AlarmType.HUMIDITY_HIGH, 
                    humidity, 
                    self.humi_high_threshold, 
                    message
                )
                
                # Set latch
                if self.latch_enabled:
                    self.humi_alarm_latched = True
        else:
            # Humidity normal, clear latch
            if self.humi_alarm_latched:
                self.humi_alarm_latched = False
                self.alarm_cleared.emit(AlarmType.HUMIDITY_HIGH)
    
    def check_values(self, temperature: float, humidity: float) -> None:
        """
        Check both temperature and humidity
        
        Args:
            temperature: Current temperature
            humidity: Current humidity
        """
        self.check_temperature(temperature)
        self.check_humidity(humidity)
    
    def _log_alarm(self, alarm_type: str, value: float, threshold: float, message: str) -> None:
        """
        Log alarm event to CSV
        
        Args:
            alarm_type: Type of alarm
            value: Current value
            threshold: Threshold value
            message: Alarm message
        """
        try:
            # Ensure daily log file exists
            self._ensure_alarm_log()
            
            # Append alarm event
            with open(self.alarm_log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    alarm_type,
                    f"{value:.1f}",
                    f"{threshold:.1f}",
                    message
                ])
            
            print(f"[ALARM] {message}")
            
        except Exception as e:
            print(f"Error logging alarm: {e}")
    
    def reset_latches(self) -> None:
        """Reset all alarm latches"""
        self.temp_alarm_latched = False
        self.humi_alarm_latched = False
    
    def get_status(self) -> Dict[str, any]:
        """
        Get alarm manager status
        
        Returns:
            dict: Status information
        """
        return {
            'temp_threshold': self.temp_high_threshold,
            'humi_threshold': self.humi_high_threshold,
            'latch_enabled': self.latch_enabled,
            'temp_latched': self.temp_alarm_latched,
            'humi_latched': self.humi_alarm_latched,
            'alarm_log_path': str(self.alarm_log_path) if self.alarm_log_path else None
        }


if __name__ == "__main__":
    """Test alarm manager"""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    print("=== Alarm Manager Test ===\n")
    
    app = QApplication(sys.argv)
    
    alarm_mgr = AlarmManager(base_path="./test_alarms")
    
    # Connect signals
    def on_alarm(alarm_type, value, threshold, message):
        print(f"⚠ ALARM TRIGGERED!")
        print(f"   Type: {alarm_type}")
        print(f"   Value: {value:.1f}")
        print(f"   Threshold: {threshold:.1f}")
        print(f"   Message: {message}\n")
    
    def on_cleared(alarm_type):
        print(f"✓ Alarm cleared: {alarm_type}\n")
    
    alarm_mgr.alarm_triggered.connect(on_alarm)
    alarm_mgr.alarm_cleared.connect(on_cleared)
    
    # Test 1: Set thresholds
    print("1. Setting thresholds:")
    alarm_mgr.set_thresholds(temp_high=30.0, humi_high=70.0)
    print(f"   Temp threshold: {alarm_mgr.temp_high_threshold}°C")
    print(f"   Humi threshold: {alarm_mgr.humi_high_threshold}%\n")
    
    # Test 2: Normal values
    print("2. Checking normal values:")
    alarm_mgr.check_values(25.0, 60.0)
    print("   No alarms (values normal)\n")
    
    # Test 3: Trigger temperature alarm
    print("3. Triggering temperature alarm:")
    alarm_mgr.check_values(35.0, 60.0)
    
    # Test 4: Latch prevents repeated trigger
    print("4. Testing latch (should not trigger again):")
    alarm_mgr.check_values(36.0, 60.0)
    print("   Latch prevented repeated alarm\n")
    
    # Test 5: Clear alarm
    print("5. Clearing alarm:")
    alarm_mgr.check_values(25.0, 60.0)
    
    # Test 6: Trigger humidity alarm
    print("6. Triggering humidity alarm:")
    alarm_mgr.check_values(25.0, 75.0)
    
    # Test 7: Status
    print("7. Alarm manager status:")
    status = alarm_mgr.get_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Cleanup
    print("\n8. Cleanup test files...")
    import shutil
    if Path("./test_alarms").exists():
        shutil.rmtree("./test_alarms")
        print("   Test files removed")
    
    print("\n✓ Test completed!")
