#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Controller

Central controller that coordinates all components:
- Serial communication
- Data parsing and storage
- UI updates
- Chart refresh timing
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSlot
from core.serial_manager import SerialManager
from core.data_parser import DataParser, SensorData
from core.data_store import DataStore
from core.statistics import Statistics
from core.alarm_manager import AlarmManager
from controllers.replay_controller import ReplayController
from controllers.logging_controller import LoggingController
from utils.export_utils import ExportUtils
from utils.file_utils import FileUtils
from utils.sound_player import get_sound_player
from utils.config import get_config
from ui.dialogs.alarm_dialog import AlarmDialog


class MainController(QObject):
    """Main application controller (MVC pattern)"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Core components
        self.serial_manager = SerialManager()
        self.data_parser = DataParser()
        self.data_store = DataStore(max_history_minutes=60)
        self.statistics = Statistics()
        self.logging_controller = LoggingController()
        self.alarm_manager = AlarmManager()
        
        # Sound player
        self.sound_player = get_sound_player()
        
        # Config
        self.config = get_config()
        
        # UI references
        self.dashboard_tab = None
        self.terminal_tab = None
        self.files_tab = None
        self.settings_tab = None
        self.replay_tab = None
        
        # Chart update timer (5 seconds)
        self.chart_timer = QTimer()
        self.chart_timer.setInterval(5000)  # 5 seconds
        self.chart_timer.timeout.connect(self._on_chart_timer)
        
        # Auto-snapshot timer
        self.snapshot_timer = QTimer()
        self.snapshot_timer.timeout.connect(self._on_snapshot_timer)
        self.auto_snapshot_enabled = False
        self.is_replay_mode = False
        
        # Connection state
        self.is_connected = False
        self.is_monitoring = True  # Auto-start monitoring when connected
        self.is_logging = False
        
        # Setup connections
        self._setup_connections()
    
    def _setup_connections(self) -> None:
        """Setup signal/slot connections"""
        # Serial manager signals
        self.serial_manager.data_received.connect(self._on_data_received)
        self.serial_manager.connection_changed.connect(self._on_connection_changed)
        self.serial_manager.error_occurred.connect(self._on_serial_error)
        
        # Connection bar signals
        self.main_window.connection_bar.connect_requested.connect(self._on_connect_requested)
        self.main_window.connection_bar.disconnect_requested.connect(self._on_disconnect_requested)
        self.main_window.connection_bar.refresh_ports_requested.connect(self._on_refresh_ports)
        
        # Logging controller signals
        self.logging_controller.logging_started.connect(self._on_logging_started)
        self.logging_controller.logging_stopped.connect(self._on_logging_stopped)
        self.logging_controller.logging_error.connect(self._on_logging_error)
        
        # Alarm manager signals
        self.alarm_manager.alarm_triggered.connect(self._on_alarm_triggered)
        self.alarm_manager.alarm_cleared.connect(self._on_alarm_cleared)

        # Replay controller signals
        self.replay_controller = ReplayController()
        self.replay_controller.replay_loaded.connect(self._on_replay_loaded)
        self.replay_controller.replay_frame_changed.connect(self._on_replay_frame_changed)
        self.replay_controller.replay_started.connect(lambda: self.main_window.update_status("Replay started"))
        self.replay_controller.replay_paused.connect(lambda: self.main_window.update_status("Replay paused"))
        self.replay_controller.replay_stopped.connect(lambda: self.main_window.update_status("Replay stopped"))
        self.replay_controller.replay_finished.connect(lambda: self.main_window.update_status("Replay finished"))
        self.replay_controller.replay_error.connect(self._on_replay_error)
    
    def set_dashboard_tab(self, dashboard_tab) -> None:
        """
        Set dashboard tab reference
        
        Args:
            dashboard_tab: DashboardTab instance
        """
        self.dashboard_tab = dashboard_tab
        
        # Connect dashboard signals
        dashboard_tab.monitor_toggled.connect(self._on_monitor_toggled)
        dashboard_tab.logging_toggled.connect(self._on_logging_toggled)
    
    def set_terminal_tab(self, terminal_tab) -> None:
        """
        Set terminal tab reference
        
        Args:
            terminal_tab: TerminalTab instance
        """
        self.terminal_tab = terminal_tab
    
    def set_files_tab(self, files_tab) -> None:
        """
        Set files tab reference
        
        Args:
            files_tab: FilesTab instance
        """
        self.files_tab = files_tab
        
        # Connect files tab signals
        files_tab.export_summary_requested.connect(self._on_export_summary)
        files_tab.export_excel_chart_requested.connect(self._on_export_excel_chart)
        files_tab.export_waveform_png_requested.connect(self._on_export_waveform_png)
        files_tab.auto_snapshot_toggled.connect(self._on_auto_snapshot_toggled)
        files_tab.base_path_changed.connect(self._on_base_path_changed)
    
    def set_settings_tab(self, settings_tab) -> None:
        """
        Set settings tab reference
        
        Args:
            settings_tab: SettingsTab instance
        """
        self.settings_tab = settings_tab
        
        # Connect settings tab signals
        settings_tab.settings_changed.connect(self._on_settings_changed)

    def set_replay_tab(self, replay_tab) -> None:
        """Set replay tab reference and connect signals."""
        self.replay_tab = replay_tab
        replay_tab.file_load_requested.connect(self._on_replay_file_load)
        replay_tab.play_requested.connect(self._on_replay_play)
        replay_tab.pause_requested.connect(self._on_replay_pause)
        replay_tab.stop_requested.connect(self._on_replay_stop)
        replay_tab.prev_requested.connect(self._on_replay_prev)
        replay_tab.next_requested.connect(self._on_replay_next)
        replay_tab.seek_requested.connect(self._on_replay_seek)
        replay_tab.speed_changed.connect(self._on_replay_speed_changed)
    
    @pyqtSlot(str, int)
    def _on_connect_requested(self, port: str, baudrate: int) -> None:
        """Handle connection request"""
        # Leave replay mode when connecting to live device.
        self.is_replay_mode = False
        self.replay_controller.pause()
        if self.serial_manager.connect(port, baudrate):
            self.main_window.update_status(f"Connected to {port}")
            
            # Start chart update timer
            self.chart_timer.start()
        else:
            self.main_window.update_status(f"Failed to connect to {port}")
    
    @pyqtSlot()
    def _on_disconnect_requested(self) -> None:
        """Handle disconnection request"""
        self.serial_manager.disconnect()
        self.chart_timer.stop()
        self.main_window.update_status("Disconnected")
    
    @pyqtSlot()
    def _on_refresh_ports(self) -> None:
        """Handle port refresh request"""
        ports = self.serial_manager.list_available_ports()
        port_names = [p['device'] for p in ports]
        
        self.main_window.connection_bar.set_ports(port_names)
        self.main_window.update_status(f"Found {len(port_names)} ports")
        
        # Try auto-detect
        auto_port = self.serial_manager.find_stm32_port()
        if auto_port and auto_port in port_names:
            self.main_window.connection_bar.set_selected_port(auto_port)
            self.main_window.update_status(f"Auto-detected: {auto_port}")
    
    @pyqtSlot(bool)
    def _on_connection_changed(self, connected: bool) -> None:
        """Handle connection state change"""
        self.is_connected = connected
        
        port = self.main_window.connection_bar.get_selected_port()
        self.main_window.update_connection_status(connected, port)
        self.main_window.connection_bar.set_connected(connected, port)
        
        if not connected:
            # Reset on disconnect
            self.statistics.reset()
            if self.dashboard_tab:
                self.dashboard_tab.reset_display()
    
    @pyqtSlot(str)
    def _on_serial_error(self, error_msg: str) -> None:
        """Handle serial error"""
        self.main_window.update_status(f"Error: {error_msg}")
        
        # Also show in terminal if available
        if self.terminal_tab:
            self.terminal_tab.append_line(f"[ERROR] {error_msg}")
    
    @pyqtSlot(str)
    def _on_data_received(self, line: str) -> None:
        """
        Handle received serial data line
        
        Args:
            line: Raw line from serial port
        """
        # Always show in terminal
        if self.terminal_tab:
            self.terminal_tab.append_line(line)
        
        # Parse data
        data = self.data_parser.parse(line)
        
        if data and self.is_monitoring and not self.is_replay_mode:
            # Update statistics
            self.statistics.update(data.temperature, data.humidity)
            
            # Update data store
            self.data_store.add(data)
            
            # Update dashboard current values
            if self.dashboard_tab:
                self.dashboard_tab.update_current_values(
                    data.temperature,
                    data.humidity,
                    data.oled_state
                )
                
                # Add to waveform (but don't update chart yet - wait for timer)
                self.dashboard_tab.add_waveform_point(
                    data.temperature,
                    data.humidity,
                    data.timestamp
                )
                
                # Update statistics display
                stats = self.statistics.get_all_stats()
                self.dashboard_tab.update_statistics(stats)
            
            # Handle logging if enabled
            if self.is_logging:
                self.logging_controller.log_data(data)
            
            # Check alarms
            self.alarm_manager.check_values(data.temperature, data.humidity)
    
    def _on_chart_timer(self) -> None:
        """Handle chart update timer (every 5 seconds)"""
        if self.dashboard_tab and self.is_monitoring:
            self.dashboard_tab.update_waveform()
    
    @pyqtSlot(bool)
    def _on_monitor_toggled(self, enabled: bool) -> None:
        """Handle monitor toggle"""
        self.is_monitoring = enabled
        
        if enabled:
            self.main_window.update_status("Monitoring enabled")
        else:
            self.main_window.update_status("Monitoring paused")
    
    @pyqtSlot(bool)
    def _on_logging_toggled(self, enabled: bool) -> None:
        """Handle logging toggle"""
        self.is_logging = enabled
        
        if enabled:
            if self.logging_controller.start_logging():
                self.main_window.update_status("Logging started")
            else:
                # Failed to start, toggle button back off
                if self.dashboard_tab:
                    self.dashboard_tab.is_logging = False
                    self.dashboard_tab._on_logging_clicked()  # Toggle UI back
        else:
            self.logging_controller.stop_logging()
    
    @pyqtSlot(str, str)
    def _on_logging_started(self, csv_path: str, excel_path: str) -> None:
        """Handle logging started event"""
        if self.files_tab:
            self.files_tab.update_session_paths(csv_path, excel_path)
        self.main_window.update_status(f"Logging to: {csv_path}")
    
    @pyqtSlot(int)
    def _on_logging_stopped(self, record_count: int) -> None:
        """Handle logging stopped event"""
        if self.files_tab:
            self.files_tab.clear_session_paths()
        self.main_window.update_status(f"Logging stopped ({record_count} records)")
    
    @pyqtSlot(str)
    def _on_logging_error(self, error_msg: str) -> None:
        """Handle logging error"""
        self.main_window.update_status(f"Logging error: {error_msg}")
    
    @pyqtSlot()
    def _on_export_summary(self) -> None:
        """Handle export summary request"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Export Summary CSV",
            ExportUtils.generate_export_filename("summary", "csv"),
            "CSV Files (*.csv)"
        )
        
        if filename:
            info = self.logging_controller.get_session_info()
            if info and info['csv_path']:
                stats = self.statistics.get_all_stats()
                if ExportUtils.export_summary_csv(info['csv_path'], filename, stats):
                    self.main_window.update_status(f"Summary exported: {filename}")
    
    @pyqtSlot()
    def _on_export_excel_chart(self) -> None:
        """Handle export Excel chart request"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Export Excel with Chart",
            ExportUtils.generate_export_filename("data_chart", "xlsx"),
            "Excel Files (*.xlsx)"
        )
        
        if filename:
            info = self.logging_controller.get_session_info()
            if info and info['csv_path']:
                if ExportUtils.export_excel_with_chart(info['csv_path'], filename):
                    self.main_window.update_status(f"Excel chart exported: {filename}")
    
    @pyqtSlot()
    def _on_export_waveform_png(self) -> None:
        """Handle export waveform PNG request"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Export Waveform PNG",
            ExportUtils.generate_export_filename("waveform", "png"),
            "PNG Images (*.png)"
        )
        
        if filename and self.dashboard_tab:
            if ExportUtils.export_waveform_png(self.dashboard_tab.waveform, filename):
                self.main_window.update_status(f"Waveform PNG exported: {filename}")
    
    @pyqtSlot(bool, int)
    def _on_auto_snapshot_toggled(self, enabled: bool, interval_sec: int) -> None:
        """Handle auto-snapshot toggle"""
        self.auto_snapshot_enabled = enabled
        
        if enabled:
            self.snapshot_timer.setInterval(interval_sec * 1000)
            self.snapshot_timer.start()
            self.main_window.update_status(f"Auto-snapshot enabled ({interval_sec}s)")
        else:
            self.snapshot_timer.stop()
            self.main_window.update_status("Auto-snapshot disabled")
    
    def _on_snapshot_timer(self) -> None:
        """Handle auto-snapshot timer"""
        if not self.dashboard_tab or not self.auto_snapshot_enabled:
            return
        
        # Generate snapshot filename
        snapshot_dir = FileUtils.create_daily_folder("./snapshots")
        filename = snapshot_dir / ExportUtils.generate_export_filename("waveform", "png")
        
        # Export waveform
        if ExportUtils.export_waveform_png(self.dashboard_tab.waveform, str(filename)):
            print(f"Auto-snapshot saved: {filename}")
    
    @pyqtSlot(str)
    def _on_base_path_changed(self, path: str) -> None:
        """Handle base path change"""
        self.logging_controller.set_base_path(path)
        self.main_window.update_status(f"Data path set to: {path}")
    
    @pyqtSlot(bool)
    def _on_logging_toggled(self, enabled: bool) -> None:
        """Handle logging toggle"""
        self.is_logging = enabled
        
        if enabled:
            if self.logging_controller.start_logging():
                self.main_window.update_status("Logging started")
            else:
                # Failed to start
                if self.dashboard_tab:
                    self.dashboard_tab.is_logging = False
        else:
            self.logging_controller.stop_logging()
    
    @pyqtSlot(str, float, float, str)
    def _on_alarm_triggered(self, alarm_type: str, value: float, threshold: float, message: str) -> None:
        """Handle alarm triggered event"""
        # Play alarm sound if enabled
        sound_enabled = self.config.get('alarm.sound_enabled', True)
        if sound_enabled:
            self.sound_player.play_alarm()
        
        # Show dialog
        if "Temperature" in alarm_type:
            AlarmDialog.show_temperature_alarm(self.main_window, value, threshold)
        elif "Humidity" in alarm_type:
            AlarmDialog.show_humidity_alarm(self.main_window, value, threshold)
        
        # Update status
        self.main_window.update_status(f"ALARM: {message}")
    
    @pyqtSlot(str)
    def _on_alarm_cleared(self, alarm_type: str) -> None:
        """Handle alarm cleared event"""
        self.main_window.update_status(f"Alarm cleared: {alarm_type}")
    
    @pyqtSlot()
    def _on_settings_changed(self) -> None:
        """Handle settings changed event"""
        # Update alarm thresholds
        temp_threshold = self.config.get('alarm.temperature_high', 35.0)
        humi_threshold = self.config.get('alarm.humidity_high', 80.0)
        self.alarm_manager.set_thresholds(temp_threshold, humi_threshold)
        
        # Update latch setting
        latch_enabled = self.config.get('alarm.latch_enabled', True)
        self.alarm_manager.set_latch_enabled(latch_enabled)
        
        # Update sound setting
        sound_enabled = self.config.get('alarm.sound_enabled', True)
        self.sound_player.set_enabled(sound_enabled)
        
        # Update chart interval
        update_interval = self.config.get('chart.update_interval_sec', 5)
        self.chart_timer.setInterval(update_interval * 1000)
        
        self.main_window.update_status("Settings applied")

    @pyqtSlot(str)
    def _on_replay_file_load(self, file_path: str) -> None:
        if self.is_connected:
            self.serial_manager.disconnect()
        self.is_replay_mode = True
        self.statistics.reset()
        if self.dashboard_tab:
            self.dashboard_tab.reset_display()
        if self.replay_tab:
            self.replay_tab.set_status("Loading replay file...")
        self.replay_controller.load_file(file_path)

    @pyqtSlot()
    def _on_replay_play(self) -> None:
        self.is_replay_mode = True
        self.replay_controller.play()

    @pyqtSlot()
    def _on_replay_pause(self) -> None:
        self.replay_controller.pause()

    @pyqtSlot()
    def _on_replay_stop(self) -> None:
        self.replay_controller.stop()
        self.is_replay_mode = False

    @pyqtSlot()
    def _on_replay_prev(self) -> None:
        self.replay_controller.step_prev()

    @pyqtSlot()
    def _on_replay_next(self) -> None:
        self.replay_controller.step_next()

    @pyqtSlot(int)
    def _on_replay_seek(self, index: int) -> None:
        self.replay_controller.seek(index)

    @pyqtSlot(float)
    def _on_replay_speed_changed(self, speed: float) -> None:
        self.replay_controller.set_speed(speed)

    @pyqtSlot(str, int)
    def _on_replay_loaded(self, file_path: str, total_frames: int) -> None:
        if self.replay_tab:
            self.replay_tab.set_loaded_file(file_path, total_frames)
        self.main_window.update_status(f"Replay loaded: {total_frames} frames")

    @pyqtSlot(object, int, int)
    def _on_replay_frame_changed(self, data: SensorData, current_index: int, total_frames: int) -> None:
        if self.replay_tab:
            self.replay_tab.set_frame(current_index, total_frames)
            self.replay_tab.set_status("Replay running" if self.replay_controller.is_playing else "Replay paused")

        if self.terminal_tab:
            self.terminal_tab.append_line(f"[REPLAY] {data.raw_line}")

        if self.dashboard_tab:
            self.dashboard_tab.update_current_values(data.temperature, data.humidity, data.oled_state)
            self.dashboard_tab.add_waveform_point(data.temperature, data.humidity, data.timestamp)
            self.dashboard_tab.update_waveform()

        # Update statistics from replay data
        self.statistics.update(data.temperature, data.humidity)
        if self.dashboard_tab:
            self.dashboard_tab.update_statistics(self.statistics.get_all_stats())

    @pyqtSlot(str)
    def _on_replay_error(self, message: str) -> None:
        self.is_replay_mode = False
        self.main_window.update_status(f"Replay error: {message}")
    
    def initialize(self) -> None:
        """Initialize controller (call after UI is ready)"""
        # Populate ports list
        self._on_refresh_ports()
        
        # Load initial settings
        self._on_settings_changed()
        
        self.main_window.update_status("Ready")


if __name__ == "__main__":
    """Test main controller"""
    from PyQt6.QtWidgets import QApplication
    import sys
    
    print("=== Main Controller Test ===")
    print("This module should be tested through the main application.")
    print("Run: python main.py")
