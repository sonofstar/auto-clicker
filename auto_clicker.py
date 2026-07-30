"""
Auto Clicker & Macro Recorder
=============================
自动连点器 + 操作录制回放工具

功能：
  1. 自动连点 — 可设间隔、次数、鼠标按键、点击位置
  2. 操作录制 — 录制鼠标点击和键盘按键，支持调速回放、保存/加载

快捷键：
  F6 — 开始/停止自动连点
  F7 — 开始/停止录制
  F8 — 回放录制
  ESC — 紧急停止所有操作

依赖：pip install pynput
运行：python auto_clicker.py
"""

import json
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import dataclass, asdict
from typing import List, Optional

from pynput import mouse, keyboard
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key, KeyCode


# ============================================================
# Data Models
# ============================================================

@dataclass
class RecordedAction:
    """Single recorded action (mouse click or key press)."""
    type: str           # "mouse" or "key"
    action: str         # "press" / "release" / "click"
    button: str = ""    # mouse button name or key name
    x: int = 0          # mouse x position
    y: int = 0          # mouse y position
    delay: float = 0.0  # delay before this action (seconds)


# ============================================================
# Auto Clicker Engine
# ============================================================

class AutoClicker:
    """Background auto-clicking engine."""

    def __init__(self):
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.mouse = MouseController()

    def start(self, interval_ms: int, button: str, count: int,
              use_current_pos: bool, x: int = 0, y: int = 0):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(
            target=self._loop,
            args=(interval_ms, button, count, use_current_pos, x, y),
            daemon=True
        )
        self._thread.start()

    def stop(self):
        self.running = False

    def _loop(self, interval_ms, button_str, count, use_current_pos, x, y):
        btn_map = {
            "左键": Button.left,
            "右键": Button.right,
            "中键": Button.middle,
        }
        btn = btn_map.get(button_str, Button.left)
        interval = interval_ms / 1000.0
        clicked = 0

        while self.running:
            if count > 0 and clicked >= count:
                break
            if not use_current_pos:
                self.mouse.position = (x, y)
            self.mouse.click(btn)
            clicked += 1
            # Sleep in small increments for responsive stop
            slept = 0.0
            while slept < interval and self.running:
                time.sleep(0.01)
                slept += 0.01

        self.running = False


# ============================================================
# Recorder Engine
# ============================================================

