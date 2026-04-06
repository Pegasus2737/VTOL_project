#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Controller

Controls data logging operations independently from monitoring.
Provides separate Monitor/Logging control.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from core.logger import DataLogger
from core.data_parser import SensorData
from typing import Optional


class LoggingController(QObject):
    """Controller for data logging operations"""
    
    # Signals
    logging_started = pyqtSignal(str, str)  # csv_path, excel_path
    logging_stopped = pyqtSignal(int)  # record_count
    logging_error = pyqtSignal(str)  # error_message
    
    def __init__(self, base_path: str = "./data"):
        """
        Initialize logging controller
        
        Args:
            base_path: Base directory for data files
        """
        super().__init__()
        self.logger: Optional[DataLogger] = None
        self.base_path = base_path
        self.is_logging = False
    
    def start_logging(self) -> bool:
        """
        Start data logging
        
        Returns:
            bool: True if started successfully
        """
        if self.is_logging:
            self.logging_error.emit("Logging already active")
            return False
        
        try:
            # Create new logger
            self.logger = DataLogger(base_path=self.base_path)
            
            if self.logger.start_logging():
                self.is_logging = True
                
                # Get paths and emit signal
                info = self.logger.get_session_info()
                self.logging_started.emit(
                    info['csv_path'],
                    info['excel_path']
                )
                
                return True
            else:
                self.logging_error.emit("Failed to start logging")
                return False
                
        except Exception as e:
            self.logging_error.emit(f"Logging error: {str(e)}")
            return False
    
    def stop_logging(self) -> None:
        """Stop data logging"""
        if not self.is_logging or not self.logger:
            return
        
        try:
            # Get record count before stopping
            info = self.logger.get_session_info()
            record_count = info['record_count']
            
            # Stop logger
            self.logger.stop_logging()
            self.is_logging = False
            
            # Emit signal
            self.logging_stopped.emit(record_count)
            
            # Clear logger reference
            self.logger = None
            
        except Exception as e:
            self.logging_error.emit(f"Error stopping logging: {str(e)}")
    
    def log_data(self, data: SensorData) -> bool:
        """
        Log sensor data (if logging is active)
        
        Args:
            data: SensorData object
            
        Returns:
            bool: True if logged successfully
        """
        if not self.is_logging or not self.logger:
            return False
        
        try:
            return self.logger.write_data(data)
        except Exception as e:
            self.logging_error.emit(f"Error writing data: {str(e)}")
            return False
    
    def get_session_info(self) -> Optional[dict]:
        """
        Get current logging session info
        
        Returns:
            dict or None: Session info if logging active
        """
        if self.logger:
            return self.logger.get_session_info()
        return None
    
    def set_base_path(self, path: str) -> None:
        """
        Set base path for data files
        
        Args:
            path: Base directory path
        """
        if self.is_logging:
            self.logging_error.emit("Cannot change path while logging")
            return
        
        self.base_path = path


if __name__ == "__main__":
    """Test logging controller"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    import sys
    from datetime import datetime
    
    print("=== Logging Controller Test ===\n")
    
    app = QApplication(sys.argv)
    
    controller = LoggingController(base_path="./test_log_ctrl")
    
    # Connect signals
    def on_started(csv_path, excel_path):
        print(f"✓ Logging started:")
        print(f"  CSV: {csv_path}")
        print(f"  Excel: {excel_path}")
    
    def on_stopped(count):
        print(f"✓ Logging stopped: {count} records")
        app.quit()
    
    def on_error(msg):
        print(f"✗ Error: {msg}")
    
    controller.logging_started.connect(on_started)
    controller.logging_stopped.connect(on_stopped)
    controller.logging_error.connect(on_error)
    
    # Test sequence
    print("1. Starting logging...")
    controller.start_logging()
    
    # Write some test data
    print("\n2. Writing test data...")
    counter = [0]
    
    def write_data():
        from core.data_parser import SensorData
        
        counter[0] += 1
        data = SensorData(
            timestamp=datetime.now(),
            temperature=25.0 + counter[0] * 0.1,
            humidity=60.0 + counter[0] * 0.2,
            oled_state=True,
            raw_line=f"TEST,{counter[0]}"
        )
        controller.log_data(data)
        
        if counter[0] >= 10:
            print(f"   Wrote {counter[0]} records")
            print("\n3. Stopping logging...")
            controller.stop_logging()
    
    timer = QTimer()
    timer.timeout.connect(write_data)
    timer.start(100)
    
    sys.exit(app.exec())
