# Auto Clicker

[![Build](https://img.shields.io/github/actions/workflow/status/DemonMartin/button-auto-clicker/build.yml?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/actions/workflows/build.yml) [![Release](https://img.shields.io/github/v/release/DemonMartin/button-auto-clicker?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/releases/latest) [![Stars](https://img.shields.io/github/stars/DemonMartin/button-auto-clicker?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/stargazers) [![Issues](https://img.shields.io/github/issues/DemonMartin/button-auto-clicker?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/issues) [![License](https://img.shields.io/github/license/DemonMartin/button-auto-clicker?style=flat-square)](LICENSE) ![Platform](https://img.shields.io/badge/platform-Windows-blue?style=flat-square) ![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)

A lightweight button auto-clicker for Windows with a simple GUI and customizable timing.

---

## Features

* **Target selection:** any keyboard key or mouse button (left, right, middle, X1/X2 side buttons).
* **Global toggle hotkey:** start/stop with a key or a mouse side button, even while another window is focused (default `F8`).
* **Delay range:** random delay between a minimum and maximum (ms).
* **Jitter:** extra random variation (%) for more human-like timing.
* **Hold time:** press-and-hold with configurable min/max duration.
* **No admin rights needed**, single portable `.exe`.

---

## Download

Grab `AutoClicker.exe` from the [latest release](https://github.com/DemonMartin/button-auto-clicker/releases/latest) and run it. There is nothing to install or extract.

A `AutoClicker.exe.sha256` checksum is published next to it. Windows SmartScreen or some antivirus tools may warn about unsigned PyInstaller executables; this is a common false positive, and you can always run from source instead.

---

## Usage

1. Start `AutoClicker.exe` (or `python gui.py`).
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

The result is `dist/AutoClicker.exe`.

## Releases (automated)

The [`build.yml`](.github/workflows/build.yml) workflow builds `AutoClicker.exe` on a Windows runner and smoke-tests that it launches:

* **When you publish a GitHub release**, the `.exe` and its checksum are attached to that release automatically.
* On pushes to `main` and on pull requests, the build is uploaded as a downloadable workflow artifact.
* It can also be started manually from the Actions tab.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
