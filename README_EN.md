# Auto Clicker & Macro Recorder

[![GitHub release](https://img.shields.io/badge/release-v1.0.0-blue)](https://github.com/sonofstar/auto-clicker/releases/tag/v1.0.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Windows-green)]()

> A lightweight Windows desktop tool for auto-clicking and macro recording. Supports auto-click, mouse/keyboard action recording, and playback.

[中文文档](README.md)

## Features

### Auto Clicker
- Configurable click interval (1~60000 ms)
- Support left, right, and middle mouse buttons
- Fixed count or infinite clicking
- Follow cursor position or custom X/Y coordinates

### Macro Recording & Playback
- Record mouse clicks and keyboard presses
- Automatic timestamp recording between actions
- Adjustable playback speed (0.5x ~ 8x)
- Save recordings as JSON files, load and replay
- Real-time action list display

### Other
- Dark theme UI, clean and modern
- Global hotkeys, works even when window is not focused
- Multi-threaded, non-blocking UI
- Packaged as a single exe file, no Python installation required

## Installation

### Option 1: Download exe (Recommended)

1. Go to the [Releases](https://github.com/sonofstar/auto-clicker/releases) page
2. Download `auto-clicker-v1.0.0.exe`
3. Double-click to run

### Option 2: Run from source

```bash
# Clone the repository
git clone https://github.com/sonofstar/auto-clicker.git
cd auto-clicker

# Install dependencies
pip install pynput

# Run
python auto_clicker.py
```

## Usage

### Auto Clicking

1. Set parameters in the "Auto Clicker" tab (interval, button, count, position)
2. Press `F6` or click the "Start" button
3. Move your mouse to the target position, the program will click automatically
4. Press `F6` or `ESC` to stop

### Recording & Playback

1. Switch to the "Record & Playback" tab
2. Press `F7` to start recording
3. Use your mouse and keyboard normally, all actions will be recorded
4. Press `F7` to stop recording
5. Select playback speed
6. Press `F8` to start playback
7. Click "Save" to store actions as a JSON file, use "Load" to replay later

## Hotkeys

| Key | Action |
|-----|--------|
| `F6` | Start / Stop auto-clicking |
| `F7` | Start / Stop recording |
| `F8` | Playback recorded actions |
| `ESC` | Emergency stop all operations |

> Hotkeys are global — they work even when the application window is not in focus.

## Changelog

### v1.0.0 (2025-07-30)

- Initial release
- Auto-clicker with configurable interval, count, button, and position
- Mouse/keyboard macro recording and playback
- Recording save/load (JSON format)
- Global hotkey support (F6/F7/F8/ESC)
- Dark theme GUI
- Windows single-file exe packaging

## Tech Stack

- **Python 3.13** — Programming language
- **tkinter** — GUI framework
- **pynput** — Mouse/keyboard control and listening
- **PyInstaller** — exe packaging

## License

[MIT License](LICENSE)