class Recorder:
    """Records mouse and keyboard actions with timestamps."""

    def __init__(self):
        self.recording = False
        self.playing = False
        self.actions: List[RecordedAction] = []
        self._last_time: float = 0.0
        self._mouse_listener = None
        self._key_listener = None
        self.mouse = MouseController()
        self.keyboard = KeyboardController()

    def start(self):
        if self.recording:
            return
        self.recording = True
        self.actions.clear()
        self._last_time = time.time()

        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click
        )
        self._key_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._mouse_listener.start()
        self._key_listener.start()

    def stop(self):
        self.recording = False
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None
        if self._key_listener:
            self._key_listener.stop()
            self._key_listener = None

    def _record_delay(self):
        now = time.time()
        delay = now - self._last_time
        self._last_time = now
        return round(delay, 3)

    def _on_mouse_click(self, x, y, button, pressed):
        if not self.recording:
            return
        # Only record press events (not release) to keep it simple
        if pressed:
            self.actions.append(RecordedAction(
                type="mouse",
                action="click",
                button=str(button),
                x=int(x),
                y=int(y),
                delay=self._record_delay()
            ))

    def _on_key_press(self, key):
        if not self.recording:
            return
        self.actions.append(RecordedAction(
            type="key",
            action="press",
            button=self._key_to_str(key),
            delay=self._record_delay()
        ))

    def _on_key_release(self, key):
        if not self.recording:
            return
        self.actions.append(RecordedAction(
            type="key",
            action="release",
            button=self._key_to_str(key),
            delay=self._record_delay()
        ))

    @staticmethod
    def _key_to_str(key) -> str:
        if isinstance(key, KeyCode):
            return key.char if key.char else str(key)
        return str(key)

    def playback(self, speed: float = 1.0, on_done=None):
        if self.playing or not self.actions:
            return
        self.playing = True
        thread = threading.Thread(
            target=self._playback_loop,
            args=(speed, on_done),
            daemon=True
        )
        thread.start()

    def stop_playback(self):
        self.playing = False

    def _playback_loop(self, speed: float, on_done):
        btn_map = {
            "Button.left": Button.left,
            "Button.right": Button.right,
            "Button.middle": Button.middle,
        }

        for action in self.actions:
            if not self.playing:
                break

            delay = action.delay / speed if speed > 0 else 0
            if delay > 0:
                slept = 0.0
                while slept < delay and self.playing:
                    time.sleep(0.005)
                    slept += 0.005

            if not self.playing:
                break

            if action.type == "mouse":
                btn = btn_map.get(action.button, Button.left)
                self.mouse.position = (action.x, action.y)
                self.mouse.click(btn)

            elif action.type == "key":
                key = self._str_to_key(action.button)
                if key is not None:
                    try:
                        if action.action == "press":
                            self.keyboard.press(key)
                        elif action.action == "release":
                            self.keyboard.release(key)
                    except Exception:
                        pass

        self.playing = False
        if on_done:
            on_done()

    @staticmethod
    def _str_to_key(key_str: str):
        """Convert string back to pynput key object."""
        # Handle special keys
        special = {
            "Key.space": Key.space,
            "Key.enter": Key.enter,
            "Key.backspace": Key.backspace,
            "Key.tab": Key.tab,
            "Key.esc": Key.esc,
            "Key.shift": Key.shift,
            "Key.shift_l": Key.shift_l,
            "Key.shift_r": Key.shift_r,
            "Key.ctrl": Key.ctrl,
            "Key.ctrl_l": Key.ctrl_l,
            "Key.ctrl_r": Key.ctrl_r,
            "Key.alt": Key.alt,
            "Key.alt_l": Key.alt_l,
            "Key.alt_r": Key.alt_r,
            "Key.cmd": Key.cmd,
            "Key.caps_lock": Key.caps_lock,
            "Key.delete": Key.delete,
            "Key.up": Key.up,
            "Key.down": Key.down,
            "Key.left": Key.left,
            "Key.right": Key.right,
            "Key.home": Key.home,
            "Key.end": Key.end,
            "Key.page_up": Key.page_up,
            "Key.page_down": Key.page_down,
            "Key.f1": Key.f1, "Key.f2": Key.f2, "Key.f3": Key.f3,
            "Key.f4": Key.f4, "Key.f5": Key.f5, "Key.f6": Key.f6,
            "Key.f7": Key.f7, "Key.f8": Key.f8, "Key.f9": Key.f9,
            "Key.f10": Key.f10, "Key.f11": Key.f11, "Key.f12": Key.f12,
        }
        if key_str in special:
            return special[key_str]
        # Single character key
        if len(key_str) == 1:
            return KeyCode.from_char(key_str)
        return None

    def save_to_file(self, filepath: str):
        data = [asdict(a) for a in self.actions]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.actions = [RecordedAction(**item) for item in data]


# ============================================================
# Main GUI Application
# ============================================================

