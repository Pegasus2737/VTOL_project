#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STM32 Temperature & Humidity Monitoring System - Main Entry Point

This is the main application entry point for the DHT11 sensor monitoring GUI.
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

def main():
    """Main application entry point"""
    
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("STM32 DHT11 Monitor")
    app.setOrganizationName("VTOL Project")
    app.setApplicationVersion("1.0.0")
    
    # Create main window
    from ui.main_window import MainWindow
    window = MainWindow()
    
    # Create and setup controller
    from controllers.main_controller import MainController
    controller = MainController(window)
    controller.set_dashboard_tab(window.dashboard_tab)
    controller.set_terminal_tab(window.terminal_tab)
    controller.set_files_tab(window.files_tab)
    controller.set_settings_tab(window.settings_tab)
    controller.set_replay_tab(window.replay_tab)
    controller.initialize()
    
    # Show window
    window.show()
    
    print("=" * 60)
    print("STM32 DHT11 Monitoring System - STAGE 5 COMPLETE")
    print("=" * 60)
    print("Features Available:")
    print("  ✓ Connection management with auto-detect")
    print("  ✓ Dashboard with real-time values")
    print("  ✓ Temperature & Humidity waveform chart")
    print("  ✓ Statistics (Min/Max/Avg)")
    print("  ✓ Terminal for raw UART data")
    print("  ✓ Monitor/Logging controls")
    print("  ✓ CSV/Excel automatic logging")  
    print("  ✓ Export tools (Summary, Chart, PNG)")
    print("  ✓ Auto-snapshot feature")
    print("  ✓ Settings tab (Serial, Storage, Alarm, Chart)")
    print("  ✓ Alarm system with threshold checking")
    print("  ✓ Alarm latch mechanism")
    print("  ✓ Alarm sound notifications")
    print("  ✓ Alarm log CSV")
    print("  ✓ Replay tab with CSV playback")
    print("  ✓ Replay controls (play/pause/seek/speed)")
    print("=" * 60)
    print("\nConnect your STM32 device and click 'Refresh' -> 'Connect'")
    print("Toggle 'Logging: ON' to start recording data")
    print("Configure alarm thresholds in Settings tab")
    print("=" * 60)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
