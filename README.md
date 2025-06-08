# Auto Clicker

[![Stars](https://img.shields.io/github/stars/DemonMartin/button-auto-clicker?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/stargazers) [![Forks](https://img.shields.io/github/forks/DemonMartin/button-auto-clicker?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/network) [![Issues](https://img.shields.io/github/issues/DemonMartin/button-auto-clicker?style=flat-square)](https://github.com/DemonMartin/button-auto-clicker/issues) [![License](https://img.shields.io/github/license/DemonMartin/button-auto-clicker?style=flat-square)](LICENSE) \[![Platform](https://img.shields.io/badge/platform-Windows-blue?style=flat-square)] \[![Python](https://img.shields.io/badge/python-3.12%2B-blue?style=flat-square)]

A lightweight button auto-clicker **made by AI (thx ChatGPT)** for Windows, featuring a modern GUI and customizable behavior.

---

## 🚀 Features

* **Target Selection:** Choose any keyboard key or mouse button (including extra buttons: X1/X2, Button4/5).
* **Toggle Hotkey:** Define a start/stop key for instant control.
* **Delay Range:** Configure minimum/maximum delay (ms) between actions.
* **Jitter Support:** Add random variation (%) for human-like timing.
* **Hold Time:** Enable press-and-hold with configurable min/max durations.
* **Modern GUI:** Built with Tkinter & `ttk.Clam` theme for a polished look.

---

## 🛠️ Installation

1. **Download** the latest ZIP or installer from the [Releases](https://github.com/DemonMartin/button-auto-clicker/releases) page.
2. **Extract** and run `gui.exe`, or use the source:

   ```bash
   pip install pyautogui keyboard pynput
   python gui.py
   ```

---

## 🎮 Usage

1. Launch `gui.exe` (or `gui.py`).
2. Click **Set Target** and press or click the desired input (ESC to cancel).
3. Click **Set Toggle** to choose your start/stop hotkey.
4. Configure **Delay Min/Max**, **Enable Jitter**, and **Hold Time** settings.
5. Press **Start** (or use the toggle key) to begin, and **Stop** to end.

---

## 📥 Releases

Find the precompiled Windows executable (`gui.exe`) and installer under the [Releases](https://github.com/DemonMartin/button-auto-clicker/releases) section.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
