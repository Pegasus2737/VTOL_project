# Quick Start Guide

## Installation

1. Make sure Python 3.8+ is installed:
```bash
python --version
```

2. Navigate to the gui directory:
```bash
cd lab2\gui
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## Current Status - Stage 5 Complete ✓

**Completed Features:**

**Stage 1 - Foundation ✓**
- ✓ Project structure initialized
- ✓ Configuration management (config.json)
- ✓ Serial port manager with auto-detection
- ✓ Data parser for STM32 format
- ✓ Data storage with pandas
- ✓ Main window with 5-tab layout
- ✓ Connection control bar

**Stage 2 - Core Monitoring ✓**
- ✓ Terminal tab for raw UART data
- ✓ Statistics module (Min/Max/Avg)
- ✓ Real-time waveform chart (pyqtgraph)
- ✓ Statistics display panel
- ✓ Dashboard with live values
- ✓ Main controller integration

**Stage 3 - Data Logging ✓**
- ✓ File utilities with daily folder creation
- ✓ CSV/Excel data logger
- ✓ Logging controller with independent control
- ✓ Export utilities (Summary CSV, Excel charts, PNG)
- ✓ Files tab with export tools
- ✓ Auto-snapshot functionality

**Stage 4 - Settings & Alarm ✓**
- ✓ Settings tab with all configuration options
- ✓ Alarm manager with threshold checking
- ✓ Alarm latch mechanism to prevent repeated alerts
- ✓ Sound player with fallback support
- ✓ Alarm dialogs (Temperature/Humidity alerts)
- ✓ Alarm system integrated into main controller
- ✓ Alarm log CSV file

**Stage 5 - Replay ✓**
- ✓ Replay tab with dedicated controls
- ✓ CSV file loading for historical data
- ✓ Playback controls (play/pause/stop/prev/next)
- ✓ Timeline seek slider and frame indicator
- ✓ Playback speed control (1x/2x/4x)
- ✓ Replay integration with Dashboard, Terminal, and statistics

**What You Can Do Now:**
- ✅ Connect to STM32 via USB (auto-detect CH340/STM)
- ✅ View real-time temperature & humidity values
- ✅ See dual-axis waveform chart (updates every 5 seconds)
- ✅ Monitor Min/Max/Average statistics
- ✅ View raw UART data in Terminal tab
- ✅ Control Monitor/Logging independently
- ✅ Automatic CSV/Excel logging with daily folders
- ✅ Export summary statistics, Excel charts, PNG waveforms
- ✅ Auto-snapshot at configurable intervals
- ✅ Configure serial port, baud rate, storage paths
- ✅ Set temperature/humidity alarm thresholds
- ✅ Receive alarm notifications with sound
- ✅ View alarm history in Alarm_Log.csv
- ✅ Load historical CSV and replay data in Replay tab
- ✅ Control replay timeline and speed (1x/2x/4x)

## Testing Individual Modules

Each module has a built-in test:

```bash
# Core modules
python -m utils.config
python -m core.serial_manager
python -m core.data_parser
python -m core.data_store
python -m core.statistics
python -m core.logger
python -m core.alarm_manager

# UI widgets
python -m ui.tabs.terminal_tab
python -m ui.tabs.dashboard_tab
python -m ui.tabs.files_tab
python -m ui.tabs.settings_tab
python -m ui.widgets.waveform_widget
python -m ui.widgets.stats_panel
python -m ui.dialogs.alarm_dialog

