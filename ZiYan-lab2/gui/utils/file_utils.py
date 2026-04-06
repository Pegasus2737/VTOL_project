#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Utilities

Handles file and directory management for data logging.
Features:
- Daily folder creation (YYYY-MM-DD)
- File naming with timestamps
- Path management
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class FileUtils:
    """File and directory utilities for data logging"""
    
    @staticmethod
    def create_daily_folder(base_path: str, date: Optional[datetime] = None) -> Path:
        """
        Create daily folder in format YYYY-MM-DD
        
        Args:
            base_path: Base directory path
            date: Date for folder (uses today if None)
            
        Returns:
            Path: Path to daily folder
        """
        if date is None:
            date = datetime.now()
        
        # Format: YYYY-MM-DD
        folder_name = date.strftime("%Y-%m-%d")
        folder_path = Path(base_path) / folder_name
        
        # Create folder if not exists
        folder_path.mkdir(parents=True, exist_ok=True)
        
        return folder_path
    
    @staticmethod
    def generate_filename(prefix: str, extension: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate filename with timestamp
        
        Args:
            prefix: Filename prefix (e.g., 'sensor_data')
            extension: File extension (e.g., 'csv', 'xlsx')
            timestamp: Timestamp for filename (uses now if None)
            
        Returns:
            str: Generated filename
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Format: prefix_HHMMSS.extension
        time_str = timestamp.strftime("%H%M%S")
        filename = f"{prefix}_{time_str}.{extension}"
        
        return filename
    
    @staticmethod
    def get_session_filepath(base_path: str, prefix: str, extension: str,
                            create_daily: bool = True) -> Path:
        """
        Get full filepath for a session file
        
        Args:
            base_path: Base directory path
            prefix: Filename prefix
            extension: File extension
            create_daily: If True, creates daily folder
            
        Returns:
            Path: Full file path
        """
        now = datetime.now()
        
        if create_daily:
            folder = FileUtils.create_daily_folder(base_path, now)
        else:
            folder = Path(base_path)
            folder.mkdir(parents=True, exist_ok=True)
        
        filename = FileUtils.generate_filename(prefix, extension, now)
        
        return folder / filename
    
    @staticmethod
    def ensure_directory(path: str) -> Path:
        """
        Ensure directory exists, create if not
        
        Args:
            path: Directory path
            
        Returns:
            Path: Path object
        """
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def get_existing_files(directory: str, pattern: str = "*") -> list:
        """
        Get list of existing files in directory
        
        Args:
            directory: Directory path
            pattern: Glob pattern (e.g., "*.csv")
            
        Returns:
            list: List of file paths
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return []
        
        return sorted(dir_path.glob(pattern))
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """
        Get file size in bytes
        
        Args:
            filepath: File path
            
        Returns:
            int: File size in bytes (0 if not exists)
        """
        path = Path(filepath)
        if path.exists():
            return path.stat().st_size
        return 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size to human-readable string
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """
        Convert string to safe filename
        
        Args:
            filename: Original filename
            
        Returns:
            str: Safe filename with invalid characters removed
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe = filename
        
        for char in invalid_chars:
            safe = safe.replace(char, '_')
        
        return safe
    
    @staticmethod
    def get_temp_directory() -> Path:
        """
        Get temporary directory for the application
        
        Returns:
            Path: Temp directory path
        """
        import tempfile
        temp_base = Path(tempfile.gettempdir()) / "stm32_monitor"
        temp_base.mkdir(parents=True, exist_ok=True)
        return temp_base


if __name__ == "__main__":
    """Test file utilities"""
    print("=== File Utilities Test ===\n")
    
    # Test 1: Create daily folder
    print("1. Creating daily folder...")
    test_base = "./test_data"
    daily_folder = FileUtils.create_daily_folder(test_base)
    print(f"   Created: {daily_folder}")
    
    # Test 2: Generate filename
    print("\n2. Generate filename:")
    filename = FileUtils.generate_filename("sensor_data", "csv")
    print(f"   Generated: {filename}")
    
    # Test 3: Get session filepath
    print("\n3. Get session filepath:")
    filepath = FileUtils.get_session_filepath(test_base, "test_sensor", "csv")
    print(f"   Full path: {filepath}")
    
    # Test 4: Create test file and get size
    print("\n4. File size test:")
    with open(filepath, 'w') as f:
        f.write("Test data\n" * 100)
    
    size_bytes = FileUtils.get_file_size(filepath)
    size_str = FileUtils.format_file_size(size_bytes)
    print(f"   File size: {size_str}")
    
    # Test 5: List files
    print("\n5. List existing files:")
    files = FileUtils.get_existing_files(test_base, "**/*.csv")
    print(f"   Found {len(files)} CSV files:")
    for file in files:
        print(f"     - {file}")
    
    # Test 6: Safe filename
    print("\n6. Safe filename:")
    unsafe = "data:2024/12*test?.csv"
    safe = FileUtils.safe_filename(unsafe)
    print(f"   Unsafe: {unsafe}")
    print(f"   Safe:   {safe}")
    
    # Test 7: Temp directory
    print("\n7. Temp directory:")
    temp_dir = FileUtils.get_temp_directory()
    print(f"   Temp: {temp_dir}")
    
    # Cleanup
    print("\n8. Cleanup test files...")
    import shutil
    if Path(test_base).exists():
        shutil.rmtree(test_base)
        print("   Test files removed")
    
    print("\n✓ Test completed!")
