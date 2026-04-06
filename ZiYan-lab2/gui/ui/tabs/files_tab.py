#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Files Tab

Manages file operations and exports:
- Current session file paths display
- Export tools (Summary CSV, Excel Chart)
- Auto-snapshot settings
- File browser
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QSpinBox,
    QCheckBox, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path


class FilesTab(QWidget):
    """Files management tab"""
    
    # Signals
    export_summary_requested = pyqtSignal()
    export_excel_chart_requested = pyqtSignal()
    export_waveform_png_requested = pyqtSignal()
    auto_snapshot_toggled = pyqtSignal(bool, int)  # enabled, interval_seconds
    base_path_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_csv_path = ""
        self.current_excel_path = ""
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Current session files group
        session_group = self._create_session_group()
        layout.addWidget(session_group)
        
        # Export tools group
        export_group = self._create_export_group()
        layout.addWidget(export_group)
        
        # Auto-snapshot settings group
        snapshot_group = self._create_snapshot_group()
        layout.addWidget(snapshot_group)
        
        # Base path settings
        path_group = self._create_path_group()
        layout.addWidget(path_group)
        
        layout.addStretch()
    
    def _create_session_group(self) -> QGroupBox:
        """Create current session files group"""
        group = QGroupBox("Current Session Files")
        layout = QVBoxLayout(group)
        
        # CSV path
        csv_layout = QHBoxLayout()
        csv_layout.addWidget(QLabel("CSV:"))
        self.csv_path_label = QLabel("Not logging")
        self.csv_path_label.setStyleSheet("color: #888; font-family: monospace;")
        csv_layout.addWidget(self.csv_path_label, stretch=1)
        
        self.open_csv_btn = QPushButton("Open")
        self.open_csv_btn.clicked.connect(self._on_open_csv)
        self.open_csv_btn.setEnabled(False)
        csv_layout.addWidget(self.open_csv_btn)
        
        layout.addLayout(csv_layout)
        
        # Excel path
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("Excel:"))
        self.excel_path_label = QLabel("Not logging")
        self.excel_path_label.setStyleSheet("color: #888; font-family: monospace;")
        excel_layout.addWidget(self.excel_path_label, stretch=1)
        
        self.open_excel_btn = QPushButton("Open")
        self.open_excel_btn.clicked.connect(self._on_open_excel)
        self.open_excel_btn.setEnabled(False)
        excel_layout.addWidget(self.open_excel_btn)
        
        layout.addLayout(excel_layout)
        
        return group
    
    def _create_export_group(self) -> QGroupBox:
        """Create export tools group"""
        group = QGroupBox("Export Tools")
        layout = QVBoxLayout(group)
        
        # Summary CSV export
        summary_btn = QPushButton("Export Summary CSV")
        summary_btn.setToolTip("Export statistical summary to CSV file")
        summary_btn.clicked.connect(self._on_export_summary)
        layout.addWidget(summary_btn)
        
        # Excel chart export
        excel_chart_btn = QPushButton("Export Excel with Chart")
        excel_chart_btn.setToolTip("Export data to Excel with embedded chart")
        excel_chart_btn.clicked.connect(self._on_export_excel_chart)
        layout.addWidget(excel_chart_btn)
        
        # Waveform PNG export
        waveform_png_btn = QPushButton("Export Waveform PNG")
        waveform_png_btn.setToolTip("Save current waveform chart as PNG image")
        waveform_png_btn.clicked.connect(self._on_export_waveform)
        layout.addWidget(waveform_png_btn)
        
        return group
    
    def _create_snapshot_group(self) -> QGroupBox:
        """Create auto-snapshot settings group"""
        group = QGroupBox("Auto Snapshot")
        layout = QVBoxLayout(group)
        
        # Enable checkbox
        self.auto_snapshot_check = QCheckBox("Enable automatic waveform snapshots")
        layout.addWidget(self.auto_snapshot_check)
        
        # Interval setting
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Interval:"))
        
        self.snapshot_interval_spin = QSpinBox()
        self.snapshot_interval_spin.setRange(10, 3600)
        self.snapshot_interval_spin.setValue(60)
        self.snapshot_interval_spin.setSuffix(" seconds")
        interval_layout.addWidget(self.snapshot_interval_spin)
        
        interval_layout.addStretch()
        layout.addLayout(interval_layout)
        
        # Apply button
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self._on_apply_snapshot_settings)
        layout.addWidget(apply_btn)
        
        return group
    
    def _create_path_group(self) -> QGroupBox:
        """Create base path settings group"""
        group = QGroupBox("Storage Location")
        layout = QVBoxLayout(group)
        
        path_layout = QHBoxLayout()
        
        self.base_path_edit = QLineEdit()
        self.base_path_edit.setText("./data")
        self.base_path_edit.setPlaceholderText("Base path for data files")
        path_layout.addWidget(self.base_path_edit, stretch=1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_path)
        path_layout.addWidget(browse_btn)
        
        set_path_btn = QPushButton("Set Path")
        set_path_btn.clicked.connect(self._on_set_path)
        path_layout.addWidget(set_path_btn)
        
        layout.addLayout(path_layout)
        
        help_label = QLabel("Data will be organized in daily folders (YYYY-MM-DD)")
        help_label.setStyleSheet("color: #888; font-size: 9pt;")
        layout.addWidget(help_label)
        
        return group
    
    def update_session_paths(self, csv_path: str, excel_path: str) -> None:
        """
        Update current session file paths
        
        Args:
            csv_path: CSV file path
            excel_path: Excel file path
        """
        self.current_csv_path = csv_path
        self.current_excel_path = excel_path
        
        self.csv_path_label.setText(csv_path)
        self.csv_path_label.setStyleSheet("color: #4CAF50; font-family: monospace;")
        self.open_csv_btn.setEnabled(True)
        
        self.excel_path_label.setText(excel_path)
        self.excel_path_label.setStyleSheet("color: #4CAF50; font-family: monospace;")
        self.open_excel_btn.setEnabled(True)
    
    def clear_session_paths(self) -> None:
        """Clear session file paths"""
        self.current_csv_path = ""
        self.current_excel_path = ""
        
        self.csv_path_label.setText("Not logging")
        self.csv_path_label.setStyleSheet("color: #888; font-family: monospace;")
        self.open_csv_btn.setEnabled(False)
        
        self.excel_path_label.setText("Not logging")
        self.excel_path_label.setStyleSheet("color: #888; font-family: monospace;")
        self.open_excel_btn.setEnabled(False)
    
    def _on_open_csv(self) -> None:
        """Open CSV file in system default application"""
        if self.current_csv_path and Path(self.current_csv_path).exists():
            import os
            os.startfile(self.current_csv_path)
    
    def _on_open_excel(self) -> None:
        """Open Excel file in system default application"""
        if self.current_excel_path and Path(self.current_excel_path).exists():
            import os
            os.startfile(self.current_excel_path)
    
    def _on_export_summary(self) -> None:
        """Handle export summary button"""
        self.export_summary_requested.emit()
    
    def _on_export_excel_chart(self) -> None:
        """Handle export Excel chart button"""
        self.export_excel_chart_requested.emit()
    
    def _on_export_waveform(self) -> None:
        """Handle export waveform PNG button"""
        self.export_waveform_png_requested.emit()
    
    def _on_apply_snapshot_settings(self) -> None:
        """Handle apply snapshot settings"""
        enabled = self.auto_snapshot_check.isChecked()
        interval = self.snapshot_interval_spin.value()
        self.auto_snapshot_toggled.emit(enabled, interval)
    
    def _on_browse_path(self) -> None:
        """Browse for base path"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Data Storage Location",
            self.base_path_edit.text()
        )
        
        if path:
            self.base_path_edit.setText(path)
    
    def _on_set_path(self) -> None:
        """Set base path"""
        path = self.base_path_edit.text()
        if path:
            self.base_path_changed.emit(path)


if __name__ == "__main__":
    """Test files tab"""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    files_tab = FilesTab()
    files_tab.setWindowTitle("Files Tab Test")
    files_tab.resize(600, 500)
    files_tab.show()
    
    # Connect signals
    files_tab.export_summary_requested.connect(lambda: print("Export summary requested"))
    files_tab.export_excel_chart_requested.connect(lambda: print("Export Excel chart requested"))
    files_tab.export_waveform_png_requested.connect(lambda: print("Export waveform PNG requested"))
    files_tab.auto_snapshot_toggled.connect(lambda en, iv: print(f"Auto snapshot: {en}, Interval: {iv}s"))
    files_tab.base_path_changed.connect(lambda p: print(f"Base path changed: {p}"))
    
    # Simulate session start
    files_tab.update_session_paths(
        "./data/2024-01-01/sensor_data_103045.csv",
        "./data/2024-01-01/sensor_data_103045.xlsx"
    )
    
    sys.exit(app.exec())
