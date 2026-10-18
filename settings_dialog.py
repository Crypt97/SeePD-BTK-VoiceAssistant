"""
SeeRPG Settings Dialog
A modern PyQt6 settings window for configuring Hotkeys, API keys, Audio devices, and Outputs.
"""
import os
import sys
import json
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QSlider, QSpinBox, QTabWidget, QWidget,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from audio_recorder import AudioRecorder

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

DEFAULT_CONFIG = {
    "google_api_key": "",
    "hotkey": "f9",
    "hotkey_mode": "toggle", # "hold" (Push-To-Talk) or "toggle" (Push-To-Toggle)
    "audio_device_index": None,
    "enable_clipboard": True,
    "clipboard_template": "{codes}", # e.g. "{codes}" or "/ticket {id} {fine} {codes}"
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

class SettingsDialog(QDialog):
    settings_saved = pyqtSignal(dict)

    def __init__(self, btk_service, parent=None):
        super().__init__(parent)
        self.btk_service = btk_service
        self.cfg = load_config()
        self.setWindowTitle("SeePD BTK Hangasszisztens - Beállítások")
        self.setFixedSize(540, 580)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        tabs = QTabWidget(self)

        # Tab 1: AI & Beszédfelismerés
        tab_ai = QWidget()
        ai_layout = QVBoxLayout(tab_ai)
        ai_layout.setSpacing(12)

        api_group = QGroupBox("Google Gemini API (Ingyenes)", tab_ai)
        api_layout = QVBoxLayout(api_group)
        api_layout.setSpacing(8)

        lbl_info = QLabel(
            "A Google AI Studio teljesen ingyenes API kulcsot biztosít,\n"
            "amivel közvetlenül elemezhető a magyar mikrofon-hang.",
            api_group
        )
        lbl_info.setStyleSheet("color: #64748b; font-size: 11px;")
        api_layout.addWidget(lbl_info)

        self.input_api_key = QLineEdit(api_group)
        self.input_api_key.setPlaceholderText("Másold be ide a Google AI Studio API kulcsodat (AIzaSy...)")
        self.input_api_key.setText(self.cfg.get("google_api_key", ""))
        self.input_api_key.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        api_layout.addWidget(self.input_api_key)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("AI Modell:", api_group))
        self.combo_model = QComboBox(api_group)
        self.combo_model.setEditable(True)
        self.combo_model.addItem("Gemini 3.1 Flash-Lite (Legújabb)", "gemini-3.1-flash-lite")
        self.combo_model.addItem("Gemini 2.0 Flash-Lite (Villámgyors)", "gemini-2.0-flash-lite")
        self.combo_model.addItem("Gemini 2.5 Flash (Kiegyensúlyozott)", "gemini-2.5-flash")
        self.combo_model.addItem("Gemini 2.0 Flash", "gemini-2.0-flash")
        cur_model = self.cfg.get("model_name", "gemini-3.1-flash-lite")
        found = False
        for i in range(self.combo_model.count()):
            if self.combo_model.itemData(i) == cur_model or self.combo_model.itemText(i) == cur_model:
                self.combo_model.setCurrentIndex(i)
                found = True
                break
        if not found:
            self.combo_model.setCurrentText(cur_model)
        model_row.addWidget(self.combo_model)
        api_layout.addLayout(model_row)

        btn_key_link = QPushButton("Ingyenes API Kulcs kérése (aistudio.google.com)", api_group)
        btn_key_link.setStyleSheet("text-align: left; color: #2563eb; background: none; border: none; font-size: 11px; text-decoration: underline;")
        btn_key_link.clicked.connect(self._open_ai_studio)
        api_layout.addWidget(btn_key_link)

        ai_layout.addWidget(api_group)

        # Tab 2: Gyorsbillentyű & Mikrofon
        tab_input = QWidget()
        input_layout = QVBoxLayout(tab_input)
        input_layout.setSpacing(12)

        hotkey_group = QGroupBox("Gyorsbillentyűk (Hotkey)", tab_input)
        hk_layout = QVBoxLayout(hotkey_group)

        hk_row = QHBoxLayout()
        hk_row.addWidget(QLabel("Hangrögzítés gombja (Voice):", hotkey_group))
        self.combo_hotkey = QComboBox(hotkey_group)
        self.combo_hotkey.addItems(["f9", "f8", "f10", "f11", "f12", "insert", "pause", "page_up", "page_down"])
        current_hk = self.cfg.get("hotkey", "f9").lower()
        idx = self.combo_hotkey.findText(current_hk)
        if idx >= 0:
            self.combo_hotkey.setCurrentIndex(idx)
        else:
            self.combo_hotkey.addItem(current_hk)
            self.combo_hotkey.setCurrentText(current_hk)
        hk_row.addWidget(self.combo_hotkey)
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
        self.combo_text_hotkey = QComboBox(hotkey_group)
        self.combo_text_hotkey.addItems(["f10", "f9", "f8", "f11", "f12", "insert", "pause", "page_up", "page_down"])
        current_text_hk = self.cfg.get("text_hotkey", "f10").lower()
        idx_t = self.combo_text_hotkey.findText(current_text_hk)
        if idx_t >= 0:
            self.combo_text_hotkey.setCurrentIndex(idx_t)
        else:
            self.combo_text_hotkey.addItem(current_text_hk)
            self.combo_text_hotkey.setCurrentText(current_text_hk)
        hk_text_row.addWidget(self.combo_text_hotkey)
        hk_layout.addLayout(hk_text_row)

        input_layout.addWidget(hotkey_group)

        # Mikrofon választó
        mic_group = QGroupBox("Mikrofon", tab_input)
        mic_layout = QVBoxLayout(mic_group)
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

        # Tab 3: Kimenetek (Vágólap, Hang, Overlay)
        tab_output = QWidget()
        out_layout = QVBoxLayout(tab_output)
        out_layout.setSpacing(12)

        # Clipboard
        self.chk_clip = QCheckBox("Automatikus másolás a vágólapra (Ctrl+V)", tab_output)
        self.chk_clip.setChecked(self.cfg.get("enable_clipboard", True))
        out_layout.addWidget(self.chk_clip)

        # TTS
        tts_group = QGroupBox("Hangos visszajelzés (TTS fülhallgatóba)", tab_output)
        tts_l = QVBoxLayout(tts_group)
        self.chk_tts = QCheckBox("Hangos bemondás bekapcsolása", tts_group)
        self.chk_tts.setChecked(self.cfg.get("enable_tts", True))
        tts_l.addWidget(self.chk_tts)

        vol_row = QHBoxLayout()
        vol_row.addWidget(QLabel("Hangerő:", tts_group))
        self.slider_vol = QSlider(Qt.Orientation.Horizontal, tts_group)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(int(self.cfg.get("tts_volume", 90)))
        vol_row.addWidget(self.slider_vol)
        tts_l.addLayout(vol_row)
        out_layout.addWidget(tts_group)

        # HUD Overlay
        overlay_group = QGroupBox("Képernyő Overlay (HUD)", tab_output)
        ov_l = QVBoxLayout(overlay_group)
        self.chk_overlay = QCheckBox("Lebegő HUD ablak megjelenítése a játék felett", overlay_group)
        self.chk_overlay.setChecked(self.cfg.get("enable_overlay", True))
        ov_l.addWidget(self.chk_overlay)

        dur_row = QHBoxLayout()
        dur_row.addWidget(QLabel("Automatikus eltűnés (másodperc):", overlay_group))
        self.spin_dur = QSpinBox(overlay_group)
        self.spin_dur.setRange(3, 60)
        self.spin_dur.setValue(int(self.cfg.get("overlay_duration_sec", 10)))
        dur_row.addWidget(self.spin_dur)
        ov_l.addLayout(dur_row)
        out_layout.addWidget(overlay_group)

        # Tab 4: BTK & Enyhítés
        tab_btk = QWidget()
        btk_l = QVBoxLayout(tab_btk)
        btk_l.setSpacing(12)

        ease_group = QGroupBox("Enyhítés mértéke (Rendfokozat alapján)", tab_btk)
        ease_l = QVBoxLayout(ease_group)
        self.combo_ease = QComboBox(ease_group)
        self.combo_ease.addItem("0% - Nincs enyhítés", 0)
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

        btn_refresh_btk = QPushButton("SeePD BTK adatbázis azonnali újraszinkronizálása", tab_btk)
        btn_refresh_btk.clicked.connect(self._sync_btk)
        btk_l.addWidget(btn_refresh_btk)

        lbl_btk_stat = QLabel(f"Jelenleg tárolt tételek száma: {len(self.btk_service.points)} db", tab_btk)
        lbl_btk_stat.setStyleSheet("color: #64748b; font-size: 11px;")
        btk_l.addWidget(lbl_btk_stat)
        self.lbl_btk_stat = lbl_btk_stat

        btk_l.addStretch()

        tabs.addTab(tab_ai, "AI Kulcs")
        tabs.addTab(tab_input, "Gomb & Mikrofon")
        tabs.addTab(tab_output, "Kimenetek")
        tabs.addTab(tab_btk, "BTK Szabályok")

        layout.addWidget(tabs)

        # Buttons footer
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Mégse", self)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Mentés és Alkalmazás", self)
        btn_save.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 14px; border-radius: 4px;")
        btn_save.clicked.connect(self.save)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

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
        self.cfg["hotkey"] = self.combo_hotkey.currentText().strip().lower()
        self.cfg["hotkey_mode"] = self.combo_hk_mode.currentData()
        self.cfg["text_hotkey"] = self.combo_text_hotkey.currentText().strip().lower()
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
