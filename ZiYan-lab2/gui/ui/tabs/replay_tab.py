#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replay Tab

UI controls for loading and playing back historical CSV data.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QSlider,
    QComboBox,
    QGroupBox,
    QLineEdit,
)


class ReplayTab(QWidget):
    """Replay tab with file picker and playback controls."""

    file_load_requested = pyqtSignal(str)
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    prev_requested = pyqtSignal()
    next_requested = pyqtSignal()
    seek_requested = pyqtSignal(int)
    speed_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._slider_user_dragging = False
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        file_group = QGroupBox("Replay File")
        file_layout = QHBoxLayout(file_group)
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText("Select CSV file to replay...")
        browse_btn = QPushButton("Browse CSV...")
        browse_btn.clicked.connect(self._on_browse_clicked)
        file_layout.addWidget(self.file_path_edit, stretch=1)
        file_layout.addWidget(browse_btn)
        layout.addWidget(file_group)

        ctrl_group = QGroupBox("Playback Controls")
        ctrl_layout = QHBoxLayout(ctrl_group)
        self.prev_btn = QPushButton("⏮ Prev")
        self.play_btn = QPushButton("▶ Play")
        self.pause_btn = QPushButton("⏸ Pause")
        self.stop_btn = QPushButton("⏹ Stop")
        self.next_btn = QPushButton("⏭ Next")
        for btn in [self.prev_btn, self.play_btn, self.pause_btn, self.stop_btn, self.next_btn]:
            ctrl_layout.addWidget(btn)

        ctrl_layout.addWidget(QLabel("Speed:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["1x", "2x", "4x"])
        ctrl_layout.addWidget(self.speed_combo)
        ctrl_layout.addStretch()
        layout.addWidget(ctrl_group)

        timeline_group = QGroupBox("Timeline")
        timeline_layout = QVBoxLayout(timeline_group)
        self.timeline_slider = QSlider(Qt.Orientation.Horizontal)
        self.timeline_slider.setRange(0, 0)
        self.timeline_label = QLabel("Frame: 0 / 0")
        timeline_layout.addWidget(self.timeline_slider)
        timeline_layout.addWidget(self.timeline_label)
        layout.addWidget(timeline_group)

        self.status_label = QLabel("Replay idle")
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.prev_btn.clicked.connect(self.prev_requested.emit)
        self.play_btn.clicked.connect(self.play_requested.emit)
        self.pause_btn.clicked.connect(self.pause_requested.emit)
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        self.next_btn.clicked.connect(self.next_requested.emit)
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        self.timeline_slider.sliderPressed.connect(self._on_slider_pressed)
        self.timeline_slider.sliderReleased.connect(self._on_slider_released)

    def _on_browse_clicked(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Replay CSV", "", "CSV Files (*.csv)")
        if file_name:
            self.file_path_edit.setText(file_name)
            self.file_load_requested.emit(file_name)

    def _on_speed_changed(self, text: str) -> None:
        speed = 1.0
        if text == "2x":
            speed = 2.0
        elif text == "4x":
            speed = 4.0
        self.speed_changed.emit(speed)

    def _on_slider_pressed(self) -> None:
        self._slider_user_dragging = True

    def _on_slider_released(self) -> None:
        self._slider_user_dragging = False
        self.seek_requested.emit(self.timeline_slider.value())

    def set_loaded_file(self, file_path: str, total_frames: int) -> None:
        self.file_path_edit.setText(file_path)
        self.timeline_slider.setRange(0, max(0, total_frames - 1))
        self.timeline_slider.setValue(0)
        self.timeline_label.setText(f"Frame: 1 / {total_frames}" if total_frames > 0 else "Frame: 0 / 0")
        self.status_label.setText("Replay file loaded")

    def set_frame(self, current_index: int, total_frames: int) -> None:
        if not self._slider_user_dragging:
            self.timeline_slider.setValue(current_index)
        self.timeline_label.setText(
            f"Frame: {current_index + 1} / {total_frames}" if total_frames > 0 else "Frame: 0 / 0"
        )

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

