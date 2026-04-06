#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Manager

Handles application configuration persistence using JSON format.
Provides default values and automatic config file creation.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """Configuration manager with JSON persistence"""
    
    DEFAULT_CONFIG = {
        "serial": {
            "port": "COM3",
            "baud_rate": 115200,
            "auto_connect": True,
            "keywords": ["CH340", "STM", "USB-SERIAL", "USB Serial"]
        },
        "logging": {
            "enabled": False,
            "base_path": "./data",
            "auto_create_daily_folder": True,
            "sync_interval_sec": 2
        },
        "alarm": {
            "temperature_high": 35.0,
            "humidity_high": 80.0,
            "sound_enabled": True,
            "latch_enabled": True
        },
        "chart": {
            "update_interval_sec": 5,
            "history_minutes": 5,
            "auto_snapshot_enabled": False,
            "auto_snapshot_interval_sec": 60
        },
        "ui": {
            "theme": "dark",
            "window_width": 1200,
            "window_height": 800,
            "window_x": -1,  # -1 means center on screen
            "window_y": -1
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to config file. If None, uses 'config.json' in app directory
        """
        if config_path is None:
            # Place config.json in the gui directory
            app_dir = Path(__file__).parent.parent
            config_path = app_dir / "config.json"
        
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from file, create with defaults if not exists"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                self.config = self._deep_merge(self.DEFAULT_CONFIG.copy(), loaded_config)
                print(f"Configuration loaded from: {self.config_path}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                self.config = self.DEFAULT_CONFIG.copy()
                self.save()
        else:
            # Create new config with defaults
            print(f"Config file not found. Creating default: {self.config_path}")
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
    
    def save(self) -> bool:
        """
        Save current configuration to file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            print(f"Configuration saved to: {self.config_path}")
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., 'serial.port')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any, auto_save: bool = True) -> None:
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., 'serial.port')
            value: Value to set
            auto_save: If True, automatically save to file
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config or not isinstance(config[key], dict):
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        if auto_save:
            self.save()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
        print("Configuration reset to defaults")
    
    @staticmethod
    def _deep_merge(base: Dict, overlay: Dict) -> Dict:
        """
        Deep merge two dictionaries (overlay takes precedence)
        
        Args:
            base: Base dictionary
            overlay: Overlay dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result


# Global configuration instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration instance (singleton pattern)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


if __name__ == "__main__":
    # Test configuration manager
    print("=== Configuration Manager Test ===\n")
    
    config = ConfigManager("test_config.json")
    
    print("\n1. Get serial port:")
    print(f"   Port: {config.get('serial.port')}")
    
    print("\n2. Set new value:")
    config.set('serial.port', 'COM5')
    print(f"   New port: {config.get('serial.port')}")
    
    print("\n3. Get nested value:")
    print(f"   Alarm temp threshold: {config.get('alarm.temperature_high')}")
    
    print("\n4. Get with default:")
    print(f"   Non-existent key: {config.get('foo.bar', 'default_value')}")
    
    print("\n5. Reset to defaults:")
    config.reset_to_defaults()
    print(f"   Port after reset: {config.get('serial.port')}")
    
    # Cleanup test file
    Path("test_config.json").unlink(missing_ok=True)
    print("\n✓ Test completed!")
