"""Button Auto Clicker - repeatedly presses a keyboard key or mouse button.

All input (capturing, the global toggle hotkey and sending clicks/keys) goes
through pynput, so no administrator rights are needed and key names are
consistent everywhere.
"""

import queue
import random
import sys
import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk

from pynput import keyboard, mouse

APP_TITLE = "Auto Clicker"
POLL_MS = 30  # how often the GUI drains events coming from listener threads

DELAY_RANGE = (1, 60000)  # ms
HOLD_RANGE = (0, 10000)  # ms


# ---------------------------------------------------------------------------
# Input abstraction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Binding:
    """A single keyboard key or mouse button."""

    kind: str  # "key" or "mouse"
    value: object  # keyboard.Key / keyboard.KeyCode / mouse.Button

    @property
    def ident(self):
        """Hashable identity used to compare a captured binding to live events."""
        return (self.kind, key_ident(self.value) if self.kind == "key" else self.value)

    @property
    def label(self):
        if self.kind == "mouse":
            return f"Mouse {self.value.name.upper()}"
        v = self.value
        if isinstance(v, keyboard.Key):
            return v.name.upper()
        if v.char:
            return v.char.upper()
        return f"VK {v.vk}"


def key_ident(key):
    """Normalize a pynput key so the same physical key always compares equal.

    Character keys are compared by virtual-key code when available, so that
    'a', 'A' (shift held) and Ctrl+A (control char) all match the same key.
    """
    if isinstance(key, keyboard.Key):
        return ("special", key.name)
    if key.vk is not None:
        return ("vk", key.vk)
    return ("char", (key.char or "").lower())


def normalize_key(key):
    """Turn a captured key into one that is safe to replay with the controller."""
    if isinstance(key, keyboard.Key):
        return key
    if key.char and key.char.isprintable():
        return keyboard.KeyCode(vk=key.vk, char=key.char.lower())
    return keyboard.KeyCode.from_vk(key.vk) if key.vk is not None else key


@dataclass(frozen=True)
class ClickConfig:
    """Immutable snapshot of the settings, read by the worker thread."""

    target: Binding
    delay_min: int
    delay_max: int
    jitter_pct: int  # 0 = disabled
    hold_min: int
    hold_max: int
    hold_enabled: bool


