#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Window

Main application window with tabbed interface for STM32 DHT11 monitoring.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QStatusBar, QLabel
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from ui.widgets.connection_bar import ConnectionBar
from ui.tabs.dashboard_tab import DashboardTab
from ui.tabs.terminal_tab import TerminalTab
from ui.tabs.files_tab import FilesTab
from ui.tabs.settings_tab import SettingsTab
from ui.tabs.replay_tab import ReplayTab


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STM32 DHT11 Temperature & Humidity Monitor")
        self.setMinimumSize(QSize(1200, 800))
        
        # Initialize UI
        self._init_ui()
        
        # Load window settings (position, size)
        self._load_window_settings()
    
    def _init_ui(self) -> None:
        """Initialize user interface"""
        
        # Central widget with tab container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Connection bar
        self.connection_bar = ConnectionBar()
        layout.addWidget(self.connection_bar)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(False)
        layout.addWidget(self.tab_widget)
        
        # Create placeholder tabs
        self._create_tabs()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.connection_status = QLabel("Disconnected")
        self.status_bar.addPermanentWidget(self.connection_status)
    
    def _create_tabs(self) -> None:
        """Create tab widgets"""
        
        # Dashboard Tab
        self.dashboard_tab = DashboardTab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Terminal Tab
        self.terminal_tab = TerminalTab()
        self.tab_widget.addTab(self.terminal_tab, "Terminal")
        
        # Files Tab
        self.files_tab = FilesTab()
        self.tab_widget.addTab(self.files_tab, "Files")
        
        # Settings Tab (Stage 4)
        self.settings_tab = SettingsTab()
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Replay Tab (Stage 5)
        self.replay_tab = ReplayTab()
        self.tab_widget.addTab(self.replay_tab, "Replay")
    
    def _load_window_settings(self) -> None:
        """Load window position and size from config"""
        try:
            from utils.config import get_config
            config = get_config()
            
            width = config.get('ui.window_width', 1200)
            height = config.get('ui.window_height', 800)
            x = config.get('ui.window_x', -1)
            y = config.get('ui.window_y', -1)
            
            self.resize(width, height)
            
            if x != -1 and y != -1:
                self.move(x, y)
            else:
                # Center on screen
                self._center_on_screen()
                
        except Exception as e:
            print(f"Could not load window settings: {e}")
            self._center_on_screen()
    
    def _center_on_screen(self) -> None:
        """Center window on screen"""
        screen = self.screen().geometry()
        window_geometry = self.frameGeometry()
        center_point = screen.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
    
    def _save_window_settings(self) -> None:
        """Save window position and size to config"""
        try:
            from utils.config import get_config
            config = get_config()
            
            config.set('ui.window_width', self.width(), auto_save=False)
            config.set('ui.window_height', self.height(), auto_save=False)
            config.set('ui.window_x', self.x(), auto_save=False)
            config.set('ui.window_y', self.y(), auto_save=False)
            config.save()
            
        except Exception as e:
            print(f"Could not save window settings: {e}")
    
    def update_status(self, message: str) -> None:
        """
        Update status bar message
        
        Args:
            message: Status message to display
        """
        self.status_label.setText(message)
    
    def update_connection_status(self, connected: bool, port: str = "") -> None:
        """
        Update connection status indicator
        
        Args:
            connected: Connection state
            port: Port name (if connected)
        """
        if connected:
            self.connection_status.setText(f"✓ Connected: {port}")
            self.connection_status.setStyleSheet("color: green;")
        else:
            self.connection_status.setText("✗ Disconnected")
            self.connection_status.setStyleSheet("color: red;")
    
    def closeEvent(self, event) -> None:
        """Handle window close event"""
        # Save window settings
        self._save_window_settings()
        
        # TODO: Add cleanup tasks
        # - Disconnect serial port
        # - Stop logging
        # - Save any unsaved data
        
        event.accept()


if __name__ == "__main__":
    """Test main window"""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Test status updates
    window.update_status("Application started")
    window.update_connection_status(True, "COM3")
    
    sys.exit(app.exec())
