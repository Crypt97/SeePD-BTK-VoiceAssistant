"""
SeeRPG Settings Dialog
A modern, dark-themed PyQt6 settings window with custom segmented pill navigation,
sleek cards, and flawless border alignment matching FiveM / GTA V HUD aesthetics.
"""
import os
import sys
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QSlider, QSpinBox, QWidget,
    QGroupBox, QMessageBox, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from audio_recorder import AudioRecorder
from icons import get_app_icon, get_app_pixmap
from updater import APP_VERSION

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "google_api_key": "",
    "model_name": "gemini-3.1-flash-lite",
    "hotkey": "f9",
    "hotkey_mode": "toggle", # "hold" (Push-To-Talk) or "toggle" (Push-To-Toggle)
    "text_hotkey": "f10",
    "audio_device_index": None,
    "enable_clipboard": True,
    "clipboard_template": "{codes}",
    "enable_tts": True,
    "tts_volume": 90,
    "tts_rate": 180,
    "enable_overlay": True,
    "overlay_duration_sec": 10,
    "ease_percent": 0
}

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                cfg = DEFAULT_CONFIG.copy()
                cfg.update(saved)
                return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")

class HotkeyRecorderButton(QPushButton):
    hotkey_changed = pyqtSignal(str)

    SPECIAL_KEYS_MAP = {
        int(Qt.Key.Key_Insert): "insert",
        int(Qt.Key.Key_Delete): "delete",
        int(Qt.Key.Key_Home): "home",
        int(Qt.Key.Key_End): "end",
        int(Qt.Key.Key_PageUp): "page_up",
        int(Qt.Key.Key_PageDown): "page_down",
        int(Qt.Key.Key_Pause): "pause",
        int(Qt.Key.Key_Print): "print_screen",
        int(Qt.Key.Key_ScrollLock): "scroll_lock",
        int(Qt.Key.Key_NumLock): "num_lock",
        int(Qt.Key.Key_CapsLock): "caps_lock",
        int(Qt.Key.Key_Tab): "tab",
        int(Qt.Key.Key_Space): "space",
        int(Qt.Key.Key_Backspace): "backspace",
        int(Qt.Key.Key_Return): "enter",
        int(Qt.Key.Key_Enter): "enter",
        int(Qt.Key.Key_Up): "up",
        int(Qt.Key.Key_Down): "down",
        int(Qt.Key.Key_Left): "left",
        int(Qt.Key.Key_Right): "right",
    }

    IGNORE_KEYS = {
        int(Qt.Key.Key_Shift),
        int(Qt.Key.Key_Control),
        int(Qt.Key.Key_Alt),
        int(Qt.Key.Key_Meta),
    }

    def __init__(self, key: str = "f9", parent=None):
        super().__init__(parent)
        self.current_key = (key or "f9").lower()
        self.is_recording = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._toggle_recording)
        self._update_appearance()

    def _toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.cancel_recording()

    def start_recording(self):
        self.is_recording = True
        self.setFocus()
        self._update_appearance()

    def cancel_recording(self):
        self.is_recording = False
        self._update_appearance()

    def get_key(self) -> str:
        return self.current_key

    def set_key(self, key: str):
        self.current_key = (key or "f9").lower()
        self._update_appearance()

    def _display_key(self) -> str:
        return self.current_key.replace("_", " ").upper()

    def _update_appearance(self):
        if self.is_recording:
            self.setText("[  Nyomj le egy gombot...  ]")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #0f172a;
                    color: #38bdf8;
                    border: 2px solid #0284c7;
                    border-radius: 6px;
                    padding: 7px 18px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 170px;
                }
            """)
            self.setToolTip("Nyomj le egy tetszőleges billentyűt a rögzítéshez (ESC: mégse).")
        else:
            self.setText(f"[  {self._display_key()}  ]")
            self.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #f8fafc;
                    border: 1px solid #475569;
                    border-radius: 6px;
                    padding: 7px 18px;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 170px;
                }
                QPushButton:hover {
                    background-color: #334155;
                    border-color: #64748b;
                    color: #38bdf8;
                }
            """)
            self.setToolTip("Kattints ide a gyorsbillentyű módosításához!")

    def focusOutEvent(self, event):
        if self.is_recording:
            self.cancel_recording()
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if not self.is_recording:
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key.Key_Escape:
            self.cancel_recording()
            event.accept()
            return

        mapped_key = self._map_event_to_key(event)
        if mapped_key:
            self.current_key = mapped_key
            self.is_recording = False
            self._update_appearance()
            self.hotkey_changed.emit(self.current_key)
            event.accept()
        else:
            event.ignore()

    def _map_event_to_key(self, event: QKeyEvent) -> str:
        k_val = int(event.key())
        if k_val in self.IGNORE_KEYS:
            return ""

        # Function keys F1..F24
        if int(Qt.Key.Key_F1) <= k_val <= int(Qt.Key.Key_F24):
            return f"f{k_val - int(Qt.Key.Key_F1) + 1}"

        # Special named keys
        if k_val in self.SPECIAL_KEYS_MAP:
            return self.SPECIAL_KEYS_MAP[k_val]

        # A-Z
        if int(Qt.Key.Key_A) <= k_val <= int(Qt.Key.Key_Z):
            return chr(ord('a') + (k_val - int(Qt.Key.Key_A)))

        # 0-9
        if int(Qt.Key.Key_0) <= k_val <= int(Qt.Key.Key_9):
            return chr(ord('0') + (k_val - int(Qt.Key.Key_0)))

        # Fallback to printable text
        text = event.text().strip().lower()
        if text and len(text) == 1:
            return text

        return ""

