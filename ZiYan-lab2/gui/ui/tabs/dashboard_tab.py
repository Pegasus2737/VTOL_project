#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Tab

Main monitoring dashboard with real-time data display.
Integrates:
- Current temperature/humidity values
- Statistics panel
- Waveform chart
- Monitor/Logging controls
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ui.widgets.waveform_widget import WaveformWidget
from ui.widgets.stats_panel import StatsPanel


class DashboardTab(QWidget):
    """Dashboard tab widget"""
    
    # Signals
    monitor_toggled = pyqtSignal(bool)  # Monitor on/off
    logging_toggled = pyqtSignal(bool)  # Logging on/off
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_monitoring = False
        self.is_logging = False
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Top section: Current values and stats
        top_layout = QHBoxLayout()
        
        # Current values display
        current_values_widget = self._create_current_values_widget()
        top_layout.addWidget(current_values_widget, stretch=2)
        
        # Statistics panel
        self.stats_panel = StatsPanel()
        top_layout.addWidget(self.stats_panel, stretch=1)
        
        layout.addLayout(top_layout, stretch=1)
        
        # Waveform chart
        self.waveform = WaveformWidget(history_minutes=5)
        layout.addWidget(self.waveform, stretch=3)
        
        # Control buttons
        control_layout = self._create_control_layout()
        layout.addLayout(control_layout)
    
    def _create_current_values_widget(self) -> QWidget:
        """
        Create current values display widget
        
        Returns:
            QWidget: Current values widget
        """
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(15)
        
        # Title font
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        
        # Value font
        value_font = QFont()
        value_font.setPointSize(32)
        value_font.setBold(True)
        
        # Unit font
        unit_font = QFont()
        unit_font.setPointSize(14)
        
        # Temperature display
        temp_group = QGroupBox("Temperature")
        temp_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ff6b6b;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #ff6b6b;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        temp_layout = QVBoxLayout(temp_group)
        
        self.temp_value_label = QLabel("--.-")
        self.temp_value_label.setFont(value_font)
        self.temp_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_value_label.setStyleSheet("color: #ff6b6b;")
        temp_layout.addWidget(self.temp_value_label)
        
        temp_unit = QLabel("°C")
        temp_unit.setFont(unit_font)
        temp_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temp_layout.addWidget(temp_unit)
        
        layout.addWidget(temp_group, 0, 0)
        
        # Humidity display
        humi_group = QGroupBox("Humidity")
        humi_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4ecdc4;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #4ecdc4;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        humi_layout = QVBoxLayout(humi_group)
        
        self.humi_value_label = QLabel("--.-")
        self.humi_value_label.setFont(value_font)
        self.humi_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.humi_value_label.setStyleSheet("color: #4ecdc4;")
        humi_layout.addWidget(self.humi_value_label)
        
        humi_unit = QLabel("%")
        humi_unit.setFont(unit_font)
        humi_unit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        humi_layout.addWidget(humi_unit)
        
        layout.addWidget(humi_group, 0, 1)
        
        # OLED status
        oled_label = QLabel("OLED Status:")
        layout.addWidget(oled_label, 1, 0)
        
        self.oled_status_label = QLabel("--")
        self.oled_status_label.setFont(title_font)
        layout.addWidget(self.oled_status_label, 1, 1)
        
        return widget
    
    def _create_control_layout(self) -> QHBoxLayout:
        """
        Create control buttons layout
        
        Returns:
            QHBoxLayout: Control layout
        """
        layout = QHBoxLayout()
        
        # Monitor button
        self.monitor_btn = QPushButton("● Monitor: OFF")
        self.monitor_btn.setMinimumHeight(40)
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        self.monitor_btn.clicked.connect(self._on_monitor_clicked)
        layout.addWidget(self.monitor_btn)
        
        # Logging button
        self.logging_btn = QPushButton("● Logging: OFF")
        self.logging_btn.setMinimumHeight(40)
        self.logging_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        self.logging_btn.clicked.connect(self._on_logging_clicked)
        layout.addWidget(self.logging_btn)
        
        return layout
    
    def _on_monitor_clicked(self) -> None:
        """Handle monitor button click"""
        self.is_monitoring = not self.is_monitoring
        
        if self.is_monitoring:
            self.monitor_btn.setText("● Monitor: ON")
            self.monitor_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
            """)
        else:
            self.monitor_btn.setText("● Monitor: OFF")
            self.monitor_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7f8c8d;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #95a5a6;
                }
            """)
        
        self.monitor_toggled.emit(self.is_monitoring)
    
    def _on_logging_clicked(self) -> None:
        """Handle logging button click"""
        self.is_logging = not self.is_logging
        
        if self.is_logging:
            self.logging_btn.setText("● Logging: ON")
            self.logging_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f39c12;
                }
            """)
        else:
            self.logging_btn.setText("● Logging: OFF")
            self.logging_btn.setStyleSheet("""
                QPushButton {
                    background-color: #7f8c8d;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #95a5a6;
                }
            """)
        
        self.logging_toggled.emit(self.is_logging)
    
    def update_current_values(self, temperature: float, humidity: float, oled_state: bool) -> None:
        """
        Update current value displays
        
        Args:
            temperature: Current temperature
            humidity: Current humidity
            oled_state: OLED on/off state
        """
        self.temp_value_label.setText(f"{temperature:.1f}")
        self.humi_value_label.setText(f"{humidity:.1f}")
        
        if oled_state:
            self.oled_status_label.setText("ON")
            self.oled_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.oled_status_label.setText("OFF")
            self.oled_status_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
    
    def update_statistics(self, stats: dict) -> None:
        """
        Update statistics panel
        
        Args:
            stats: Statistics dictionary
        """
        self.stats_panel.update_all(stats)
    
    def add_waveform_point(self, temperature: float, humidity: float, timestamp=None) -> None:
        """
        Add point to waveform
        
        Args:
            temperature: Temperature value
            humidity: Humidity value
            timestamp: Timestamp (optional)
        """
        self.waveform.add_data_point(temperature, humidity, timestamp)
    
    def update_waveform(self) -> None:
        """Update waveform chart display"""
        self.waveform.update_chart()
    
    def reset_display(self) -> None:
        """Reset all displays"""
        self.temp_value_label.setText("--.-")
        self.humi_value_label.setText("--.-")
        self.oled_status_label.setText("--")
        self.stats_panel.reset()
        self.waveform.clear()


if __name__ == "__main__":
    """Test dashboard tab"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    import sys
    from datetime import datetime
    import random
    import math
    
    app = QApplication(sys.argv)
    
    dashboard = DashboardTab()
    dashboard.setWindowTitle("Dashboard Tab Test")
    dashboard.resize(1200, 800)
    dashboard.show()
    
    # Connect signals
    dashboard.monitor_toggled.connect(lambda on: print(f"Monitor: {on}"))
    dashboard.logging_toggled.connect(lambda on: print(f"Logging: {on}"))
    
    # Simulate data
    counter = [0]
    
    def update_test_data():
        counter[0] += 1
        t = counter[0] * 0.2
        
        # Generate test data
        temp = 25.0 + 3.0 * math.sin(t * 0.3)
        humi = 60.0 + 8.0 * math.cos(t * 0.2)
        oled = (counter[0] // 10) % 2 == 0
        
        # Update current values
        dashboard.update_current_values(temp, humi, oled)
        
        # Add to waveform
        dashboard.add_waveform_point(temp, humi)
        
        # Update waveform every 5 "samples" (simulating 5-second interval)
        if counter[0] % 5 == 0:
            dashboard.update_waveform()
        
        # Update statistics
        stats = {
            'temp_min': 22.0,
            'temp_max': 28.0,
            'temp_avg': 25.0,
            'humi_min': 52.0,
            'humi_max': 68.0,
            'humi_avg': 60.0,
            'packet_count': counter[0],
            'sample_rate': 0.5
        }
        dashboard.update_statistics(stats)
    
    # Update every 500ms
    timer = QTimer()
    timer.timeout.connect(update_test_data)
    timer.start(500)
    
    print("Dashboard test running...")
    print("Close window to exit")
    
    sys.exit(app.exec())
