#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replay Controller

Coordinates replay playback state and timer-driven frame updates.
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from core.replay_engine import ReplayEngine


class ReplayController(QObject):
    """Playback controller for replay mode."""

    replay_loaded = pyqtSignal(str, int)  # file_path, total_frames
    replay_frame_changed = pyqtSignal(object, int, int)  # SensorData, current_index, total_frames
    replay_started = pyqtSignal()
    replay_paused = pyqtSignal()
    replay_stopped = pyqtSignal()
    replay_finished = pyqtSignal()
    replay_error = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.engine = ReplayEngine()
        self.is_playing = False
        self.base_interval_ms = 1000  # replay tick
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_tick)

    def load_file(self, file_path: str) -> bool:
        ok = self.engine.load_csv(file_path)
        if not ok:
            self.replay_error.emit("Failed to load replay CSV")
            return False
        self.engine.seek(0)
        self._emit_current_frame()
        self.replay_loaded.emit(file_path, self.engine.total_frames())
        return True

    def set_speed(self, speed: float) -> None:
        self.engine.set_speed(speed)
        interval = max(100, int(self.base_interval_ms / self.engine.speed))
        self.timer.setInterval(interval)

    def play(self) -> None:
        if not self.engine.is_loaded():
            self.replay_error.emit("No replay file loaded")
            return
        if self.is_playing:
            return
        self.is_playing = True
        self.set_speed(self.engine.speed)
        self.timer.start()
        self.replay_started.emit()

    def pause(self) -> None:
        if not self.is_playing:
            return
        self.is_playing = False
        self.timer.stop()
        self.replay_paused.emit()

    def stop(self) -> None:
        self.pause()
        if self.engine.is_loaded():
            self.engine.seek(0)
            self._emit_current_frame()
        self.replay_stopped.emit()

    def seek(self, index: int) -> None:
        if not self.engine.is_loaded():
            return
        self.engine.seek(index)
        self._emit_current_frame()

    def step_next(self) -> None:
        if not self.engine.is_loaded():
            return
        moved = self.engine.step_forward()
        self._emit_current_frame()
        if not moved:
            self.pause()
            self.replay_finished.emit()

    def step_prev(self) -> None:
        if not self.engine.is_loaded():
            return
        self.engine.step_backward()
        self._emit_current_frame()

    def _on_tick(self) -> None:
        self.step_next()

    def _emit_current_frame(self) -> None:
        frame = self.engine.current_frame()
        if frame is None:
            return
        self.replay_frame_changed.emit(frame, self.engine.current_index, self.engine.total_frames())

