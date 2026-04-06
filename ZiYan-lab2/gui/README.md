# STM32 DHT11 Monitoring System - GUI

Professional desktop application for real-time temperature & humidity monitoring.

## Features

- **Real-time Monitoring**: Live data visualization with dual-axis waveform charts
- **Data Logging**: Automatic CSV/Excel export with daily folder organization
- **Alarm System**: Configurable thresholds with audio alerts
- **Replay Mode**: Historical data playback with synchronized updates
- **Professional UI**: Multi-tab interface with modern design

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Navigate to the GUI directory:
```bash
cd lab2/gui
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Application

```bash
python main.py
```

## Project Structure

```
gui/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── core/                   # Business logic layer
├── ui/                     # View layer (tabs, widgets, dialogs)
├── controllers/            # Controller layer (MVC pattern)
├── utils/                  # Utility modules
├── resources/              # Assets (icons, sounds, styles)
└── tests/                  # Unit tests
```

## Configuration

Configuration is stored in `config.json` (auto-created on first run):
- Serial port settings
- Alarm thresholds
- Logging preferences
- UI preferences

## Hardware Connection

- Connect STM32F103C8T6 via USB (CH340 adapter)
- Default baudrate: 115200
- Data format: `DATA,<temp>,<humidity>,<oled_state>\r\n`

## Development Status

Current implementation phase: **Stage 1 - Foundation**

## License

MIT License - See LICENSE file for details