def click_loop(cfg, stop_event, errors):
    """Worker thread: send the target input until stop_event is set."""
    kb = keyboard.Controller()
    ms = mouse.Controller()
    if cfg.target.kind == "mouse":
        press, release = ms.press, ms.release
    else:
        press, release = kb.press, kb.release
    value = cfg.target.value
    lo_d, hi_d = sorted((cfg.delay_min, cfg.delay_max))
    lo_h, hi_h = sorted((cfg.hold_min, cfg.hold_max))

    try:
        while not stop_event.is_set():
            hold = random.uniform(lo_h, hi_h) / 1000.0 if cfg.hold_enabled else 0.0
            press(value)
            try:
                if hold > 0:
                    # Interruptible, but the input is always released.
                    stop_event.wait(hold)
            finally:
                release(value)

            delay_ms = random.uniform(lo_d, hi_d)
            if cfg.jitter_pct:
                spread = delay_ms * cfg.jitter_pct / 100.0
                delay_ms += random.uniform(-spread, spread)
            stop_event.wait(max(1.0, delay_ms) / 1000.0)
    except Exception as exc:  # report to the GUI instead of dying silently
        errors.put(("error", f"Sending input failed: {exc}"))


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.resizable(False, False)
        self._setup_style()

        # State
        self.target = None
        self.toggle_binding = Binding("key", keyboard.Key.f8)
        self.capture_mode = None  # None, "target" or "toggle"
        self.stop_event = None
        self.worker = None
        self.events = queue.Queue()  # listener/worker threads -> GUI thread
        self._toggle_down = False  # suppresses key auto-repeat on the hotkey

        # Tk variables
        self.delay_min = tk.StringVar(value="100")
        self.delay_max = tk.StringVar(value="100")
        self.jitter_enabled = tk.BooleanVar(value=False)
        self.jitter_pct = tk.IntVar(value=10)
        self.hold_enabled = tk.BooleanVar(value=False)
        self.hold_min = tk.StringVar(value="50")
        self.hold_max = tk.StringVar(value="100")

        self._build_ui()
        self._start_listeners()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.after(POLL_MS, self._poll_events)

    # ----- UI construction -------------------------------------------------

    def _setup_style(self):
        bg, panel, font = "#f5f5f5", "#ffffff", ("Segoe UI", 10)
        self.root.configure(bg=bg)
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=bg)
        style.configure("TLabelframe", background=panel)
        style.configure("TLabelframe.Label", background=bg, font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background=panel, font=font)
        style.configure("TButton", font=font, padding=6)
        style.configure("TCheckbutton", background=panel, font=font)
        style.configure("TScale", background=panel)

    def _build_ui(self):
        container = ttk.Frame(self.root, padding=20)
        container.grid()

        s = ttk.Labelframe(container, text="Settings", padding=10)
        s.grid(row=0, column=0, sticky="ew")
        for i in range(4):
            s.columnconfigure(i, weight=1)

        # Target
        ttk.Label(s, text="Target (click/key):").grid(row=0, column=0, sticky="w", pady=5)
        self.target_label = ttk.Label(s, text="None", width=14)
        self.target_label.grid(row=0, column=1, sticky="w", padx=5)
        self.target_btn = ttk.Button(s, text="Set Target",
                                     command=lambda: self.begin_capture("target"))
        self.target_btn.grid(row=0, column=2, columnspan=2, sticky="e")

        # Toggle hotkey
        ttk.Label(s, text="Toggle (start/stop):").grid(row=1, column=0, sticky="w", pady=5)
        self.toggle_label = ttk.Label(s, text=self.toggle_binding.label, width=14)
        self.toggle_label.grid(row=1, column=1, sticky="w", padx=5)
        self.toggle_btn = ttk.Button(s, text="Set Toggle",
                                     command=lambda: self.begin_capture("toggle"))
        self.toggle_btn.grid(row=1, column=2, columnspan=2, sticky="e")

        # Delay
        ttk.Label(s, text="Delay Min (ms):").grid(row=2, column=0, sticky="w", pady=5)
        self.delay_min_spin = ttk.Spinbox(s, from_=DELAY_RANGE[0], to=DELAY_RANGE[1],
                                          textvariable=self.delay_min, width=8)
        self.delay_min_spin.grid(row=2, column=1, sticky="w", padx=5)
        ttk.Label(s, text="Max (ms):").grid(row=2, column=2, sticky="w")
        self.delay_max_spin = ttk.Spinbox(s, from_=DELAY_RANGE[0], to=DELAY_RANGE[1],
                                          textvariable=self.delay_max, width=8)
        self.delay_max_spin.grid(row=2, column=3, sticky="w", padx=5)

        # Jitter
        self.jitter_check = ttk.Checkbutton(s, text="Enable jitter", variable=self.jitter_enabled,
                                            command=self._update_states)
        self.jitter_check.grid(row=3, column=0, sticky="w", pady=5)
        self.jitter_value = ttk.Label(s, width=5)
        self.jitter_value.grid(row=3, column=3, sticky="w", padx=5)
        self.jitter_slider = ttk.Scale(s, from_=0, to=100, orient="horizontal",
                                       command=self._on_jitter_slide)
        self.jitter_slider.set(self.jitter_pct.get())
        self.jitter_slider.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5)

        # Hold time
        self.hold_check = ttk.Checkbutton(s, text="Enable hold time", variable=self.hold_enabled,
                                          command=self._update_states)
        self.hold_check.grid(row=4, column=0, sticky="w", pady=5)
        ttk.Label(s, text="Hold Min (ms):").grid(row=5, column=0, sticky="w", pady=5)
        self.hold_min_spin = ttk.Spinbox(s, from_=HOLD_RANGE[0], to=HOLD_RANGE[1],
                                         textvariable=self.hold_min, width=8)
        self.hold_min_spin.grid(row=5, column=1, sticky="w", padx=5)
        ttk.Label(s, text="Max (ms):").grid(row=5, column=2, sticky="w")
        self.hold_max_spin = ttk.Spinbox(s, from_=HOLD_RANGE[0], to=HOLD_RANGE[1],
                                         textvariable=self.hold_max, width=8)
        self.hold_max_spin.grid(row=5, column=3, sticky="w", padx=5)

        # Control
        c = ttk.Labelframe(container, text="Control", padding=10)
        c.grid(row=1, column=0, pady=(20, 0), sticky="ew")
        for i in range(3):
            c.columnconfigure(i, weight=1)
        self.start_btn = ttk.Button(c, text="Start", command=self.start)
        self.start_btn.grid(row=0, column=0, padx=10)
        self.stop_btn = ttk.Button(c, text="Stop", command=self.stop)
        self.stop_btn.grid(row=0, column=1, padx=10)
        self.status_label = ttk.Label(c, width=30)
        self.status_label.grid(row=0, column=2, padx=10)

        self._on_jitter_slide(self.jitter_slider.get())
        self._update_states()

    @property
    def running(self):
        return self.worker is not None and self.worker.is_alive()

    def _update_states(self):
        """Enable/disable widgets according to the current state."""
        running, capturing = self.running, self.capture_mode is not None
        editable = not running and not capturing

        def set_enabled(widget, enabled):
            widget.state(["!disabled"] if enabled else ["disabled"])

        for w in (self.target_btn, self.toggle_btn, self.delay_min_spin,
                  self.delay_max_spin, self.jitter_check, self.hold_check):
            set_enabled(w, editable)
        set_enabled(self.jitter_slider, editable and self.jitter_enabled.get())
        for w in (self.hold_min_spin, self.hold_max_spin):
            set_enabled(w, editable and self.hold_enabled.get())
        set_enabled(self.start_btn, editable)
        set_enabled(self.stop_btn, running)

        self.target_label.config(
            text="Press input..." if self.capture_mode == "target"
            else (self.target.label if self.target else "None"))
        self.toggle_label.config(
            text="Press input..." if self.capture_mode == "toggle"
            else self.toggle_binding.label)
        if capturing:
            status = "Capturing (Esc cancels)"
        else:
            status = "Running" if running else "Stopped"
        self.status_label.config(text=f"Status: {status}")

    def _on_jitter_slide(self, value):
        self.jitter_pct.set(int(float(value)))
        self.jitter_value.config(text=f"{self.jitter_pct.get()}%")

    # ----- Global input listeners -----------------------------------------
    # pynput calls these on its own threads; they only push to self.events.

    def _start_listeners(self):
        self.kb_listener = keyboard.Listener(on_press=self._on_key_press,
                                             on_release=self._on_key_release)
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.kb_listener.daemon = True
        self.mouse_listener.daemon = True
        self.kb_listener.start()
        self.mouse_listener.start()

    def _on_key_press(self, key, injected=False):
        if injected or key is None:
            return  # ignore our own synthetic input
        if self.capture_mode:
            if key == keyboard.Key.esc:
                self.events.put(("captured", None))
            else:
                self.events.put(("captured", Binding("key", normalize_key(key))))
            return
        if Binding("key", key).ident == self.toggle_binding.ident:
            if not self._toggle_down:
                self._toggle_down = True
                self.events.put(("toggle", None))

    def _on_key_release(self, key, injected=False):
        if not injected and key is not None and \
                Binding("key", key).ident == self.toggle_binding.ident:
            self._toggle_down = False

    def _on_click(self, x, y, button, pressed, injected=False):
        if injected or not pressed or button == mouse.Button.unknown:
            return
        binding = Binding("mouse", button)
        if self.capture_mode:
            self.events.put(("captured", binding))
        elif binding.ident == self.toggle_binding.ident:
            self.events.put(("toggle", None))

    def _poll_events(self):
        """Handle events from other threads on the Tk thread (Tk is not thread-safe)."""
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "toggle":
                    self.toggle()
                elif kind == "captured":
                    self._finish_capture(payload)
                elif kind == "error":
                    self.stop()
                    messagebox.showerror(APP_TITLE, payload)
        except queue.Empty:
            pass
        if self.worker is not None and not self.worker.is_alive():
            self.worker = None
            self._update_states()
        self.root.after(POLL_MS, self._poll_events)

    # ----- Capture ---------------------------------------------------------

    def begin_capture(self, mode):
        # Drop anything already queued so only input made after the click counts.
        while not self.events.empty():
            self.events.get_nowait()
        self.capture_mode = mode
        self._update_states()

    def _finish_capture(self, binding):
        mode, self.capture_mode = self.capture_mode, None
        if mode is None:
            return
        if binding is not None:
            other = self.toggle_binding if mode == "target" else self.target
            if other is not None and other.ident == binding.ident:
                messagebox.showwarning(
                    APP_TITLE, "The target and the toggle hotkey must be different inputs.")
            elif mode == "target":
                self.target = binding
            else:
                if binding.kind == "mouse" and binding.value == mouse.Button.left:
                    messagebox.showwarning(
                        APP_TITLE, "The left mouse button cannot be used as the toggle.")
                else:
                    self.toggle_binding = binding
                    # The key is still held from the capture; ignore it until released.
                    self._toggle_down = binding.kind == "key"
        self._update_states()

    # ----- Start / stop ----------------------------------------------------

    def _read_int(self, var, name, lo, hi):
        try:
            value = int(var.get().strip())
        except ValueError:
            raise ValueError(f"{name} must be a whole number.") from None
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be between {lo} and {hi}.")
        return value

    def _build_config(self):
        hold_on = self.hold_enabled.get()
        return ClickConfig(
            target=self.target,
            delay_min=self._read_int(self.delay_min, "Delay Min", *DELAY_RANGE),
            delay_max=self._read_int(self.delay_max, "Delay Max", *DELAY_RANGE),
            jitter_pct=self.jitter_pct.get() if self.jitter_enabled.get() else 0,
            hold_enabled=hold_on,
            hold_min=self._read_int(self.hold_min, "Hold Min", *HOLD_RANGE) if hold_on else 0,
            hold_max=self._read_int(self.hold_max, "Hold Max", *HOLD_RANGE) if hold_on else 0,
        )

    def start(self):
        if self.running or self.capture_mode:
            return
        if self.target is None:
            messagebox.showwarning(APP_TITLE, "Please set a target before starting.")
            return
        try:
            cfg = self._build_config()
        except ValueError as exc:
            messagebox.showwarning(APP_TITLE, str(exc))
            return
        self.stop_event = threading.Event()
        self.worker = threading.Thread(target=click_loop,
                                       args=(cfg, self.stop_event, self.events),
                                       daemon=True)
        self.worker.start()
        self._update_states()

    def stop(self):
        if self.stop_event is not None:
            self.stop_event.set()
        if self.worker is not None:
            self.worker.join(timeout=1.0)
            self.worker = None
        self._update_states()

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def on_close(self):
        self.stop()
        self.kb_listener.stop()
        self.mouse_listener.stop()
        self.root.destroy()


def enable_dpi_awareness():
    """Render crisply on high-DPI Windows displays instead of being bitmap-scaled."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass


def main():
    enable_dpi_awareness()
    root = tk.Tk()
    AutoClickerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
