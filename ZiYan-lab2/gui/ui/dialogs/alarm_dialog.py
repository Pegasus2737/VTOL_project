#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alarm Dialog

QMessageBox-based dialog for alarm notifications
"""

from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import Qt


class AlarmDialog:
    """Alarm notification dialog"""
    
    @staticmethod
    def show_temperature_alarm(parent: QWidget, temperature: float, threshold: float) -> None:
        """
        Show temperature alarm dialog
        
        Args:
            parent: Parent widget
            temperature: Current temperature
            threshold: Temperature threshold
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Temperature Alarm")
        msg.setText(f"<b>Temperature Alert!</b>")
        msg.setInformativeText(
            f"Current temperature <b>{temperature:.1f}°C</b> exceeds "
            f"threshold <b>{threshold:.1f}°C</b>."
        )
        msg.setDetailedText(
            f"Temperature: {temperature:.1f}°C\n"
            f"Threshold: {threshold:.1f}°C\n"
            f"Difference: +{temperature - threshold:.1f}°C"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        # Style
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        msg.exec()
    
    @staticmethod
    def show_humidity_alarm(parent: QWidget, humidity: float, threshold: float) -> None:
        """
        Show humidity alarm dialog
        
        Args:
            parent: Parent widget
            humidity: Current humidity
            threshold: Humidity threshold
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Humidity Alarm")
        msg.setText(f"<b>Humidity Alert!</b>")
        msg.setInformativeText(
            f"Current humidity <b>{humidity:.1f}%</b> exceeds "
            f"threshold <b>{threshold:.1f}%</b>."
        )
        msg.setDetailedText(
            f"Humidity: {humidity:.1f}%\n"
            f"Threshold: {threshold:.1f}%\n"
            f"Difference: +{humidity - threshold:.1f}%"
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        # Style
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        
        msg.exec()
    
    @staticmethod
    def show_generic_alarm(parent: QWidget, title: str, message: str, 
                          details: str = None) -> None:
        """
        Show generic alarm dialog
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Main message
            details: Optional detailed text
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(f"<b>{message}</b>")
        
        if details:
            msg.setDetailedText(details)
        
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        # Style
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 5px 15px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        msg.exec()


if __name__ == "__main__":
    """Test alarm dialogs"""
    from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
    import sys
    
    print("=== Alarm Dialog Test ===\n")
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = QWidget()
    window.setWindowTitle("Alarm Dialog Test")
    layout = QVBoxLayout(window)
    
    # Test button 1: Temperature alarm
    temp_btn = QPushButton("Show Temperature Alarm")
    temp_btn.clicked.connect(
        lambda: AlarmDialog.show_temperature_alarm(window, 36.5, 35.0)
    )
    layout.addWidget(temp_btn)
    
    # Test button 2: Humidity alarm
    humi_btn = QPushButton("Show Humidity Alarm")
    humi_btn.clicked.connect(
        lambda: AlarmDialog.show_humidity_alarm(window, 85.0, 80.0)
    )
    layout.addWidget(humi_btn)
    
    # Test button 3: Generic alarm
    generic_btn = QPushButton("Show Generic Alarm")
    generic_btn.clicked.connect(
        lambda: AlarmDialog.show_generic_alarm(
            window,
            "System Alert",
            "Something unusual happened!",
            "This is a detailed description of the issue.\nMultiple lines supported."
        )
    )
    layout.addWidget(generic_btn)
    
    window.resize(300, 150)
    window.show()
    
    print("Click buttons to test alarm dialogs")
    print("✓ Test window created")
    
    sys.exit(app.exec())