class SettingsDialog(QDialog):
    settings_saved = pyqtSignal(dict)

    def __init__(self, btk_service, parent=None):
        super().__init__(parent)
        self.btk_service = btk_service
        self.cfg = load_config()
        self.nav_buttons = []
        self.setWindowIcon(get_app_icon())
        self.setWindowTitle("SeePD BTK Asszisztens - Beállítások")
        self.setFixedSize(580, 650)
        self.apply_theme()
        self.init_ui()

    def _create_section_card(self, title: str, parent: QWidget = None):
        card = QFrame(parent)
        card.setObjectName("settingsCard")
        card.setStyleSheet("""
            QFrame#settingsCard {
                background-color: #141824;
                border: none;
                border-radius: 12px;
            }
        """)
        card_l = QVBoxLayout(card)
        card_l.setContentsMargins(18, 16, 18, 16)
        card_l.setSpacing(12)

        title_lbl = QLabel(title, card)
        title_lbl.setStyleSheet("""
            color: #38bdf8;
            font-size: 13px;
            font-weight: bold;
            background: transparent;
            padding-bottom: 2px;
        """)
        card_l.addWidget(title_lbl)
        return card, card_l

    def apply_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0f1117;
                color: #f8fafc;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            QLabel {
                color: #f8fafc;
                font-size: 13px;
                background: transparent;
            }
            QLineEdit {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #38bdf8;
                background-color: #0f172a;
            }
            QComboBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                min-height: 24px;
            }
            QComboBox:focus, QComboBox:hover {
                border: 1px solid #38bdf8;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #f8fafc;
                selection-background-color: #2563eb;
                selection-color: white;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QCheckBox {
                color: #f8fafc;
                font-size: 13px;
                spacing: 8px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #475569;
                background-color: #1e293b;
            }
            QCheckBox::indicator:hover {
                border-color: #38bdf8;
            }
            QCheckBox::indicator:checked {
                background-color: #2563eb;
                border-color: #38bdf8;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #1e293b;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #2563eb;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #38bdf8;
                border: 2px solid #ffffff;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #60a5fa;
            }
            QSpinBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border: 1px solid #38bdf8;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # Header with Logo & Title
        header = QFrame(self)
        header.setStyleSheet("background: transparent; border: none;")
        header_l = QHBoxLayout(header)
        header_l.setContentsMargins(4, 0, 4, 0)
        header_l.setSpacing(12)

        icon_lbl = QLabel(header)
        icon_lbl.setPixmap(get_app_pixmap(36, 36))
        header_l.addWidget(icon_lbl)

        title_l = QVBoxLayout()
        title_l.setSpacing(1)
        title = QLabel("SeePD BTK Hangasszisztens", header)
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #f8fafc;")
        title_l.addWidget(title)

        subtitle = QLabel("Hang- és szöveges szabálysértés-elemző FiveM / SeeRPG járőröknek", header)
        subtitle.setStyleSheet("font-size: 11px; color: #64748b;")
        title_l.addWidget(subtitle)
        header_l.addLayout(title_l)

        header_l.addStretch()

        ver_badge = QLabel(f"v{APP_VERSION}", header)
        ver_badge.setStyleSheet("""
            background-color: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 12px;
        """)
        header_l.addWidget(ver_badge)

        layout.addWidget(header)

        # Modern Segmented Pill Navigation Bar (No lines, no clipping!)
        nav_bar = QFrame(self)
        nav_bar.setObjectName("navBar")
        nav_bar.setStyleSheet("""
            QFrame#navBar {
                background-color: #141824;
                border: none;
                border-radius: 8px;
                padding: 3px;
            }
        """)
        nav_l = QHBoxLayout(nav_bar)
        nav_l.setContentsMargins(3, 3, 3, 3)
        nav_l.setSpacing(4)

        tabs_info = [
            "AI Modell",
            "Gombok & Hang",
            "Kimenetek & HUD",
            "BTK Szabályok"
        ]

        self.nav_buttons = []
        for i, name in enumerate(tabs_info):
            btn = QPushButton(name, nav_bar)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self.switch_tab(idx))
            nav_l.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addWidget(nav_bar)

        # Content Card with QStackedWidget (Seamless, rounded, no overlapping border cuts)
        content_card = QFrame(self)
        content_card.setObjectName("contentCard")
        content_card.setStyleSheet("""
            QFrame#contentCard {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
        """)
        card_layout = QVBoxLayout(content_card)
        card_layout.setContentsMargins(8, 8, 8, 8)

        self.stack = QStackedWidget(content_card)
        card_layout.addWidget(self.stack)

        # Tab 1: AI & Beszédfelismerés
        tab_ai = QWidget()
        ai_layout = QVBoxLayout(tab_ai)
        ai_layout.setContentsMargins(8, 8, 8, 8)
        ai_layout.setSpacing(12)

        api_group, api_layout = self._create_section_card("Google Gemini API (Ingyenes)", tab_ai)

        lbl_info = QLabel(
            "A Google AI Studio teljesen ingyenes API kulcsot biztosít,\n"
            "amivel közvetlenül és azonnal elemezhető a járőri hang/szöveg.",
            api_group
        )
        lbl_info.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        api_layout.addWidget(lbl_info)

        self.input_api_key = QLineEdit(api_group)
        self.input_api_key.setPlaceholderText("Másold be ide a Google AI Studio API kulcsodat (AIzaSy...)")
        self.input_api_key.setText(self.cfg.get("google_api_key", ""))
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        api_layout.addWidget(self.input_api_key)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("AI Modell:", api_group))
        self.combo_model = QComboBox(api_group)
        self.combo_model.setEditable(False)
        self.combo_model.addItem("Gemini 3.1 Flash-Lite (Legújabb)", "gemini-3.1-flash-lite")
        self.combo_model.addItem("Gemini 2.0 Flash-Lite (Villámgyors)", "gemini-2.0-flash-lite")
        self.combo_model.addItem("Gemini 2.5 Flash (Kiegyensúlyozott)", "gemini-2.5-flash")
        self.combo_model.addItem("Gemini 2.0 Flash", "gemini-2.0-flash")
        self.combo_model.addItem("Gemma 4 26B (Google Open Weights)", "gemma-4-26b-a4b-it")
        cur_model = self.cfg.get("model_name", "gemini-3.1-flash-lite")
        found = False
        for i in range(self.combo_model.count()):
            if self.combo_model.itemData(i) == cur_model or self.combo_model.itemText(i) == cur_model:
                self.combo_model.setCurrentIndex(i)
                found = True
                break
        if not found:
            self.combo_model.addItem(cur_model, cur_model)
            self.combo_model.setCurrentIndex(self.combo_model.count() - 1)
        model_row.addWidget(self.combo_model)
        api_layout.addLayout(model_row)

        btn_key_link = QPushButton("Ingyenes API Kulcs kérése (aistudio.google.com) ↗", api_group)
        btn_key_link.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_key_link.setStyleSheet("""
            QPushButton {
                text-align: left;
                color: #38bdf8;
                background: none;
                border: none;
                font-size: 11px;
                font-weight: 500;
                text-decoration: underline;
                padding: 0;
            }
            QPushButton:hover {
                color: #60a5fa;
            }
        """)
        btn_key_link.clicked.connect(self._open_ai_studio)
        api_layout.addWidget(btn_key_link)

        ai_layout.addWidget(api_group)
        ai_layout.addStretch()
        self.stack.addWidget(tab_ai)

        # Tab 2: Gyorsbillentyűk & Bemenet
        tab_input = QWidget()
        input_layout = QVBoxLayout(tab_input)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(12)

        hotkey_group, hk_layout = self._create_section_card("Gyorsbillentyűk (Hotkey)", tab_input)

        hk_row = QHBoxLayout()
        hk_row.addWidget(QLabel("Hangrögzítés gombja (Voice):", hotkey_group))
        self.btn_hotkey = HotkeyRecorderButton(self.cfg.get("hotkey", "f9"), hotkey_group)
        hk_row.addWidget(self.btn_hotkey)
        hk_row.addStretch()
        hk_layout.addLayout(hk_row)

        hk_mode_row = QHBoxLayout()
        hk_mode_row.addWidget(QLabel("Hangrögzítés módja:", hotkey_group))
        self.combo_hk_mode = QComboBox(hotkey_group)
        self.combo_hk_mode.addItem("Egyszer megnyomod: indul / újra megnyomod: leáll (Toggle)", "toggle")
        self.combo_hk_mode.addItem("Nyomva tartás alatt rögzít (Push-To-Talk)", "hold")
        if self.cfg.get("hotkey_mode") == "hold":
            self.combo_hk_mode.setCurrentIndex(1)
        else:
            self.combo_hk_mode.setCurrentIndex(0)
        hk_mode_row.addWidget(self.combo_hk_mode)
        hk_layout.addLayout(hk_mode_row)

        hk_text_row = QHBoxLayout()
        hk_text_row.addWidget(QLabel("Szöveges bevitel gombja (Text):", hotkey_group))
        self.btn_text_hotkey = HotkeyRecorderButton(self.cfg.get("text_hotkey", "f10"), hotkey_group)
        hk_text_row.addWidget(self.btn_text_hotkey)
        hk_text_row.addStretch()
        hk_layout.addLayout(hk_text_row)

        lbl_hint = QLabel("Tipp: Kattints bármelyik gombra, majd nyomd le a kívánt billentyűt a rögzítéshez (ESC: mégse).", hotkey_group)
        lbl_hint.setStyleSheet("color: #64748b; font-size: 11px; margin-top: 4px;")
        hk_layout.addWidget(lbl_hint)

        input_layout.addWidget(hotkey_group)

        # Mikrofon választó
        mic_group, mic_layout = self._create_section_card("Mikrofon Kiválasztása", tab_input)
        self.combo_mics = QComboBox(mic_group)
        self.combo_mics.addItem("Alapértelmezett rendszer mikrofon", None)
        devices = AudioRecorder.get_input_devices()
        sel_idx = self.cfg.get("audio_device_index")
        for dev_id, dev_name in devices:
            self.combo_mics.addItem(f"{dev_name} (ID: {dev_id})", dev_id)
            if sel_idx is not None and sel_idx == dev_id:
                self.combo_mics.setCurrentIndex(self.combo_mics.count() - 1)
        mic_layout.addWidget(self.combo_mics)
        input_layout.addWidget(mic_group)
        input_layout.addStretch()
        self.stack.addWidget(tab_input)

        # Tab 3: Kimenetek (Vágólap, Hang, Overlay)
        tab_output = QWidget()
        out_layout = QVBoxLayout(tab_output)
        out_layout.setContentsMargins(8, 8, 8, 8)
        out_layout.setSpacing(12)

        # Clipboard
        clip_group, clip_l = self._create_section_card("Vágólap (Gyorsmásolás)", tab_output)
        self.chk_clip = QCheckBox("Automatikus másolás a vágólapra (Ctrl+V a játékban)", clip_group)
        self.chk_clip.setChecked(self.cfg.get("enable_clipboard", True))
        clip_l.addWidget(self.chk_clip)
        out_layout.addWidget(clip_group)

        # TTS
        tts_group, tts_l = self._create_section_card("Hangos Visszajelzés (TTS fülhallgatóba)", tab_output)
        self.chk_tts = QCheckBox("Hangos összegzés bemondása fülhallgatóba", tts_group)
        self.chk_tts.setChecked(self.cfg.get("enable_tts", True))
        tts_l.addWidget(self.chk_tts)

        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Hangerő:", tts_group))
        self.slider_vol = QSlider(Qt.Orientation.Horizontal, tts_group)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(int(self.cfg.get("tts_volume", 90)))
        vol_row.addWidget(self.slider_vol)

        self.lbl_vol_val = QLabel(f"{int(self.cfg.get('tts_volume', 90))}%", tts_group)
        self.lbl_vol_val.setFixedWidth(40)
        self.lbl_vol_val.setStyleSheet("color: #38bdf8; font-weight: bold;")
        self.slider_vol.valueChanged.connect(lambda v: self.lbl_vol_val.setText(f"{v}%"))
        vol_row.addWidget(self.lbl_vol_val)
        tts_l.addLayout(vol_row)
        out_layout.addWidget(tts_group)

        # HUD Overlay
        overlay_group, ov_l = self._create_section_card("Képernyő Overlay (In-Game HUD)", tab_output)
        self.chk_overlay = QCheckBox("Lebegő átlátszó HUD megjelenítése a játék felett", overlay_group)
        self.chk_overlay.setChecked(self.cfg.get("enable_overlay", True))
        ov_l.addWidget(self.chk_overlay)

        dur_row = QHBoxLayout()
        dur_row.addWidget(QLabel("Automatikus eltűnés időtartama:", overlay_group))
        self.spin_dur = QSpinBox(overlay_group)
        self.spin_dur.setRange(3, 60)
        self.spin_dur.setSuffix(" mp")
        self.spin_dur.setValue(int(self.cfg.get("overlay_duration_sec", 10)))
        dur_row.addWidget(self.spin_dur)
        dur_row.addStretch()
        ov_l.addLayout(dur_row)
        out_layout.addWidget(overlay_group)
        out_layout.addStretch()
        self.stack.addWidget(tab_output)

        # Tab 4: BTK & Enyhítés
        tab_btk = QWidget()
        btk_l = QVBoxLayout(tab_btk)
        btk_l.setContentsMargins(8, 8, 8, 8)
        btk_l.setSpacing(12)

        ease_group, ease_l = self._create_section_card("Enyhítés Mértéke (Rendfokozat alapján)", tab_btk)
        self.combo_ease = QComboBox(ease_group)
        self.combo_ease.addItem("0% - Nincs enyhítés (Alapértelmezett)", 0)
        self.combo_ease.addItem("10% - Őrmester / Deputy I (max 10%)", 10)
        self.combo_ease.addItem("30% - Zászlós / Sr. Deputy I (max 30%)", 30)
        self.combo_ease.addItem("60% - Hadnagy / Sergeant (max 60%)", 60)
        self.combo_ease.addItem("100% - Őrnagy / Major (max 100%)", 100)
        
        cur_ease = self.cfg.get("ease_percent", 0)
        for i in range(self.combo_ease.count()):
            if self.combo_ease.itemData(i) == cur_ease:
                self.combo_ease.setCurrentIndex(i)
                break
        ease_l.addWidget(self.combo_ease)
        btk_l.addWidget(ease_group)

        sync_group, sync_l = self._create_section_card("Élő SeePD BTK Szinkronizáció", tab_btk)

        btn_refresh_btk = QPushButton("BTK Adatbázis azonnali frissítése (btkapi.seepd.hu)", sync_group)
        btn_refresh_btk.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh_btk.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #38bdf8;
                border: none;
                border-radius: 6px;
                padding: 9px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563eb;
                color: white;
            }
        """)
        btn_refresh_btk.clicked.connect(self._sync_btk)
        sync_l.addWidget(btn_refresh_btk)

        lbl_btk_stat = QLabel(f"Jelenleg tárolt tételek száma: {len(self.btk_service.points)} db", sync_group)
        lbl_btk_stat.setStyleSheet("color: #64748b; font-size: 11px;")
        sync_l.addWidget(lbl_btk_stat)
        self.lbl_btk_stat = lbl_btk_stat
        btk_l.addWidget(sync_group)

        btk_l.addStretch()
        self.stack.addWidget(tab_btk)

        layout.addWidget(content_card)

        # Set default tab to AI (0)
        self.switch_tab(0)

        # Buttons footer
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(4, 4, 4, 0)

        lbl_ver = QLabel(f"v{APP_VERSION}", self)
        lbl_ver.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")
        btn_layout.addWidget(lbl_ver)

        btn_chk_update = QPushButton("Frissítés keresése", self)
        btn_chk_update.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                padding: 6px 14px;
                background-color: #161b26;
                color: #cbd5e1;
                border: none;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #38bdf8;
            }
        """)
        btn_chk_update.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_chk_update.clicked.connect(self._manual_check_update)
        btn_layout.addWidget(btn_chk_update)

        btn_layout.addStretch()

        btn_cancel = QPushButton("Mégse", self)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #161b26;
                color: #cbd5e1;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: white;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Mentés és Alkalmazás", self)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                padding: 8px 22px;
                border-radius: 6px;
                border: none;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_save.clicked.connect(self.save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2563eb;
                        color: #ffffff;
                        font-weight: bold;
                        border-radius: 6px;
                        padding: 7px 16px;
                        border: none;
                        font-size: 12px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #94a3b8;
                        font-weight: 500;
                        border-radius: 6px;
                        padding: 7px 16px;
                        border: none;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #1e293b;
                        color: #f8fafc;
                    }
                """)

    def _manual_check_update(self):
        from updater import check_for_updates_sync, UpdateDialog
        info = check_for_updates_sync()
        if not info.get("success", False):
            QMessageBox.warning(self, "Frissítési hiba", f"Nem sikerült kapcsolódni a GitHubhoz:\n{info.get('error', '')}")
            return
        if info.get("update_available"):
            dlg = UpdateDialog(info, self)
            dlg.exec()
        else:
            QMessageBox.information(self, "Naprakész", f"A legfrissebb verziót használod ({info.get('current_version', f'v{APP_VERSION}')})!")

    def _open_ai_studio(self):
        import webbrowser
        webbrowser.open("https://aistudio.google.com/app/apikey")

    def _sync_btk(self):
        try:
            self.btk_service.load_data(force_refresh=True)
            self.lbl_btk_stat.setText(f"Frissítve! Tárolt tételek száma: {len(self.btk_service.points)} db")
            QMessageBox.information(self, "Siker", "A BTK adatbázis sikeresen frissítve lett a btkapi.seepd.hu-ról!")
        except Exception as e:
            QMessageBox.warning(self, "Hiba", f"Nem sikerült a frissítés: {e}")

    def save(self):
        self.cfg["google_api_key"] = self.input_api_key.text().strip()
        sel_model = self.combo_model.currentData()
        self.cfg["model_name"] = sel_model if sel_model else self.combo_model.currentText().strip()
        self.cfg["hotkey"] = self.btn_hotkey.get_key()
        self.cfg["hotkey_mode"] = self.combo_hk_mode.currentData()
        self.cfg["text_hotkey"] = self.btn_text_hotkey.get_key()
        self.cfg["audio_device_index"] = self.combo_mics.currentData()
        self.cfg["enable_clipboard"] = self.chk_clip.isChecked()
        self.cfg["enable_tts"] = self.chk_tts.isChecked()
        self.cfg["tts_volume"] = self.slider_vol.value()
        self.cfg["enable_overlay"] = self.chk_overlay.isChecked()
        self.cfg["overlay_duration_sec"] = self.spin_dur.value()
        self.cfg["ease_percent"] = self.combo_ease.currentData()

        save_config(self.cfg)
        self.settings_saved.emit(self.cfg)
        self.accept()
