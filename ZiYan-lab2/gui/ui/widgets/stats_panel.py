#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Statistics Panel Widget

Displays real-time statistics for temperature and humidity.
Shows Min/Max/Average values, packet count, and sample rate.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class StatsPanel(QWidget):
    """Statistics display panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Temperature stats group
        temp_group = self._create_stats_group(
            "Temperature (°C)",
            "#ff6b6b"
        )
        self.temp_min_label = temp_group['min']
        self.temp_max_label = temp_group['max']
        self.temp_avg_label = temp_group['avg']
        layout.addWidget(temp_group['widget'])
        
        # Humidity stats group
        humi_group = self._create_stats_group(
            "Humidity (%)",
            "#4ecdc4"
        )
        self.humi_min_label = humi_group['min']
        self.humi_max_label = humi_group['max']
        self.humi_avg_label = humi_group['avg']
        layout.addWidget(humi_group['widget'])
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # Packet info group
        packet_group = self._create_packet_info_group()
        layout.addWidget(packet_group)
        
        layout.addStretch()
    
    def _create_stats_group(self, title: str, color: str) -> dict:
        """
        Create a statistics group box
        
        Args:
            title: Group title
            color: Title color
            
        Returns:
            dict: {'widget', 'min', 'max', 'avg'}
        """
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {color};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                color: {color};
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(5)
        
        # Value font
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        
        # Min
        layout.addWidget(QLabel("Min:"), 0, 0)
        min_label = QLabel("--")
        min_label.setFont(value_font)
        min_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(min_label, 0, 1)
        
        # Max
        layout.addWidget(QLabel("Max:"), 1, 0)
        max_label = QLabel("--")
        max_label.setFont(value_font)
        max_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(max_label, 1, 1)
        
        # Average
        layout.addWidget(QLabel("Avg:"), 2, 0)
        avg_label = QLabel("--")
        avg_label.setFont(value_font)
        avg_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(avg_label, 2, 1)
        
        return {
            'widget': group,
            'min': min_label,
            'max': max_label,
            'avg': avg_label
        }
    
    def _create_packet_info_group(self) -> QGroupBox:
        """
        Create packet information group
        
        Returns:
            QGroupBox: Packet info widget
        """
        group = QGroupBox("Data Stream")
        group.setStyleSheet("""
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
        
        layout = QGridLayout(group)
        layout.setSpacing(5)
        
        # Value font
        value_font = QFont()
        value_font.setPointSize(14)
        value_font.setBold(True)
        
        # Packet count
        layout.addWidget(QLabel("Packets:"), 0, 0)
        self.packet_count_label = QLabel("0")
        self.packet_count_label.setFont(value_font)
        self.packet_count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.packet_count_label, 0, 1)
        
        # Sample rate
        layout.addWidget(QLabel("Rate:"), 1, 0)
        self.sample_rate_label = QLabel("0.00 Hz")
        self.sample_rate_label.setFont(value_font)
        self.sample_rate_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.sample_rate_label, 1, 1)
        
        return group
    
    def update_temperature_stats(self, min_val: float, max_val: float, avg_val: float) -> None:
        """
        Update temperature statistics
        
        Args:
            min_val: Minimum temperature
            max_val: Maximum temperature
            avg_val: Average temperature
        """
        self.temp_min_label.setText(f"{min_val:.1f}")
        self.temp_max_label.setText(f"{max_val:.1f}")
        self.temp_avg_label.setText(f"{avg_val:.1f}")
    
    def update_humidity_stats(self, min_val: float, max_val: float, avg_val: float) -> None:
        """
        Update humidity statistics
        
        Args:
            min_val: Minimum humidity
            max_val: Maximum humidity
            avg_val: Average humidity
        """
        self.humi_min_label.setText(f"{min_val:.1f}")
        self.humi_max_label.setText(f"{max_val:.1f}")
        self.humi_avg_label.setText(f"{avg_val:.1f}")
    
    def update_packet_info(self, packet_count: int, sample_rate: float) -> None:
        """
        Update packet information
        
        Args:
            packet_count: Total packet count
            sample_rate: Sample rate in Hz
        """
        self.packet_count_label.setText(f"{packet_count}")
        self.sample_rate_label.setText(f"{sample_rate:.2f} Hz")
    
    def update_all(self, stats: dict) -> None:
        """
        Update all statistics from a stats dictionary
        
        Args:
            stats: Dictionary with keys: temp_min, temp_max, temp_avg,
                   humi_min, humi_max, humi_avg, packet_count, sample_rate
        """
        self.update_temperature_stats(
            stats.get('temp_min', 0.0),
            stats.get('temp_max', 0.0),
            stats.get('temp_avg', 0.0)
        )
        
        self.update_humidity_stats(
            stats.get('humi_min', 0.0),
            stats.get('humi_max', 0.0),
            stats.get('humi_avg', 0.0)
        )
        
        self.update_packet_info(
            stats.get('packet_count', 0),
            stats.get('sample_rate', 0.0)
        )
    
    def reset(self) -> None:
        """Reset all displays to default"""
        self.temp_min_label.setText("--")
        self.temp_max_label.setText("--")
        self.temp_avg_label.setText("--")
        
        self.humi_min_label.setText("--")
        self.humi_max_label.setText("--")
        self.humi_avg_label.setText("--")
        
        self.packet_count_label.setText("0")
        self.sample_rate_label.setText("0.00 Hz")


if __name__ == "__main__":
    """Test stats panel"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    import sys
    import random
    
    app = QApplication(sys.argv)
    
    panel = StatsPanel()
    panel.setWindowTitle("Stats Panel Test")
    panel.resize(300, 400)
    panel.show()
    
    # Simulate updating stats
    counter = [0]
    
    def update_test_stats():
        counter[0] += 1
        
        # Simulate random stats
        temp_base = 25.0
        humi_base = 60.0
        
        stats = {
            'temp_min': temp_base - random.uniform(0, 3),
            'temp_max': temp_base + random.uniform(0, 3),
            'temp_avg': temp_base + random.uniform(-1, 1),
            'humi_min': humi_base - random.uniform(0, 5),
            'humi_max': humi_base + random.uniform(0, 5),
            'humi_avg': humi_base + random.uniform(-2, 2),
            'packet_count': counter[0] * 10,
            'sample_rate': 0.5 + random.uniform(-0.05, 0.05)
        }
        
        panel.update_all(stats)
    
    # Update every second
    timer = QTimer()
    timer.timeout.connect(update_test_stats)
    timer.start(1000)
    
    # Initial update
    update_test_stats()
    
    print("Stats panel test running...")
    print("Close window to exit")
    
    sys.exit(app.exec())
