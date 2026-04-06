#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connection Bar Widget

Provides connection controls including:
- COM port selection
- Baud rate selection
- Connect/Disconnect button
- Connection status indicator
- Auto-connect feature
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont


class ConnectionBar(QWidget):
    """Connection control bar widget"""
    
    # Signals
    connect_requested = pyqtSignal(str, int)  # port, baudrate
    disconnect_requested = pyqtSignal()
    refresh_ports_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Connection status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 14))
        self._update_indicator(False)
        layout.addWidget(self.status_indicator)
        
        # Port label
        port_label = QLabel("Port:")
        layout.addWidget(port_label)
        
        # Port combo box
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(120)
        self.port_combo.setEditable(False)
        layout.addWidget(self.port_combo)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setMaximumWidth(100)
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        layout.addWidget(self.refresh_btn)
        
        # Baud rate label
        baud_label = QLabel("Baud Rate:")
        layout.addWidget(baud_label)
        
        # Baud rate combo box
        self.baud_combo = QComboBox()
        self.baud_combo.setMinimumWidth(100)
        self.baud_combo.addItems([
            "9600", "19200", "38400", "57600", 
            "115200", "230400", "460800", "921600"
        ])
        self.baud_combo.setCurrentText("115200")  # Default
        layout.addWidget(self.baud_combo)
        
        # Auto-connect checkbox
        # self.auto_connect_check = QCheckBox("Auto-connect")
        # layout.addWidget(self.auto_connect_check)
        
        # Spacer
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Connect/Disconnect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumWidth(120)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_btn)
    
    def _on_connect_clicked(self) -> None:
        """Handle connect/disconnect button click"""
        if self.is_connected:
            # Disconnect
            self.disconnect_requested.emit()
        else:
            # Connect
            port = self.port_combo.currentText()
            if not port:
                return
            
            try:
                baudrate = int(self.baud_combo.currentText())
            except ValueError:
                baudrate = 115200
            
            self.connect_requested.emit(port, baudrate)
    
    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click"""
        self.refresh_ports_requested.emit()
    
    def set_ports(self, ports: list) -> None:
        """
        Update available ports in combo box
        
        Args:
            ports: List of port names
        """
        current_port = self.port_combo.currentText()
        
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        
        # Restore previous selection if still available
        if current_port in ports:
            self.port_combo.setCurrentText(current_port)
    
    def get_selected_port(self) -> str:
        """Get currently selected port"""
        return self.port_combo.currentText()
    
    def set_selected_port(self, port: str) -> None:
        """
        Set selected port
        
        Args:
            port: Port name to select
        """
        index = self.port_combo.findText(port)
        if index >= 0:
            self.port_combo.setCurrentIndex(index)
    
    def get_baudrate(self) -> int:
        """Get currently selected baud rate"""
        try:
            return int(self.baud_combo.currentText())
        except ValueError:
            return 115200
    
    def set_connected(self, connected: bool, port: str = "") -> None:
        """
        Update connection state
        
        Args:
            connected: Connection state
            port: Port name (if connected)
        """
        self.is_connected = connected
        
        if connected:
            self.connect_btn.setText(f"Disconnect")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            
            # Disable controls during connection
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            self.refresh_btn.setEnabled(False)
        else:
            self.connect_btn.setText("Connect")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            
            # Re-enable controls
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.refresh_btn.setEnabled(True)
        
        self._update_indicator(connected)
    
    def _update_indicator(self, connected: bool) -> None:
        """
        Update status indicator color
        
        Args:
            connected: Connection state
        """
        if connected:
            self.status_indicator.setStyleSheet("color: #4CAF50;")  # Green
        else:
            self.status_indicator.setStyleSheet("color: #f44336;")  # Red


if __name__ == "__main__":
    """Test connection bar"""
    from PyQt6.QtWidgets import QApplication, QVBoxLayout
    import sys
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = QWidget()
    window.setWindowTitle("Connection Bar Test")
    layout = QVBoxLayout(window)
    
    # Create connection bar
    conn_bar = ConnectionBar()
    layout.addWidget(conn_bar)
    
    # Test: Add some ports
    conn_bar.set_ports(["COM1", "COM3", "COM5"])
    
    # Connect signals
    def on_connect(port, baud):
        print(f"Connect requested: {port} @ {baud}")
        conn_bar.set_connected(True, port)
    
    def on_disconnect():
        print("Disconnect requested")
        conn_bar.set_connected(False)
    
    def on_refresh():
        print("Refresh requested")
        conn_bar.set_ports(["COM1", "COM3", "COM5", "COM7"])
    
    conn_bar.connect_requested.connect(on_connect)
    conn_bar.disconnect_requested.connect(on_disconnect)
    conn_bar.refresh_ports_requested.connect(on_refresh)
    
    window.show()
    sys.exit(app.exec())
