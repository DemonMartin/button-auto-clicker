import threading
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox

import pyautogui
import keyboard  # Requires administrator privileges on Windows
from pynput.keyboard import Listener as KeyboardListener, Key as PKey
from pynput.mouse import Controller as MouseController, Button as MouseButton, Listener as MouseListener

# Supported keys and buttons
SUPPORTED_KEYS = [
    *[chr(c) for c in range(ord('a'), ord('z')+1)],
    *[str(n) for n in range(0, 10)],
    'enter', 'space', 'tab', 'esc', 'backspace', 'delete',
    'home', 'end', 'page_up', 'page_down',
    'up', 'down', 'left', 'right',
    'shift', 'ctrl', 'alt',
    *[f'f{i}' for i in range(1, 13)]
]
SUPPORTED_BUTTONS = ['left', 'right',
                     'middle', 'x1', 'x2', 'button4', 'button5']
# Map to pynput Button
BUTTON_MAPPING = {
    'left': MouseButton.left,
    'right': MouseButton.right,
    'middle': MouseButton.middle,
    'x1': MouseButton.x1,
    'button4': MouseButton.x1,
    'x2': MouseButton.x2,
    'button5': MouseButton.x2
}


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        root.title("Auto Clicker")
        root.configure(bg="#f5f5f5")
        root.resizable(False, False)

        # Theme
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabelframe', background='#ffffff',
                        font=('Segoe UI', 10, 'bold'))
        style.configure('TLabelframe.Label', background='#f5f5f5')
        style.configure('TLabel', background='#ffffff', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=6)
        style.configure('TCheckbutton', background='#ffffff',
                        font=('Segoe UI', 10))
        style.configure('TSpinbox', background='#ffffff',
                        font=('Segoe UI', 10))
        style.configure('TScale', background='#ffffff')

        # State
        self.running = False
        self.thread = None
        self.mouse = MouseController()
        self.target = None
        self.toggle_key = 'f8'
        self.delay_min = tk.IntVar(value=100)
        self.delay_max = tk.IntVar(value=100)
        self.jitter_enabled = tk.BooleanVar(value=False)
        self.jitter_pct = tk.IntVar(value=10)
        self.hold_enabled = tk.BooleanVar(value=False)
        self.hold_min = tk.IntVar(value=50)
        self.hold_max = tk.IntVar(value=100)

        # Layout
        container = ttk.Frame(root, padding=20)
        container.grid()

        settings = ttk.Labelframe(container, text="Settings", padding=10)
        settings.grid(row=0, column=0, sticky='ew')
        for i in range(4):
            settings.columnconfigure(i, weight=1)

        # Target
        ttk.Label(settings, text="Target (click/key):").grid(row=0,
                                                             column=0, sticky='w', pady=5)
        self.target_label = ttk.Label(settings, text="None", width=10)
        self.target_label.grid(row=0, column=1, sticky='w', padx=5)
        ttk.Button(settings, text="Set Target", command=self.set_target).grid(
            row=0, column=2, columnspan=2, sticky='e')

        # Toggle key
        ttk.Label(settings, text="Toggle (start/stop):").grid(row=1,
                                                              column=0, sticky='w', pady=5)
        self.toggle_label = ttk.Label(
            settings, text=self.toggle_key.upper(), width=10)
        self.toggle_label.grid(row=1, column=1, sticky='w', padx=5)
        ttk.Button(settings, text="Set Toggle", command=self.set_toggle).grid(
            row=1, column=2, columnspan=2, sticky='e')

        # Delay min/max
        ttk.Label(settings, text="Delay Min (ms):").grid(
            row=2, column=0, sticky='w', pady=5)
        self.delay_min_spin = ttk.Spinbox(
            settings, from_=1, to=60000, textvariable=self.delay_min, width=8)
        self.delay_min_spin.grid(row=2, column=1, sticky='w', padx=5)
        ttk.Label(settings, text="Max (ms):").grid(row=2, column=2, sticky='w')
        self.delay_max_spin = ttk.Spinbox(
            settings, from_=1, to=60000, textvariable=self.delay_max, width=8)
        self.delay_max_spin.grid(row=2, column=3, sticky='w', padx=5)

        # Jitter
        ttk.Checkbutton(settings, text="Enable jitter", variable=self.jitter_enabled,
                        command=self.toggle_jitter).grid(row=3, column=0, sticky='w', pady=5)
        self.jitter_slider = ttk.Scale(
            settings, from_=0, to=100, variable=self.jitter_pct, orient='horizontal', state='disabled')
        self.jitter_slider.grid(
            row=3, column=1, columnspan=3, sticky='ew', padx=5)

        # Hold time
        ttk.Checkbutton(settings, text="Enable hold time", variable=self.hold_enabled,
                        command=self.toggle_hold).grid(row=4, column=0, sticky='w', pady=5)
        ttk.Label(settings, text="Hold Min (ms):").grid(
            row=5, column=0, sticky='w', pady=5)
        self.hold_min_spin = ttk.Spinbox(
            settings, from_=0, to=10000, textvariable=self.hold_min, width=8, state='disabled')
        self.hold_min_spin.grid(row=5, column=1, sticky='w', padx=5)
        ttk.Label(settings, text="Max (ms):").grid(row=5, column=2, sticky='w')
        self.hold_max_spin = ttk.Spinbox(
            settings, from_=0, to=10000, textvariable=self.hold_max, width=8, state='disabled')
        self.hold_max_spin.grid(row=5, column=3, sticky='w', padx=5)

        # Control
        control = ttk.Labelframe(container, text="Control", padding=10)
        control.grid(row=1, column=0, pady=20, sticky='ew')
        for i in range(3):
            control.columnconfigure(i, weight=1)
        self.start_btn = ttk.Button(control, text="Start", command=self.start)
        self.start_btn.grid(row=0, column=0, padx=10)
        self.stop_btn = ttk.Button(
            control, text="Stop", command=self.stop, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=10)
        self.status_label = ttk.Label(control, text="Status: Stopped")
        self.status_label.grid(row=0, column=2, padx=10)

        keyboard.add_hotkey(self.toggle_key, self.toggle)

    def toggle_jitter(self):
        if self.jitter_enabled.get():
            self.jitter_slider.state(['!disabled'])
        else:
            self.jitter_slider.state(['disabled'])

    def toggle_hold(self):
        if self.hold_enabled.get():
            self.hold_min_spin.state(['!disabled'])
            self.hold_max_spin.state(['!disabled'])
        else:
            self.hold_min_spin.state(['disabled'])
            self.hold_max_spin.state(['disabled'])

    def set_target(self):
        val = self._capture_input()
        if val:
            self.target = val
            self.target_label.config(text=val.upper())

    def set_toggle(self):
        val = self._capture_input()
        if val:
            keyboard.clear_all_hotkeys()
            self.toggle_key = val
            self.toggle_label.config(text=val.upper())
            keyboard.add_hotkey(self.toggle_key, self.toggle)

    def _capture_input(self):
        result = {'val': None}

        def on_key(key):
            if key == PKey.esc:
                result['val'] = None
            else:
                result['val'] = key.char.lower() if getattr(
                    key, 'char', None) else key.name.lower()
            listener_k.stop()
            listener_m.stop()

        def on_click(x, y, button, pressed):
            if pressed:
                result['val'] = button.name.lower()
                listener_k.stop()
                listener_m.stop()
        listener_k = KeyboardListener(on_press=on_key)
        listener_m = MouseListener(on_click=on_click)
        listener_k.start()
        listener_m.start()
        listener_k.join()
        listener_m.join()
        return result['val']

    def start(self):
        if not self.target:
            messagebox.showwarning(
                "Warning", "Please set a target before starting.")
            return
        self.running = True
        self.start_btn.state(['disabled'])
        self.stop_btn.state(['!disabled'])
        self.status_label.config(text="Status: Running")
        self.thread = threading.Thread(target=self._click_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.start_btn.state(['!disabled'])
        self.stop_btn.state(['disabled'])
        self.status_label.config(text="Status: Stopped")

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def _click_loop(self):
        while self.running:
            dmin, dmax = self.delay_min.get(), self.delay_max.get()
            delay_ms = random.randint(min(dmin, dmax), max(dmin, dmax))
            if self.jitter_enabled.get():
                jitter_range = delay_ms * self.jitter_pct.get() / 100.0
                delay_ms += random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay_ms) / 1000.0
            hold_time = 0
            if self.hold_enabled.get():
                hmin, hmax = self.hold_min.get(), self.hold_max.get()
                hold_time = random.uniform(
                    min(hmin, hmax), max(hmin, hmax)) / 1000.0
            tgt = self.target
            if tgt in BUTTON_MAPPING:
                btn = BUTTON_MAPPING[tgt]
                if hold_time > 0:
                    self.mouse.press(btn)
                    time.sleep(hold_time)
                    self.mouse.release(btn)
                else:
                    self.mouse.click(btn)
            else:
                if hold_time > 0:
                    pyautogui.keyDown(tgt)
                    time.sleep(hold_time)
                    pyautogui.keyUp(tgt)
                else:
                    pyautogui.press(tgt)
            time.sleep(delay)


if __name__ == '__main__':
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()
