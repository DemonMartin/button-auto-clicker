# Auto Clicker

[![Build](https://img.shields.io/github/actions/workflow/status/DemonMartin/button-auto-clicker/build.yml?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/actions/workflows/build.yml) [![Release](https://img.shields.io/github/v/release/DemonMartin/button-auto-clicker?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/releases/latest) [![Stars](https://img.shields.io/github/stars/DemonMartin/button-auto-clicker?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/stargazers) [![Issues](https://img.shields.io/github/issues/DemonMartin/button-auto-clicker?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/issues) [![License](https://img.shields.io/github/license/DemonMartin/button-auto-clicker?style=flat-square)](LICENSE) ![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-blue?style=flat-square) ![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)

A lightweight button auto-clicker for Windows and macOS with a simple GUI and customizable timing.

---

## Features

* **Target selection:** any keyboard key or mouse button (left, right, middle, and X1/X2 side buttons on Windows).
* **Global toggle hotkey:** start/stop with a key or a mouse side button, even while another window is focused (default `F8`).
* **Delay range:** random delay between a minimum and maximum (ms).
* **Jitter:** extra random variation (%) for more human-like timing.
* **Hold time:** press-and-hold with configurable min/max duration.
* **Portable:** a single `.exe` on Windows (no admin rights needed), an `.app` on macOS.

---

## Download

Get the file for your system from the [latest release](https://github.com/DemonMartin/button-auto-clicker/releases/latest):

| System | File |
| --- | --- |
| Windows | `AutoClicker.exe` (just run it) |
| macOS, Apple Silicon (M1 and newer) | `AutoClicker-macOS-arm64.zip` |
| macOS, Intel | `AutoClicker-macOS-x86_64.zip` |

Each file has a `.sha256` checksum next to it.

**Windows:** SmartScreen or some antivirus tools may warn about unsigned PyInstaller executables. This is a common false positive; you can always run from source instead.

**macOS:**

1. Unzip and move `AutoClicker.app` to Applications.
2. The app is not signed with an Apple Developer ID, so the first time, right-click it and choose **Open**, then confirm. (On macOS 15+, if there is no Open button, go to System Settings > Privacy & Security and click **Open Anyway**.)
3. Allow the app under System Settings > Privacy & Security > **Accessibility** and **Input Monitoring**, then restart it. Without these, macOS silently blocks both the hotkey and the clicks; the app shows a warning if they are missing.

Note that on macOS laptops, `F8` is a media key by default; press `fn` + `F8`, or set a different toggle key.

---

## Usage

1. Start `AutoClicker.exe` / `AutoClicker.app` (or `python gui.py`).
2. Click **Set Target**, then press the key or click the mouse button to automate (`Esc` cancels).
3. Optionally click **Set Toggle** to change the start/stop hotkey (it must differ from the target; left click is not allowed).
4. Configure **Delay Min/Max**, **Jitter** and **Hold Time**.
5. Press **Start** or the toggle hotkey. Press **Stop** or the hotkey again to stop.

Settings are locked while running; stop to change them.

---

## Running from source

```bash
pip install -r requirements.txt
```

```bash
python gui.py
```

## Building the executable yourself

```bash
pip install -r requirements.txt pyinstaller
```

```bash
pyinstaller --onefile --windowed --name AutoClicker --optimize 2 --noupx --hidden-import pynput.keyboard._win32 --hidden-import pynput.mouse._win32 gui.py
```

The result is `dist/AutoClicker.exe`. On macOS:

```bash
pyinstaller --windowed --name AutoClicker --optimize 2 --noupx --hidden-import pynput.keyboard._darwin --hidden-import pynput.mouse._darwin gui.py
```

This creates `dist/AutoClicker.app`.

## Releases (automated)

The [`build.yml`](.github/workflows/build.yml) workflow builds the Windows `.exe` and the macOS `.app` (Apple Silicon and Intel) on GitHub runners and smoke-tests that each one launches:

* **When you publish a GitHub release**, all binaries and their checksums are attached to that release automatically.
* On pushes to `main` and on pull requests, the builds are uploaded as downloadable workflow artifacts.
* It can also be started manually from the Actions tab.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
