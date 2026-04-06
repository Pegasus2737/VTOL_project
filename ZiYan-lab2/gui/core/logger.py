#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Logger

Handles automatic data logging to CSV and Excel files.
Features:
- Dual format export (CSV + Excel)
- Buffered writing for performance
- Daily folder organization
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from core.data_parser import SensorData
from utils.file_utils import FileUtils


class DataLogger:
    """Data logger with CSV and Excel output"""
    
    def __init__(self, base_path: str = "./data"):
        """
        Initialize data logger
        
        Args:
            base_path: Base directory for data files
        """
        self.base_path = base_path
        self.is_logging = False
        
        # File paths
        self.csv_path: Optional[Path] = None
        self.excel_path: Optional[Path] = None
        
        # CSV file handle
        self.csv_file = None
        self.csv_writer = None
        
        # Excel buffer (write periodically)
        self.excel_buffer: List[dict] = []
        self.excel_write_interval = 10  # Write to Excel every 10 records
        
        # Session info
        self.session_start: Optional[datetime] = None
        self.record_count = 0
    
    def start_logging(self) -> bool:
        """
        Start logging session
        
        Returns:
            bool: True if started successfully
        """
        if self.is_logging:
            print("Logging already started")
            return False
        
        try:
            # Generate file paths
            self.csv_path = FileUtils.get_session_filepath(
                self.base_path, "sensor_data", "csv"
            )
            self.excel_path = FileUtils.get_session_filepath(
                self.base_path, "sensor_data", "xlsx"
            )
            
            # Open CSV file
            self.csv_file = open(self.csv_path, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write CSV header
            self.csv_writer.writerow([
                'Timestamp', 'Temperature', 'Humidity', 'OLED_State'
            ])
            self.csv_file.flush()
            
            # Initialize Excel buffer
            self.excel_buffer = []
            
            # Session info
            self.session_start = datetime.now()
            self.record_count = 0
            self.is_logging = True
            
            print(f"✓ Logging started")
            print(f"  CSV: {self.csv_path}")
            print(f"  Excel: {self.excel_path}")
            
            return True
            
        except Exception as e:
            print(f"Failed to start logging: {e}")
            self._cleanup()
            return False
    
    def stop_logging(self) -> None:
        """Stop logging session"""
        if not self.is_logging:
            return
        
        # Flush Excel buffer
        if self.excel_buffer:
            self._write_excel()
        
        # Close CSV file
        self._cleanup()
        
        self.is_logging = False
        
        print(f"✓ Logging stopped")
        print(f"  Total records: {self.record_count}")
    
    def write_data(self, data: SensorData) -> bool:
        """
        Write sensor data to log files
        
        Args:
            data: SensorData object
            
        Returns:
            bool: True if written successfully
        """
        if not self.is_logging:
            return False
        
        try:
            # Format timestamp
            timestamp_str = data.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            # Write to CSV immediately
            self.csv_writer.writerow([
                timestamp_str,
                f"{data.temperature:.1f}",
                f"{data.humidity:.1f}",
                1 if data.oled_state else 0
            ])
            self.csv_file.flush()  # Ensure data is written
            
            # Add to Excel buffer
            self.excel_buffer.append({
                'Timestamp': timestamp_str,
                'Temperature': data.temperature,
                'Humidity': data.humidity,
                'OLED_State': 1 if data.oled_state else 0
            })
            
            self.record_count += 1
            
            # Write to Excel periodically
            if len(self.excel_buffer) >= self.excel_write_interval:
                self._write_excel()
            
            return True
            
        except Exception as e:
            print(f"Error writing data: {e}")
            return False
    
    def _write_excel(self) -> None:
        """Write buffered data to Excel file"""
        if not self.excel_buffer:
            return
        
        try:
            # Check if file exists
            if self.excel_path.exists():
                # Append to existing file
                df_existing = pd.read_excel(self.excel_path)
                df_new = pd.DataFrame(self.excel_buffer)
                df = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                # Create new file
                df = pd.DataFrame(self.excel_buffer)
            
            # Write to Excel
            df.to_excel(self.excel_path, index=False, sheet_name='Data')
            
            # Clear buffer
            self.excel_buffer = []
            
        except Exception as e:
            print(f"Error writing Excel: {e}")
    
    def _cleanup(self) -> None:
        """Cleanup file handles"""
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
        
        self.csv_writer = None
    
    def get_session_info(self) -> dict:
        """
        Get current session information
        
        Returns:
            dict: Session info
        """
        return {
            'is_logging': self.is_logging,
            'session_start': self.session_start,
            'record_count': self.record_count,
            'csv_path': str(self.csv_path) if self.csv_path else None,
            'excel_path': str(self.excel_path) if self.excel_path else None,
            'csv_size': FileUtils.get_file_size(str(self.csv_path)) if self.csv_path else 0,
            'excel_size': FileUtils.get_file_size(str(self.excel_path)) if self.excel_path else 0
        }
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.is_logging:
            self.stop_logging()


if __name__ == "__main__":
    """Test data logger"""
    import time
    from core.data_parser import SensorData
    
    print("=== Data Logger Test ===\n")
    
    logger = DataLogger(base_path="./test_logs")
    
    # Test 1: Start logging
    print("1. Starting logger...")
    if logger.start_logging():
        print("   ✓ Logger started")
    
    # Test 2: Write some data
    print("\n2. Writing test data...")
    for i in range(15):
        data = SensorData(
            timestamp=datetime.now(),
            temperature=25.0 + i * 0.1,
            humidity=60.0 + i * 0.5,
            oled_state=(i % 2 == 0),
            raw_line=f"DATA,{25.0 + i * 0.1},{60.0 + i * 0.5},{i % 2}"
        )
        logger.write_data(data)
        time.sleep(0.1)
    
    print(f"   ✓ Wrote {logger.record_count} records")
    
    # Test 3: Get session info
    print("\n3. Session info:")
    info = logger.get_session_info()
    print(f"   Records: {info['record_count']}")
    print(f"   CSV: {info['csv_path']}")
    print(f"   CSV size: {FileUtils.format_file_size(info['csv_size'])}")
    print(f"   Excel: {info['excel_path']}")
    print(f"   Excel size: {FileUtils.format_file_size(info['excel_size'])}")
    
    # Test 4: Stop logging
    print("\n4. Stopping logger...")
    logger.stop_logging()
    print("   ✓ Logger stopped")
    
    # Verify files
    print("\n5. Verifying files...")
    if Path(info['csv_path']).exists():
        print(f"   ✓ CSV file exists")
    if Path(info['excel_path']).exists():
        print(f"   ✓ Excel file exists")
    
    # Cleanup
    print("\n6. Cleanup test files...")
    import shutil
    if Path("./test_logs").exists():
        shutil.rmtree("./test_logs")
        print("   Test files removed")
    
    print("\n✓ Test completed!")
