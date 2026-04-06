#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Terminal Tab

Displays raw UART serial data stream for debugging purposes.
Features:
- Auto-scrolling text display
- Clear button
- Line limit to prevent memory issues
- Timestamp display
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPlainTextEdit, QPushButton, QLabel,
    QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor
from datetime import datetime


class TerminalTab(QWidget):
    """Terminal tab for raw serial data display"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_lines = 1000  # Default max lines
        self.show_timestamp = True
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        # Timestamp checkbox
        self.timestamp_check = QCheckBox("Show Timestamp")
        self.timestamp_check.setChecked(True)
        self.timestamp_check.stateChanged.connect(self._on_timestamp_toggled)
        control_layout.addWidget(self.timestamp_check)
        
        # Max lines label and spinbox
        control_layout.addWidget(QLabel("Max Lines:"))
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(100, 10000)
        self.max_lines_spin.setValue(1000)
        self.max_lines_spin.setSingleStep(100)
        self.max_lines_spin.valueChanged.connect(self._on_max_lines_changed)
        control_layout.addWidget(self.max_lines_spin)
        
        control_layout.addStretch()
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear)
        control_layout.addWidget(self.clear_btn)
        
        # Save log button
        self.save_btn = QPushButton("Save Log...")
        self.save_btn.clicked.connect(self._on_save_clicked)
        control_layout.addWidget(self.save_btn)
        
        layout.addLayout(control_layout)
        
        # Terminal text area
        self.terminal_text = QPlainTextEdit()
        self.terminal_text.setReadOnly(True)
        self.terminal_text.setMaximumBlockCount(self.max_lines)
        
        # Set monospace font
        font = QFont("Courier New", 9)
        self.terminal_text.setFont(font)
        
        # Style
        self.terminal_text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)
        
        layout.addWidget(self.terminal_text)
        
        # Status label
        self.status_label = QLabel("Terminal ready")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
    
    @pyqtSlot(str)
    def append_line(self, line: str) -> None:
        """
        Append a line to the terminal
        
        Args:
            line: Line to append (without newline)
        """
        if self.show_timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # ms precision
            formatted_line = f"[{timestamp}] {line}"
        else:
            formatted_line = line
        
        self.terminal_text.appendPlainText(formatted_line)
        
        # Auto-scroll to bottom
        self.terminal_text.moveCursor(QTextCursor.MoveOperation.End)
        
        # Update line count
        line_count = self.terminal_text.blockCount()
        self.status_label.setText(f"Lines: {line_count} / {self.max_lines}")
    
    def clear(self) -> None:
        """Clear terminal content"""
        self.terminal_text.clear()
        self.status_label.setText("Terminal cleared")
    
    def get_content(self) -> str:
        """
        Get all terminal content
        
        Returns:
            str: Terminal text content
        """
        return self.terminal_text.toPlainText()
    
    def _on_timestamp_toggled(self, state: int) -> None:
        """Handle timestamp checkbox toggle"""
        self.show_timestamp = (state == Qt.CheckState.Checked.value)
    
    def _on_max_lines_changed(self, value: int) -> None:
        """Handle max lines spinbox change"""
        self.max_lines = value
        self.terminal_text.setMaximumBlockCount(value)
    
    def _on_save_clicked(self) -> None:
        """Handle save log button click"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Terminal Log",
            f"terminal_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.get_content())
                self.status_label.setText(f"Log saved to: {filename}")
            except Exception as e:
                self.status_label.setText(f"Error saving log: {e}")


if __name__ == "__main__":
    """Test terminal tab"""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    terminal = TerminalTab()
    terminal.setWindowTitle("Terminal Tab Test")
    terminal.resize(800, 600)
    terminal.show()
    
    # Test: Add some sample lines
    test_lines = [
        "DATA,25.3,61.0,1",
        "DATA,25.4,60.8,1",
        "DEBUG: [ERR -1] No Response",
        "[BOOT] Hello from STM32F103",
        "DATA,25.2,61.5,0",
        "DATA,25.1,61.2,0",
    ]
    
    for line in test_lines:
        terminal.append_line(line)
    
    # Simulate continuous data
    from PyQt6.QtCore import QTimer
    counter = [0]
    
    def add_test_line():
        counter[0] += 1
        terminal.append_line(f"DATA,{25.0 + counter[0] * 0.1:.1f},{60.0 + counter[0] * 0.2:.1f},1")
    
    timer = QTimer()
    timer.timeout.connect(add_test_line)
    timer.start(100)  # Add line every 100ms for testing
    
    sys.exit(app.exec())
