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
    QLabel, QGroupBox, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ui.widgets.waveform_widget import WaveformWidget


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
        
        # Top section: 3 columns x 2 rows cards
        top_grid = self._create_top_grid_widget()
        layout.addWidget(top_grid, stretch=2)
        
        # Waveform chart
        self.waveform = WaveformWidget(history_minutes=5)
        layout.addWidget(self.waveform, stretch=3)
        
        # Control buttons
        control_layout = self._create_control_layout()
        layout.addLayout(control_layout)
    
    def _create_top_grid_widget(self) -> QWidget:
        """Create top dashboard cards in a 3x2 grid."""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        for col in range(3):
            layout.setColumnStretch(col, 1)
        for row in range(2):
            layout.setRowStretch(row, 1)
        
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
        
        # Temperature current
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
        
        # Humidity current
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
        oled_group = QGroupBox("OLED Status")
        oled_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #95a5a6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #95a5a6;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        oled_layout = QVBoxLayout(oled_group)
        
        self.oled_status_label = QLabel("--")
        self.oled_status_label.setFont(value_font)
        self.oled_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.oled_status_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        oled_layout.addWidget(self.oled_status_label)

        oled_hint = QLabel("Device display state")
        oled_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        oled_hint.setFont(unit_font)
        oled_hint.setStyleSheet("color: #7f8c8d;")
        oled_layout.addWidget(oled_hint)

        layout.addWidget(oled_group, 0, 2)

        # Temperature statistics
        temp_stats_group = QGroupBox("Temperature (°C)")
        temp_stats_group.setStyleSheet("""
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
        temp_stats_layout = QGridLayout(temp_stats_group)
        temp_stats_layout.addWidget(QLabel("Min:"), 0, 0)
        self.temp_min_label = QLabel("--")
        self.temp_min_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        temp_stats_layout.addWidget(self.temp_min_label, 0, 1)
        temp_stats_layout.addWidget(QLabel("Max:"), 1, 0)
        self.temp_max_label = QLabel("--")
        self.temp_max_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        temp_stats_layout.addWidget(self.temp_max_label, 1, 1)
        temp_stats_layout.addWidget(QLabel("Avg:"), 2, 0)
        self.temp_avg_label = QLabel("--")
        self.temp_avg_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        temp_stats_layout.addWidget(self.temp_avg_label, 2, 1)
        layout.addWidget(temp_stats_group, 1, 0)

        # Humidity statistics
        humi_stats_group = QGroupBox("Humidity (%)")
        humi_stats_group.setStyleSheet("""
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
        humi_stats_layout = QGridLayout(humi_stats_group)
        humi_stats_layout.addWidget(QLabel("Min:"), 0, 0)
        self.humi_min_label = QLabel("--")
        self.humi_min_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        humi_stats_layout.addWidget(self.humi_min_label, 0, 1)
        humi_stats_layout.addWidget(QLabel("Max:"), 1, 0)
        self.humi_max_label = QLabel("--")
        self.humi_max_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        humi_stats_layout.addWidget(self.humi_max_label, 1, 1)
        humi_stats_layout.addWidget(QLabel("Avg:"), 2, 0)
        self.humi_avg_label = QLabel("--")
        self.humi_avg_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        humi_stats_layout.addWidget(self.humi_avg_label, 2, 1)
        layout.addWidget(humi_stats_group, 1, 1)

        # Data stream card
        stream_group = QGroupBox("Data Stream")
        stream_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #95a5a6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #95a5a6;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        stream_layout = QGridLayout(stream_group)
        stream_layout.addWidget(QLabel("Packets:"), 0, 0)
        self.packet_count_label = QLabel("0")
        self.packet_count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        stream_layout.addWidget(self.packet_count_label, 0, 1)
        stream_layout.addWidget(QLabel("Rate:"), 1, 0)
        self.sample_rate_label = QLabel("0.00 Hz")
        self.sample_rate_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        stream_layout.addWidget(self.sample_rate_label, 1, 1)
        layout.addWidget(stream_group, 1, 2)
        
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
        self.set_monitor_state(not self.is_monitoring, emit_signal=True)

    def set_monitor_state(self, enabled: bool, emit_signal: bool = False) -> None:
        """
        Set monitor state and update button appearance.

        Args:
            enabled: Monitor enabled/disabled state
            emit_signal: If True, emit monitor_toggled signal
        """
        self.is_monitoring = enabled

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

        if emit_signal:
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
        self.temp_min_label.setText(f"{stats.get('temp_min', 0.0):.1f}")
        self.temp_max_label.setText(f"{stats.get('temp_max', 0.0):.1f}")
        self.temp_avg_label.setText(f"{stats.get('temp_avg', 0.0):.1f}")

        self.humi_min_label.setText(f"{stats.get('humi_min', 0.0):.1f}")
        self.humi_max_label.setText(f"{stats.get('humi_max', 0.0):.1f}")
        self.humi_avg_label.setText(f"{stats.get('humi_avg', 0.0):.1f}")

        self.packet_count_label.setText(f"{stats.get('packet_count', 0)}")
        self.sample_rate_label.setText(f"{stats.get('sample_rate', 0.0):.2f} Hz")
    
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
        self.temp_min_label.setText("--")
        self.temp_max_label.setText("--")
        self.temp_avg_label.setText("--")
        self.humi_min_label.setText("--")
        self.humi_max_label.setText("--")
        self.humi_avg_label.setText("--")
        self.packet_count_label.setText("0")
        self.sample_rate_label.setText("0.00 Hz")
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
