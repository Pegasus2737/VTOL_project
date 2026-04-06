#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Tab

Application settings configuration:
- Serial port settings
- Data storage path
- Alarm thresholds
- Sound settings
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit, QPushButton, QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from utils.config import get_config


class SettingsTab(QWidget):
    """Settings configuration tab"""
    
    # Signals
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = get_config()
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Serial settings
        serial_group = self._create_serial_group()
        layout.addWidget(serial_group)
        
        # Storage settings
        storage_group = self._create_storage_group()
        layout.addWidget(storage_group)
        
        # Alarm settings
        alarm_group = self._create_alarm_group()
        layout.addWidget(alarm_group)
        
        # Chart settings
        chart_group = self._create_chart_group()
        layout.addWidget(chart_group)
        
        # Buttons
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
        
        layout.addStretch()
    
    def _create_serial_group(self) -> QGroupBox:
        """Create serial port settings group"""
        group = QGroupBox("Serial Port Settings")
        layout = QVBoxLayout(group)
        
        # Auto-connect
        self.auto_connect_check = QCheckBox("Auto-connect on startup")
        layout.addWidget(self.auto_connect_check)
        
        # Baud rate
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Default Baud Rate:"))
        
        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.addItems([
            "9600", "19200", "38400", "57600", 
            "115200", "230400", "460800", "921600"
        ])
        baud_layout.addWidget(self.baud_rate_combo)
        baud_layout.addStretch()
        
        layout.addLayout(baud_layout)
        
        return group
    
    def _create_storage_group(self) -> QGroupBox:
        """Create storage settings group"""
        group = QGroupBox("Data Storage")
        layout = QVBoxLayout(group)
        
        # Base path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Base Path:"))
        
        self.base_path_edit = QLineEdit()
        path_layout.addWidget(self.base_path_edit, stretch=1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_path)
        path_layout.addWidget(browse_btn)
        
        layout.addLayout(path_layout)
        
        # Auto-create daily folders
        self.daily_folder_check = QCheckBox("Auto-create daily folders (YYYY-MM-DD)")
        layout.addWidget(self.daily_folder_check)
        
        # Sync interval
        sync_layout = QHBoxLayout()
        sync_layout.addWidget(QLabel("Sync Interval:"))
        
        self.sync_interval_spin = QSpinBox()
        self.sync_interval_spin.setRange(1, 60)
        self.sync_interval_spin.setSuffix(" seconds")
        sync_layout.addWidget(self.sync_interval_spin)
        sync_layout.addStretch()
        
        layout.addLayout(sync_layout)
        
        return group
    
    def _create_alarm_group(self) -> QGroupBox:
        """Create alarm settings group"""
        group = QGroupBox("Alarm Thresholds")
        layout = QVBoxLayout(group)
        
        # Temperature high threshold
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("Temperature High:"))
        
        self.temp_high_spin = QDoubleSpinBox()
        self.temp_high_spin.setRange(-40, 125)
        self.temp_high_spin.setValue(35.0)
        self.temp_high_spin.setSuffix(" °C")
        self.temp_high_spin.setDecimals(1)
        temp_layout.addWidget(self.temp_high_spin)
        temp_layout.addStretch()
        
        layout.addLayout(temp_layout)
        
        # Humidity high threshold
        humi_layout = QHBoxLayout()
        humi_layout.addWidget(QLabel("Humidity High:"))
        
        self.humi_high_spin = QDoubleSpinBox()
        self.humi_high_spin.setRange(0, 100)
        self.humi_high_spin.setValue(80.0)
        self.humi_high_spin.setSuffix(" %")
        self.humi_high_spin.setDecimals(1)
        humi_layout.addWidget(self.humi_high_spin)
        humi_layout.addStretch()
        
        layout.addLayout(humi_layout)
        
        # Sound enabled
        self.sound_enabled_check = QCheckBox("Enable alarm sound")
        layout.addWidget(self.sound_enabled_check)
        
        # Latch enabled
        self.latch_enabled_check = QCheckBox("Enable alarm latch (prevent repeated alerts)")
        layout.addWidget(self.latch_enabled_check)
        
        return group
    
    def _create_chart_group(self) -> QGroupBox:
        """Create chart settings group"""
        group = QGroupBox("Chart Settings")
        layout = QVBoxLayout(group)
        
        # Update interval
        update_layout = QHBoxLayout()
        update_layout.addWidget(QLabel("Update Interval:"))
        
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setRange(1, 60)
        self.update_interval_spin.setValue(5)
        self.update_interval_spin.setSuffix(" seconds")
        update_layout.addWidget(self.update_interval_spin)
        update_layout.addStretch()
        
        layout.addLayout(update_layout)
        
        # History window
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("History Window:"))
        
        self.history_minutes_spin = QSpinBox()
        self.history_minutes_spin.setRange(1, 60)
        self.history_minutes_spin.setValue(5)
        self.history_minutes_spin.setSuffix(" minutes")
        history_layout.addWidget(self.history_minutes_spin)
        history_layout.addStretch()
        
        layout.addLayout(history_layout)
        
        return group
    
    def _create_button_layout(self) -> QHBoxLayout:
        """Create action buttons layout"""
        layout = QHBoxLayout()
        
        layout.addStretch()
        
        # Reset to defaults
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset_defaults)
        layout.addWidget(reset_btn)
        
        # Apply settings
        apply_btn = QPushButton("Apply Settings")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        apply_btn.clicked.connect(self._on_apply_settings)
        layout.addWidget(apply_btn)
        
        return layout
    
    def _load_settings(self) -> None:
        """Load settings from config"""
        # Serial
        self.auto_connect_check.setChecked(
            self.config.get('serial.auto_connect', True)
        )
        self.baud_rate_combo.setCurrentText(
            str(self.config.get('serial.baud_rate', 115200))
        )
        
        # Storage
        self.base_path_edit.setText(
            self.config.get('logging.base_path', './data')
        )
        self.daily_folder_check.setChecked(
            self.config.get('logging.auto_create_daily_folder', True)
        )
        self.sync_interval_spin.setValue(
            self.config.get('logging.sync_interval_sec', 2)
        )
        
        # Alarm
        self.temp_high_spin.setValue(
            self.config.get('alarm.temperature_high', 35.0)
        )
        self.humi_high_spin.setValue(
            self.config.get('alarm.humidity_high', 80.0)
        )
        self.sound_enabled_check.setChecked(
            self.config.get('alarm.sound_enabled', True)
        )
        self.latch_enabled_check.setChecked(
            self.config.get('alarm.latch_enabled', True)
        )
        
        # Chart
        self.update_interval_spin.setValue(
            self.config.get('chart.update_interval_sec', 5)
        )
        self.history_minutes_spin.setValue(
            self.config.get('chart.history_minutes', 5)
        )
    
    def _save_settings(self) -> None:
        """Save settings to config"""
        # Serial
        self.config.set('serial.auto_connect', 
                       self.auto_connect_check.isChecked(), auto_save=False)
        self.config.set('serial.baud_rate', 
                       int(self.baud_rate_combo.currentText()), auto_save=False)
        
        # Storage
        self.config.set('logging.base_path', 
                       self.base_path_edit.text(), auto_save=False)
        self.config.set('logging.auto_create_daily_folder', 
                       self.daily_folder_check.isChecked(), auto_save=False)
        self.config.set('logging.sync_interval_sec', 
                       self.sync_interval_spin.value(), auto_save=False)
        
        # Alarm
        self.config.set('alarm.temperature_high', 
                       self.temp_high_spin.value(), auto_save=False)
        self.config.set('alarm.humidity_high', 
                       self.humi_high_spin.value(), auto_save=False)
        self.config.set('alarm.sound_enabled', 
                       self.sound_enabled_check.isChecked(), auto_save=False)
        self.config.set('alarm.latch_enabled', 
                       self.latch_enabled_check.isChecked(), auto_save=False)
        
        # Chart
        self.config.set('chart.update_interval_sec', 
                       self.update_interval_spin.value(), auto_save=False)
        self.config.set('chart.history_minutes', 
                       self.history_minutes_spin.value(), auto_save=False)
        
        # Save all at once
        self.config.save()
    
    def _on_browse_path(self) -> None:
        """Browse for base path"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Data Storage Location",
            self.base_path_edit.text()
        )
        
        if path:
            self.base_path_edit.setText(path)
    
    def _on_apply_settings(self) -> None:
        """Apply settings"""
        self._save_settings()
        self.settings_changed.emit()
        
        # Show confirmation (could use QMessageBox)
        print("✓ Settings saved and applied")
    
    def _on_reset_defaults(self) -> None:
        """Reset to default settings"""
        from PyQt6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config.reset_to_defaults()
            self._load_settings()
            self.settings_changed.emit()
            print("✓ Settings reset to defaults")


if __name__ == "__main__":
    """Test settings tab"""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    settings_tab = SettingsTab()
    settings_tab.setWindowTitle("Settings Tab Test")
    settings_tab.resize(600, 700)
    settings_tab.show()
    
    # Connect signal
    settings_tab.settings_changed.connect(lambda: print("Settings changed!"))
    
    sys.exit(app.exec())