# Utilities
python -m utils.file_utils
python -m utils.export_utils
python -m utils.sound_player
```

## How to Use

1. **Launch Application**
   ```bash
   python main.py
   ```

2. **Connect to STM32**
   - Click "Refresh" to scan ports
   - Auto-detected port will be selected
   - Click "Connect"

3. **Monitor Data**
   - Dashboard shows real-time values
   - Waveform updates every 5 seconds
   - Statistics calculate automatically

4. **Configure Settings**
   - Switch to "Settings" tab
   - Set temperature/humidity alarm thresholds
   - Configure auto-snapshot interval
   - Adjust chart update rate
   - Change storage path if needed

5. **Alarm Features**
   - Alarms trigger when values exceed thresholds
   - Sound notification plays (if enabled)
   - Alarm dialog shows details
   - Latch prevents repeated alerts
   - All alarms logged to `Alarm_Log.csv`

6. **Export Data**
   - Go to "Files" tab
   - Export summary CSV with statistics
   - Export Excel file with chart
   - Export waveform PNG snapshot
   - Enable auto-snapshot for periodic saves

## Expected Data Format

Your STM32 should send:
```
DATA,25.3,61.0,1
```

Format: `DATA,<temperature>,<humidity>,<oled_state>`

## File Structure

```
gui/
├── main.py                     ✓ Application entry point
├── requirements.txt            ✓ Python dependencies (includes pygame)
├── core/                       ✓ Business logic (STAGES 1-5 COMPLETE)
│   ├── serial_manager.py       ✓ Serial communication
│   ├── data_parser.py          ✓ Data parsing
│   ├── data_store.py           ✓ Data storage
│   ├── statistics.py           ✓ Statistics calculation
│   ├── logger.py               ✓ CSV/Excel logging
│   ├── alarm_manager.py        ✓ Alarm management
│   └── replay_engine.py        ✓ Replay engine (NEW)
├── ui/                         ✓ User interface (STAGES 1-5 COMPLETE)
│   ├── main_window.py          ✓ Main window
│   ├── tabs/
│   │   ├── dashboard_tab.py    ✓ Dashboard
│   │   ├── terminal_tab.py     ✓ Terminal
│   │   ├── files_tab.py        ✓ Files
│   │   ├── settings_tab.py     ✓ Settings
│   │   └── replay_tab.py       ✓ Replay controls (NEW)
│   ├── widgets/
│   │   ├── connection_bar.py   ✓ Connection controls
│   │   ├── waveform_widget.py  ✓ Waveform chart
│   │   └── stats_panel.py      ✓ Statistics panel
│   └── dialogs/
│       └── alarm_dialog.py     ✓ Alarm notifications
├── controllers/                ✓ Controllers
│   ├── main_controller.py      ✓ Main controller (with replay + alarm integration)
│   ├── logging_controller.py   ✓ Logging controller
│   └── replay_controller.py    ✓ Replay controller (NEW)
└── utils/                      ✓ Utilities
    ├── config.py               ✓ Configuration
  ├── file_utils.py           ✓ File management
  ├── export_utils.py         ✓ Export tools
  └── sound_player.py         ✓ Sound playback
```

## Configuration

After first run, `config.json` will be created with default settings:

```json
{
  "serial": {
    "port": "COM3",
    "baud_rate": 115200,
    "auto_connect": true
  },
  "logging": {
    "enabled": false,
    "base_path": "./data",
    "auto_create_daily_folder": true,
    "sync_interval_sec": 2
  },
  "alarm": {
    "temperature_high": 35.0,
    "humidity_high": 80.0,
    "sound_enabled": true,
    "latch_enabled": true
  },
  "chart": {
    "update_interval_sec": 5,
    "history_minutes": 5,
    "auto_snapshot_enabled": false,
    "auto_snapshot_interval_sec": 60
  },
  "ui": {
    "theme": "dark",
    "window_width": 1200,
    "window_height": 800
  }
}
```

You can edit these values in the **Settings tab** or directly in `config.json`.

## Troubleshooting

**Module import errors:**
Make sure you're running from the `gui/` directory.

**Serial port issues:**
- Ensure CH340 drivers are installed
- Check Device Manager for COM port number
- Try running as administrator if access denied

**PyQt6 import errors:**
Reinstall PyQt6:
```bash
pip uninstall PyQt6 PyQt6-Qt6
pip install PyQt6
```

**pyqtgraph not found:**
```bash
pip install pyqtgraph
```

**Chart not updating:**
- Check if Monitor is ON (button should be green)
- Verify data is arriving in Terminal tab
- Waveform updates every 5 seconds (not immediate)

**Alarm not working:**
- Check thresholds in Settings tab
- Ensure alarm is not latched (value must return to normal first)
- Check if sound is enabled in Settings
- Verify `Alarm_Log.csv` is being created in daily folder

**pygame/Sound issues:**
- pygame 在 Python 3.12+ 有編譯問題（distutils 已移除）
- **不用擔心！** 系統會自動使用 Windows 內建的 winsound 作為備援
- 警報音效仍然可以正常工作（使用系統嗶聲）
- 如果真的需要 pygame：
  - 方案 1：降級到 Python 3.11 或更低
  - 方案 2：`pip install pygame --pre` （測試版）
  - 方案 3：從 pygame.org 下載預編譯 wheel
- 檢查音效狀態：啟動應用程式時會顯示使用哪個音效引擎

## Progress: Stage 5 Complete
