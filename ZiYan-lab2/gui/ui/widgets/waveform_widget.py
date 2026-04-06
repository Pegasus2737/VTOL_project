#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Waveform Widget

Real-time dual-axis waveform chart using pyqtgraph.
Displays temperature and humidity curves simultaneously.
"""

import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
from collections import deque
from datetime import datetime, timedelta
import numpy as np


class WaveformWidget(QWidget):
    """Real-time waveform chart widget"""
    
    def __init__(self, history_minutes: int = 5, parent=None):
        super().__init__(parent)
        self.history_minutes = history_minutes
        
        # Data buffers
        self.time_data = deque(maxlen=500)  # Store datetime objects
        self.temp_data = deque(maxlen=500)
        self.humi_data = deque(maxlen=500)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Set pyqtgraph background
        pg.setConfigOption('background', '#2b2b2b')
        pg.setConfigOption('foreground', 'd')
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setTitle("Temperature & Humidity Waveform", color='w', size='12pt')
        
        # Configure axes
        self.plot_widget.setLabel('left', 'Temperature (°C)', color='#ff6b6b')
        self.plot_widget.setLabel('bottom', 'Time', color='w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Add legend
        self.plot_widget.addLegend(offset=(10, 10))
        
        # Create temperature plot (left Y-axis)
        self.temp_curve = self.plot_widget.plot(
            pen=pg.mkPen(color='#ff6b6b', width=2),
            name='Temperature (°C)'
        )
        
        # Create second Y-axis for humidity
        self.humidity_axis = pg.ViewBox()
        self.plot_widget.scene().addItem(self.humidity_axis)
        self.plot_widget.getAxis('right').linkToView(self.humidity_axis)
        self.humidity_axis.setXLink(self.plot_widget)
        
        # Configure right axis
        self.plot_widget.setLabel('right', 'Humidity (%)', color='#4ecdc4')
        self.plot_widget.showAxis('right')
        
        # Create humidity plot (right Y-axis)
        self.humi_curve = pg.PlotDataItem(
            pen=pg.mkPen(color='#4ecdc4', width=2),
            name='Humidity (%)'
        )
        self.humidity_axis.addItem(self.humi_curve)
        
        # Update views when plot is resized
        self.plot_widget.getViewBox().sigResized.connect(self._update_views)
        
        # Set initial ranges
        self.plot_widget.setYRange(15, 35)  # Temperature range
        self.humidity_axis.setYRange(30, 80)  # Humidity range
        
        layout.addWidget(self.plot_widget)
    
    def _update_views(self) -> None:
        """Update linked views when main view changes"""
        self.humidity_axis.setGeometry(self.plot_widget.getViewBox().sceneBoundingRect())
        self.humidity_axis.linkedViewChanged(self.plot_widget.getViewBox(), self.humidity_axis.XAxis)
    
    def add_data_point(self, temperature: float, humidity: float, timestamp: datetime = None) -> None:
        """
        Add new data point to the chart
        
        Args:
            temperature: Temperature value in Celsius
            humidity: Humidity value in percentage
            timestamp: Timestamp (uses now() if None)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        self.time_data.append(timestamp)
        self.temp_data.append(temperature)
        self.humi_data.append(humidity)
        
        # Remove old data outside history window
        self._trim_old_data()
    
    def _trim_old_data(self) -> None:
        """Remove data points older than history window"""
        if not self.time_data:
            return

        # Use latest sample time as reference so replay data (historical timestamps)
        # is not immediately trimmed by current wall-clock time.
        reference_time = self.time_data[-1]
        cutoff_time = reference_time - timedelta(minutes=self.history_minutes)
        
        while self.time_data and self.time_data[0] < cutoff_time:
            self.time_data.popleft()
            self.temp_data.popleft()
            self.humi_data.popleft()
    
    def update_chart(self) -> None:
        """Update chart display (call this periodically, e.g., every 5 seconds)"""
        if not self.time_data:
            return
        
        # Convert timestamps to seconds from first point
        first_time = self.time_data[0]
        time_seconds = [(t - first_time).total_seconds() for t in self.time_data]
        
        # Convert to numpy arrays
        x_data = np.array(time_seconds)
        temp_array = np.array(self.temp_data)
        humi_array = np.array(self.humi_data)
        
        # Update curves
        self.temp_curve.setData(x_data, temp_array)
        self.humi_curve.setData(x_data, humi_array)
        
        # Auto-range Y axes
        if len(temp_array) > 0:
            temp_min, temp_max = temp_array.min(), temp_array.max()
            temp_margin = (temp_max - temp_min) * 0.1 or 5  # 10% margin or 5 degrees
            self.plot_widget.setYRange(temp_min - temp_margin, temp_max + temp_margin)
        
        if len(humi_array) > 0:
            humi_min, humi_max = humi_array.min(), humi_array.max()
            humi_margin = (humi_max - humi_min) * 0.1 or 10  # 10% margin or 10%
            self.humidity_axis.setYRange(humi_min - humi_margin, humi_max + humi_margin)
        
        # Update X axis labels (show time format)
        self._update_time_axis()
    
    def _update_time_axis(self) -> None:
        """Update X axis to show time labels"""
        if not self.time_data:
            return
        
        # Create custom tick labels showing actual time
        first_time = self.time_data[0]
        last_time = self.time_data[-1]
        
        duration = (last_time - first_time).total_seconds()
        
        # Format axis label based on duration
        if duration < 120:  # Less than 2 minutes
            axis_label = 'Time (seconds)'
        else:
            axis_label = 'Time (minutes)'
            
        self.plot_widget.setLabel('bottom', axis_label, color='w')
    
    def clear(self) -> None:
        """Clear all data"""
        self.time_data.clear()
        self.temp_data.clear()
        self.humi_data.clear()
        self.temp_curve.setData([], [])
        self.humi_curve.setData([], [])
    
    def set_history_minutes(self, minutes: int) -> None:
        """
        Set history window size
        
        Args:
            minutes: Number of minutes to keep
        """
        self.history_minutes = minutes
        self._trim_old_data()
    
    def get_data_count(self) -> int:
        """Get number of data points"""
        return len(self.time_data)


if __name__ == "__main__":
    """Test waveform widget"""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    import sys
    import math
    
    app = QApplication(sys.argv)
    
    waveform = WaveformWidget(history_minutes=2)
    waveform.setWindowTitle("Waveform Widget Test")
    waveform.resize(1000, 600)
    waveform.show()
    
    # Simulate data
    counter = [0]
    start_time = datetime.now()
    
    def add_simulated_data():
        counter[0] += 1
        t = counter[0] * 0.1  # Time in seconds
        
        # Generate sine wave data
        temp = 25.0 + 5.0 * math.sin(t * 0.5)
        humi = 60.0 + 10.0 * math.cos(t * 0.3)
        
        timestamp = start_time + timedelta(seconds=counter[0] * 0.1)
        waveform.add_data_point(temp, humi, timestamp)
        
        # Update chart every 10 points (simulate 5-second update)
        if counter[0] % 10 == 0:
            waveform.update_chart()
    
    # Add data every 100ms
    timer = QTimer()
    timer.timeout.connect(add_simulated_data)
    timer.start(100)
    
    print("Waveform test running...")
    print("Close window to exit")
    
    sys.exit(app.exec())