class App:
    # Color scheme - dark theme
    BG = "#1e1e2e"
    CARD_BG = "#2a2a3c"
    ACCENT = "#7c3aed"
    ACCENT_HOVER = "#6d28d9"
    TEXT = "#e2e2e2"
    TEXT_DIM = "#9999aa"
    SUCCESS = "#22c55e"
    DANGER = "#ef4444"
    BORDER = "#3a3a4e"

    def __init__(self, root):
        self.root = root
        self.clicker = AutoClicker()
        self.recorder = Recorder()

        self._setup_window()
        self._setup_styles()
        self._build_ui()
        self._setup_global_hotkeys()

    def _setup_window(self):
        self.root.title("自动点击器 & 操作录制")
        self.root.geometry("680x560")
        self.root.configure(bg=self.BG)
        self.root.minsize(600, 500)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=self.BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=self.CARD_BG,
                        foreground=self.TEXT_DIM,
                        padding=[20, 10],
                        font=("Microsoft YaHei UI", 11))
        style.map("TNotebook.Tab",
                  background=[("selected", self.ACCENT)],
                  foreground=[("selected", "#ffffff")])

        style.configure("TFrame", background=self.BG)
        style.configure("Card.TFrame", background=self.CARD_BG)

        style.configure("TLabel",
                        background=self.BG,
                        foreground=self.TEXT,
                        font=("Microsoft YaHei UI", 10))
        style.configure("Card.TLabel",
                        background=self.CARD_BG,
                        foreground=self.TEXT,
                        font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel",
                        background=self.BG,
                        foreground=self.TEXT,
                        font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("Dim.TLabel",
                        background=self.BG,
                        foreground=self.TEXT_DIM,
                        font=("Microsoft YaHei UI", 9))
        style.configure("CardDim.TLabel",
                        background=self.CARD_BG,
                        foreground=self.TEXT_DIM,
                        font=("Microsoft YaHei UI", 9))
        style.configure("Status.TLabel",
                        background=self.BG,
                        foreground=self.TEXT_DIM,
                        font=("Microsoft YaHei UI", 10))

        style.configure("TButton",
                        background=self.ACCENT,
                        foreground="#ffffff",
                        borderwidth=0,
                        padding=[16, 8],
                        font=("Microsoft YaHei UI", 10))
        style.map("TButton",
                  background=[("active", self.ACCENT_HOVER)])

        style.configure("Danger.TButton",
                        background=self.DANGER,
                        foreground="#ffffff",
                        borderwidth=0,
                        padding=[16, 8],
                        font=("Microsoft YaHei UI", 10))
        style.map("Danger.TButton",
                  background=[("active", "#dc2626")])

        style.configure("Success.TButton",
                        background=self.SUCCESS,
                        foreground="#ffffff",
                        borderwidth=0,
                        padding=[16, 8],
                        font=("Microsoft YaHei UI", 10))
        style.map("Success.TButton",
                  background=[("active", "#16a34a")])

        style.configure("Secondary.TButton",
                        background=self.BORDER,
                        foreground=self.TEXT,
                        borderwidth=0,
                        padding=[16, 8],
                        font=("Microsoft YaHei UI", 10))
        style.map("Secondary.TButton",
                  background=[("active", "#4a4a5e")])

        style.configure("TSpinbox",
                        fieldbackground=self.CARD_BG,
                        foreground=self.TEXT,
                        background=self.CARD_BG,
                        bordercolor=self.BORDER,
                        lightcolor=self.BORDER,
                        darkcolor=self.BORDER,
                        insertcolor=self.TEXT,
                        font=("Microsoft YaHei UI", 11))
        style.configure("TCombobox",
                        fieldbackground=self.CARD_BG,
                        foreground=self.TEXT,
                        background=self.CARD_BG,
                        bordercolor=self.BORDER,
                        lightcolor=self.BORDER,
                        darkcolor=self.BORDER,
                        arrowcolor=self.TEXT,
                        font=("Microsoft YaHei UI", 11))
        style.map("TCombobox",
                  fieldbackground=[("readonly", self.CARD_BG)],
                  foreground=[("readonly", self.TEXT)])

        style.configure("TCheckbutton",
                        background=self.BG,
                        foreground=self.TEXT,
                        font=("Microsoft YaHei UI", 10))
        style.map("TCheckbutton",
                  background=[("active", self.BG)])

    def _build_ui(self):
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=20, pady=(16, 0))

        ttk.Label(header, text="⚡ 自动点击器 & 操作录制",
                  style="Title.TLabel").pack(side="left")

        self.status_label = ttk.Label(header, text="就绪", style="Status.TLabel")
        self.status_label.pack(side="right")

        # Hotkey hint
        hint = ttk.Frame(self.root)
        hint.pack(fill="x", padx=20, pady=(4, 8))
        ttk.Label(hint,
                  text="快捷键：F6 连点 ｜ F7 录制 ｜ F8 回放 ｜ ESC 紧急停止",
                  style="Dim.TLabel").pack(side="left")

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self._build_clicker_tab()
        self._build_recorder_tab()

    # --------------------------------------------------------
    # Tab 1: Auto Clicker
    # --------------------------------------------------------

    def _build_clicker_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  自动连点  ")

        # --- Card: Settings ---
        card = ttk.Frame(tab, style="Card.TFrame")
        card.pack(fill="x", padx=8, pady=8)

        # Interval
        row1 = ttk.Frame(card, style="Card.TFrame")
        row1.pack(fill="x", padx=16, pady=(16, 8))
        ttk.Label(row1, text="点击间隔（毫秒）", style="Card.TLabel",
                  width=16).pack(side="left")
        self.interval_var = tk.IntVar(value=100)
        ttk.Spinbox(row1, from_=1, to=60000, increment=10,
                    textvariable=self.interval_var, width=12,
                    style="TSpinbox").pack(side="left", padx=(0, 8))
        ttk.Label(row1, text="ms", style="CardDim.TLabel").pack(side="left")

        # Button
        row2 = ttk.Frame(card, style="Card.TFrame")
        row2.pack(fill="x", padx=16, pady=8)
        ttk.Label(row2, text="鼠标按键", style="Card.TLabel",
                  width=16).pack(side="left")
        self.button_var = tk.StringVar(value="左键")
        ttk.Combobox(row2, textvariable=self.button_var, width=10,
                     values=["左键", "右键", "中键"], state="readonly",
                     style="TCombobox").pack(side="left")

        # Count
        row3 = ttk.Frame(card, style="Card.TFrame")
        row3.pack(fill="x", padx=16, pady=8)
        ttk.Label(row3, text="点击次数", style="Card.TLabel",
                  width=16).pack(side="left")
        self.count_var = tk.IntVar(value=0)
        ttk.Spinbox(row3, from_=0, to=999999, increment=1,
                    textvariable=self.count_var, width=12,
                    style="TSpinbox").pack(side="left", padx=(0, 8))
        ttk.Label(row3, text="（0 = 无限）", style="CardDim.TLabel").pack(side="left")

        # Position
        row4 = ttk.Frame(card, style="Card.TFrame")
        row4.pack(fill="x", padx=16, pady=8)
        ttk.Label(row4, text="点击位置", style="Card.TLabel",
                  width=16).pack(side="left")
        self.pos_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(row4, text="跟随鼠标当前位置",
                        variable=self.pos_var,
                        style="TCheckbutton").pack(side="left")

        # Custom position
        row5 = ttk.Frame(card, style="Card.TFrame")
        row5.pack(fill="x", padx=16, pady=(8, 16))
        ttk.Label(row5, text="自定义坐标", style="Card.TLabel",
                  width=16).pack(side="left")
        ttk.Label(row5, text="X:", style="CardDim.TLabel").pack(side="left")
        self.x_var = tk.IntVar(value=0)
        ttk.Spinbox(row5, from_=0, to=99999, increment=1,
                    textvariable=self.x_var, width=8,
                    style="TSpinbox").pack(side="left", padx=(4, 12))
        ttk.Label(row5, text="Y:", style="CardDim.TLabel").pack(side="left")
        self.y_var = tk.IntVar(value=0)
        ttk.Spinbox(row5, from_=0, to=99999, increment=1,
                    textvariable=self.y_var, width=8,
                    style="TSpinbox").pack(side="left", padx=(4, 0))

        # --- Buttons ---
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=8, pady=8)

        self.click_start_btn = ttk.Button(
            btn_frame, text="▶ 开始连点 (F6)", style="Success.TButton",
            command=self.toggle_clicker
        )
        self.click_start_btn.pack(side="left", padx=(0, 8), expand=True, fill="x")

        self.click_stop_btn = ttk.Button(
            btn_frame, text="■ 停止", style="Danger.TButton",
            command=self.stop_clicker, state="disabled"
        )
        self.click_stop_btn.pack(side="left", expand=True, fill="x")

        # --- Info ---
        info_frame = ttk.Frame(tab)
        info_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.click_count_label = ttk.Label(
            info_frame,
            text="已点击：0 次",
            style="Dim.TLabel"
        )
        self.click_count_label.pack(anchor="w", pady=(8, 4))

        ttk.Label(info_frame,
                  text="提示：设置好参数后按 F6 或点击「开始连点」。\n"
                       "点击次数设为 0 表示无限连点，直到手动停止。",
                  style="Dim.TLabel").pack(anchor="w")

    # --------------------------------------------------------
    # Tab 2: Recorder
    # --------------------------------------------------------

    def _build_recorder_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  录制 & 回放  ")

        # --- Card: Recording Controls ---
        card1 = ttk.Frame(tab, style="Card.TFrame")
        card1.pack(fill="x", padx=8, pady=8)

        ttk.Label(card1, text="操作录制", style="Card.TLabel",
                  font=("Microsoft YaHei UI", 12, "bold")).pack(
            anchor="w", padx=16, pady=(12, 8))

        # Record buttons
        rec_btns = ttk.Frame(card1, style="Card.TFrame")
        rec_btns.pack(fill="x", padx=16, pady=(0, 12))

        self.rec_start_btn = ttk.Button(
            rec_btns, text="● 开始录制 (F7)", style="Danger.TButton",
            command=self.toggle_recording
        )
        self.rec_start_btn.pack(side="left", padx=(0, 8), expand=True, fill="x")

        self.rec_stop_btn = ttk.Button(
            rec_btns, text="■ 停止录制", style="Secondary.TButton",
            command=self.stop_recording, state="disabled"
        )
        self.rec_stop_btn.pack(side="left", expand=True, fill="x")

        # --- Card: Playback Controls ---
        card2 = ttk.Frame(tab, style="Card.TFrame")
        card2.pack(fill="x", padx=8, pady=8)

        ttk.Label(card2, text="回放控制", style="Card.TLabel",
                  font=("Microsoft YaHei UI", 12, "bold")).pack(
            anchor="w", padx=16, pady=(12, 8))

        # Speed
        speed_row = ttk.Frame(card2, style="Card.TFrame")
        speed_row.pack(fill="x", padx=16, pady=4)
        ttk.Label(speed_row, text="回放速度", style="Card.TLabel",
                  width=12).pack(side="left")
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_combo = ttk.Combobox(speed_row, textvariable=self.speed_var,
                                   width=10, state="readonly",
                                   values=[0.5, 1.0, 2.0, 4.0, 8.0],
                                   style="TCombobox")
        speed_combo.pack(side="left")
        ttk.Label(speed_row, text="x（数值越大越快）",
                  style="CardDim.TLabel").pack(side="left", padx=(8, 0))

        # Playback buttons
        play_btns = ttk.Frame(card2, style="Card.TFrame")
        play_btns.pack(fill="x", padx=16, pady=(8, 12))

        self.play_btn = ttk.Button(
            play_btns, text="▶ 回放 (F8)", style="Success.TButton",
            command=self.start_playback
        )
        self.play_btn.pack(side="left", padx=(0, 8), expand=True, fill="x")

        self.stop_play_btn = ttk.Button(
            play_btns, text="■ 停止回放", style="Secondary.TButton",
            command=self.stop_playback, state="disabled"
        )
        self.stop_play_btn.pack(side="left", expand=True, fill="x")

        # --- Card: File Operations ---
        card3 = ttk.Frame(tab, style="Card.TFrame")
        card3.pack(fill="x", padx=8, pady=8)

        ttk.Label(card3, text="录制文件", style="Card.TLabel",
                  font=("Microsoft YaHei UI", 12, "bold")).pack(
            anchor="w", padx=16, pady=(12, 8))

        file_btns = ttk.Frame(card3, style="Card.TFrame")
        file_btns.pack(fill="x", padx=16, pady=(0, 12))

        ttk.Button(file_btns, text="💾 保存录制",
                   style="Secondary.TButton",
                   command=self.save_recording).pack(
            side="left", padx=(0, 8), expand=True, fill="x")
        ttk.Button(file_btns, text="📂 加载录制",
                   style="Secondary.TButton",
                   command=self.load_recording).pack(
            side="left", expand=True, fill="x")
        ttk.Button(file_btns, text="🗑 清空",
                   style="Secondary.TButton",
                   command=self.clear_recording).pack(
            side="left", padx=(8, 0), expand=True, fill="x")

        # --- Action list ---
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill="both", expand=True, padx=8, pady=8)

        ttk.Label(list_frame, text="录制详情：", style="Dim.TLabel").pack(
            anchor="w", pady=(0, 4))

        list_container = tk.Frame(list_frame, bg=self.CARD_BG,
                                   highlightbackground=self.BORDER,
                                   highlightthickness=1)
        list_container.pack(fill="both", expand=True)

        self.action_list = tk.Listbox(
            list_container,
            bg=self.CARD_BG,
            fg=self.TEXT,
            selectbackground=self.ACCENT,
            selectforeground="#ffffff",
            borderwidth=0,
            highlightthickness=0,
            font=("Consolas", 9),
            height=8
        )
        self.action_list.pack(fill="both", expand=True, padx=4, pady=4)

        self.rec_count_label = ttk.Label(
            list_frame,
            text="已录制：0 个动作",
            style="Dim.TLabel"
        )
        self.rec_count_label.pack(anchor="w", pady=(4, 0))

    # --------------------------------------------------------
    # Global Hotkeys
    # --------------------------------------------------------

    def _setup_global_hotkeys(self):
        """Set up global hotkeys using pynput."""

        def on_f6():
            self.root.after(0, self.toggle_clicker)

        def on_f7():
            self.root.after(0, self.toggle_recording)

        def on_f8():
            self.root.after(0, self.start_playback)

        def on_esc():
            self.root.after(0, self.emergency_stop)

        self.hotkey_listener = keyboard.GlobalHotKeys({
            "<f6>": on_f6,
            "<f7>": on_f7,
            "<f8>": on_f8,
            "<esc>": on_esc,
        })
        self.hotkey_listener.start()

    # --------------------------------------------------------
    # Auto Clicker Actions
    # --------------------------------------------------------

    def toggle_clicker(self):
        if self.clicker.running:
            self.stop_clicker()
        else:
            self.start_clicker()

    def start_clicker(self):
        interval = self.interval_var.get()
        button = self.button_var.get()
        count = self.count_var.get()
        use_current = self.pos_var.get()
        x = self.x_var.get()
        y = self.y_var.get()

        self.clicker.start(interval, button, count, use_current, x, y)
        self.click_start_btn.config(state="disabled")
        self.click_stop_btn.config(state="normal")
        self._set_status("连点中…", self.SUCCESS)
        self._update_click_count()

    def stop_clicker(self):
        self.clicker.stop()
        self.click_start_btn.config(state="normal")
        self.click_stop_btn.config(state="disabled")
        self._set_status("就绪", self.TEXT_DIM)

    def _update_click_count(self):
        """Poll and update click count display."""
        if not self.clicker.running:
            return
        # We don't track exact count from the engine, show running status
        self.click_count_label.config(text="⚡ 连点运行中…")
        self.root.after(500, self._update_click_count)

    # --------------------------------------------------------
    # Recorder Actions
    # --------------------------------------------------------

    def toggle_recording(self):
        if self.recorder.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.recorder.start()
        self.rec_start_btn.config(state="disabled")
        self.rec_stop_btn.config(state="normal")
        self.play_btn.config(state="disabled")
        self._set_status("录制中…", self.DANGER)
        self._poll_recording()

    def stop_recording(self):
        self.recorder.stop()
        self.rec_start_btn.config(state="normal")
        self.rec_stop_btn.config(state="disabled")
        self.play_btn.config(state="normal")
        self._set_status("就绪", self.TEXT_DIM)
        self._refresh_action_list()

    def _poll_recording(self):
        """Refresh action list while recording."""
        if not self.recorder.recording:
            return
        self._refresh_action_list()
        self.root.after(500, self._poll_recording)

    def _refresh_action_list(self):
        self.action_list.delete(0, tk.END)
        for i, a in enumerate(self.recorder.actions):
            if a.type == "mouse":
                text = f"[{i+1:3d}] 🖱 {a.action:7s} {a.button:12s} ({a.x}, {a.y})  +{a.delay:.3f}s"
            else:
                text = f"[{i+1:3d}] ⌨ {a.action:7s} {a.button:12s}                 +{a.delay:.3f}s"
            self.action_list.insert(tk.END, text)
        self.rec_count_label.config(
            text=f"已录制：{len(self.recorder.actions)} 个动作")

    def start_playback(self):
        if not self.recorder.actions:
            messagebox.showinfo("提示", "没有可回放的录制内容。\n请先录制操作。")
            return
        speed = self.speed_var.get()
        self.recorder.playback(speed, on_done=lambda: self.root.after(
            0, self._on_playback_done))
        self.play_btn.config(state="disabled")
        self.stop_play_btn.config(state="normal")
        self._set_status(f"回放中… ({speed}x)", self.SUCCESS)

    def stop_playback(self):
        self.recorder.stop_playback()
        self._on_playback_done()

    def _on_playback_done(self):
        self.play_btn.config(state="normal")
        self.stop_play_btn.config(state="disabled")
        self._set_status("就绪", self.TEXT_DIM)

    def save_recording(self):
        if not self.recorder.actions:
            messagebox.showinfo("提示", "没有可保存的录制内容。")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 录制文件", "*.json"), ("所有文件", "*.*")],
            title="保存录制文件"
        )
        if filepath:
            try:
                self.recorder.save_to_file(filepath)
                messagebox.showinfo("成功", f"已保存 {len(self.recorder.actions)} 个动作到：\n{filepath}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}")

    def load_recording(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON 录制文件", "*.json"), ("所有文件", "*.*")],
            title="加载录制文件"
        )
        if filepath:
            try:
                self.recorder.load_from_file(filepath)
                self._refresh_action_list()
                messagebox.showinfo("成功", f"已加载 {len(self.recorder.actions)} 个动作")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败：{e}")

    def clear_recording(self):
        if not self.recorder.actions:
            return
        if messagebox.askyesno("确认", "确定清空所有录制内容？"):
            self.recorder.actions.clear()
            self._refresh_action_list()

    # --------------------------------------------------------
    # Emergency Stop
    # --------------------------------------------------------

    def emergency_stop(self):
        """Stop everything immediately."""
        self.clicker.stop()
        self.recorder.stop()
        self.recorder.stop_playback()

        self.click_start_btn.config(state="normal")
        self.click_stop_btn.config(state="disabled")
        self.rec_start_btn.config(state="normal")
        self.rec_stop_btn.config(state="disabled")
        self.play_btn.config(state="normal")
        self.stop_play_btn.config(state="disabled")

        self._set_status("已紧急停止", self.DANGER)
        self._refresh_action_list()

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    def _set_status(self, text, color=None):
        self.status_label.config(text=text)
        if color:
            style = "Status.TLabel"
            self.root.after(0, lambda: self.status_label.configure(
                foreground=color))

    def on_close(self):
        self.emergency_stop()
        self.hotkey_listener.stop()
        self.root.destroy()


# ============================================================
# Entry Point
# ============================================================

def main():
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
