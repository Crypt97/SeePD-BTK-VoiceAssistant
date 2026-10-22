"""
SeeRPG BTK Voice Assistant - Main Application
Runs in the background, listens to global hotkeys during FiveM gameplay,
records speech, analyzes offenses with AI, and outputs via HUD, Clipboard, and TTS.
"""
import sys
import os
import time
import threading
import logging
import pyperclip
from pynput import keyboard

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox
)
from PyQt6.QtGui import QIcon, QAction, QColor, QPixmap, QPainter
from PyQt6.QtCore import QObject, pyqtSignal, Qt

from btk_service import BTKService
from calculator import BTKCalculator
from ai_analyzer import AIAnalyzer
from audio_recorder import AudioRecorder
from tts_service import TTSService
from overlay import InGameOverlay
from settings_dialog import SettingsDialog, load_config, save_config
from text_input_dialog import QuickTextInputDialog
from icons import (
    SVG_TRAY_BADGE, SVG_MIC, SVG_CHECK, SVG_SETTINGS, SVG_REFRESH, SVG_CLOSE,
    SVG_KEYBOARD, get_icon, get_app_icon
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def play_audio_cue(cue: str):
    """Low-latency acoustic feedback on background thread for in-game tactile awareness."""
    def _run():
        try:
            import winsound
            if cue == "start":
                winsound.Beep(880, 50)  # Subtle high chirp
            elif cue == "stop":
                winsound.Beep(650, 50)  # Lower acknowledgment chirp
            elif cue == "success":
                winsound.Beep(880, 40)
                winsound.Beep(1320, 60) # Positive double chirp
            elif cue == "error":
                winsound.Beep(320, 100) # Low subtle error tone
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()

class WorkerSignals(QObject):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    analysis_done = pyqtSignal(dict, str)
    analysis_error = pyqtSignal(str)
    open_text_input = pyqtSignal()
    update_result = pyqtSignal(dict, bool)

class BTKVoiceApp:
    def __init__(self, app: QApplication):
        self.app = app
        self.app.setWindowIcon(get_app_icon())
        self.cfg = load_config()
        self.signals = WorkerSignals()
        self._pending_update_info = None

        # Core Services
        self.btk_service = BTKService()
        self.calculator = BTKCalculator(self.btk_service)
        self.ai_analyzer = AIAnalyzer(
            self.btk_service,
            google_api_key=self.cfg.get("google_api_key", ""),
            model_name=self.cfg.get("model_name", "gemini-2.0-flash-lite")
        )
        self.recorder = AudioRecorder()
        self.tts = TTSService(
            rate=self.cfg.get("tts_rate", 180),
            volume=self.cfg.get("tts_volume", 90) / 100.0
        )
        self.tts.set_enabled(self.cfg.get("enable_tts", True))

        # UI Components
        self.overlay = InGameOverlay()
        self.settings_dlg = None
        self.text_input_dlg = QuickTextInputDialog()
        self.text_input_dlg.submitted.connect(self.process_text_input)
        self.overlay.text_input_clicked.connect(self.open_text_input)

        # State
        self.is_recording = False
        self._hotkey_listener = None
        self._pressed_keys = set()
        self._request_counter = 0
        self._key_down = False
        self._last_toggle_time = 0

        # Connect signals
        self.signals.recording_started.connect(self._on_recording_started)
        self.signals.recording_stopped.connect(self._on_recording_stopped)
        self.signals.analysis_done.connect(self._on_analysis_done)
        self.signals.analysis_error.connect(self._on_analysis_error)
        self.signals.open_text_input.connect(self.open_text_input)
        self.signals.update_result.connect(self._on_update_result)

        self._setup_tray()
        self.tray.messageClicked.connect(self._on_tray_message_clicked)
        self._start_hotkey_listener()

        # Check for updates in background on launch (silent)
        threading.Thread(target=self._check_updates_worker, args=(False,), daemon=True).start()

        # Initial check for API key
        if not self.cfg.get("google_api_key"):
            self.overlay.show_error("Google API kulcs szükséges! Nyisd meg a Beállításokat a tálcán.")

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(self.app)
        self.tray.setIcon(get_app_icon())
        self.tray.setToolTip(f"SeePD BTK Hangasszisztens ({self.cfg.get('hotkey', 'F9').upper()} / {self.cfg.get('text_hotkey', 'F10').upper()})")

        menu = QMenu()

        act_test = QAction(get_icon(SVG_MIC, 16), "Hangfelvétel indítása (Teszt)", menu)
        act_test.triggered.connect(self.toggle_recording)
        menu.addAction(act_test)

        act_text = QAction(get_icon(SVG_KEYBOARD, 16), f"Szöveges bevitel ({self.cfg.get('text_hotkey', 'F10').upper()})", menu)
        act_text.triggered.connect(self.open_text_input)
        menu.addAction(act_text)

        act_hud_test = QAction(get_icon(SVG_CHECK, 16), "HUD teszt megjelenítése", menu)
        act_hud_test.triggered.connect(self._test_hud)
        menu.addAction(act_hud_test)

        menu.addSeparator()

        act_settings = QAction(get_icon(SVG_SETTINGS, 16), "Beállítások...", menu)
        act_settings.triggered.connect(self.open_settings)
        menu.addAction(act_settings)

        act_update = QAction(get_icon(SVG_REFRESH, 16), "Frissítések keresése...", menu)
        act_update.triggered.connect(lambda: self.check_updates(manual=True))
        menu.addAction(act_update)

        act_refresh_btk = QAction(get_icon(SVG_REFRESH, 16), "BTK Adatbázis Frissítése", menu)
        act_refresh_btk.triggered.connect(self._refresh_btk)
        menu.addAction(act_refresh_btk)

        menu.addSeparator()

        act_exit = QAction(get_icon(SVG_CLOSE, 16), "Kilépés", menu)
        act_exit.triggered.connect(self.quit)
        menu.addAction(act_exit)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def _refresh_btk(self):
        self.btk_service.load_data(force_refresh=True)
        self.tray.showMessage("SeePD BTK", f"BTK adatbázis frissítve ({len(self.btk_service.points)} tétel).", QSystemTrayIcon.MessageIcon.Information, 2500)

    def check_updates(self, manual: bool = True):
        threading.Thread(target=self._check_updates_worker, args=(manual,), daemon=True).start()

    def _check_updates_worker(self, manual: bool):
        from updater import check_for_updates_sync
        info = check_for_updates_sync()
        self.signals.update_result.emit(info, manual)

    def _on_update_result(self, info: dict, manual: bool):
        from updater import UpdateDialog
        if not info.get("success", False):
            if manual:
                QMessageBox.warning(None, "Frissítési hiba", f"Nem sikerült kapcsolódni a GitHubhoz:\n{info.get('error', '')}")
            return

        if info.get("update_available"):
            self._pending_update_info = info
            if manual:
                dlg = UpdateDialog(info)
                dlg.exec()
            else:
                self.tray.showMessage(
                    "SeePD BTK Frissítés",
                    f"Új verzió érhető el: {info['latest_version']}!\nKattints ide a letöltéshez és frissítéshez.",
                    QSystemTrayIcon.MessageIcon.Information,
                    10000
                )
        else:
            if manual:
                QMessageBox.information(None, "Naprakész", f"A legfrissebb verziót használod ({info.get('current_version')})!")

    def _on_tray_message_clicked(self):
        if self._pending_update_info:
            from updater import UpdateDialog
            dlg = UpdateDialog(self._pending_update_info)
            dlg.exec()
            self._pending_update_info = None

    def _test_hud(self):
        """Simulates a test offense to preview HUD."""
        sample_calc = self.calculator.calculate([
            {"code": "STFK", "count": 1},
            {"code": "FF", "count": 1}
        ])
        self.overlay.show_result(sample_calc, transcription="Nem állt meg a STOP táblánál és feltartotta a forgalmat.")
        if self.cfg.get("enable_tts", True):
            self.tts.speak(sample_calc["tts_text"])

    def open_settings(self):
        if not self.settings_dlg:
            self.settings_dlg = SettingsDialog(self.btk_service)
            self.settings_dlg.settings_saved.connect(self._apply_settings)
        self.settings_dlg.show()
        self.settings_dlg.raise_()
        self.settings_dlg.activateWindow()

    def _apply_settings(self, new_cfg):
        self.cfg = new_cfg
        self.ai_analyzer.set_api_keys(
            self.cfg.get("google_api_key", ""),
            model_name=self.cfg.get("model_name", "gemini-3.1-flash-lite")
        )
        self.tts.set_enabled(self.cfg.get("enable_tts", True))
        self.tts.set_volume(self.cfg.get("tts_volume", 90) / 100.0)
        self.tray.setToolTip(f"SeePD BTK Hangasszisztens ({self.cfg.get('hotkey', 'F9').upper()} / {self.cfg.get('text_hotkey', 'F10').upper()})")
        # Restart hotkey listener if hotkey changed
        self._start_hotkey_listener()

    def _start_hotkey_listener(self):
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass

        target_key_str = self.cfg.get("hotkey", "f9").lower()
        text_key_str = self.cfg.get("text_hotkey", "f10").lower()
        mode = self.cfg.get("hotkey_mode", "toggle")

        def get_key_name(key):
            try:
                if hasattr(key, 'name'):
                    return key.name.lower()
                if hasattr(key, 'char') and key.char:
                    return key.char.lower()
            except Exception:
                pass
            return ""

        def on_press(key):
            name = get_key_name(key)
            if name == target_key_str:
                if self._key_down:
                    # Ignore Windows auto-repeat while key is held down!
                    return
                self._key_down = True

                now = time.time()
                if now - self._last_toggle_time < 0.35:
                    return  # Debounce rapid key triggers
                self._last_toggle_time = now

                if mode == "toggle":
                    self.toggle_recording()
                elif mode == "hold":
                    if not self.is_recording:
                        self.start_recording()

            elif name == text_key_str:
                self.signals.open_text_input.emit()

        def on_release(key):
            name = get_key_name(key)
            if name == target_key_str:
                self._key_down = False
                if mode == "hold":
                    if self.is_recording:
                        self.stop_and_process()

        self._hotkey_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._hotkey_listener.daemon = True
        self._hotkey_listener.start()
        logger.info(f"Hotkey listener started on key: {target_key_str} (mode: {mode}), text key: {text_key_str}")

    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_and_process()

    def start_recording(self):
        if self.is_recording:
            return
        self.is_recording = True
        self._request_counter += 1  # Invalidate any pending background AI threads
        self.tts.stop()  # Stop any lingering speech output immediately
        if self.cfg.get("enable_audio_cues", True):
            play_audio_cue("start")
        dev_idx = self.cfg.get("audio_device_index")
        self.recorder.start_recording(device_index=dev_idx)
        self.signals.recording_started.emit()

    def stop_and_process(self):
        if not self.is_recording:
            return
        self.is_recording = False
        if self.cfg.get("enable_audio_cues", True):
            play_audio_cue("stop")
        wav_bytes = self.recorder.stop_recording()
        self.signals.recording_stopped.emit()

        req_id = self._request_counter
        # Run AI in background thread so UI/Game never freezes
        threading.Thread(target=self._process_worker, args=(wav_bytes, req_id), daemon=True).start()

    def _process_worker(self, wav_bytes, req_id):
        try:
            if not wav_bytes or len(wav_bytes) < 1000 or wav_bytes == b"SILENCE":
                if req_id == self._request_counter:
                    if self.cfg.get("enable_audio_cues", True):
                        play_audio_cue("error")
                    self.signals.analysis_error.emit("Nem észlelhető beszéd a mikrofonból (túl halk vagy üres).")
                return

            res = self.ai_analyzer.analyze_audio(wav_bytes)
            # If user already started a newer recording, drop this old response!
            if req_id != self._request_counter:
                logger.info(f"Discarding stale analysis response (req_id {req_id} != {self._request_counter})")
                return

            if "error" in res and res["error"]:
                if self.cfg.get("enable_audio_cues", True):
                    play_audio_cue("error")
                self.signals.analysis_error.emit(res["error"])
                return

            transcription = res.get("transcription", "")
            offenses = res.get("offenses", [])
            ease_p = self.cfg.get("ease_percent", 0)

            calc_result = self.calculator.calculate(offenses, ease_percent=ease_p)
            if self.cfg.get("enable_audio_cues", True):
                play_audio_cue("success")
            self.signals.analysis_done.emit(calc_result, transcription)
        except Exception as e:
            if req_id == self._request_counter:
                if self.cfg.get("enable_audio_cues", True):
                    play_audio_cue("error")
                logger.error(f"Error in _process_worker: {e}", exc_info=True)
                self.signals.analysis_error.emit(f"Hiba a feldolgozás során: {e}")

    def open_text_input(self):
        self.text_input_dlg.show_and_focus()

    def process_text_input(self, text: str):
        if not text:
            return
        self._request_counter += 1
        req_id = self._request_counter

        # Show HUD in processing state
        if self.cfg.get("enable_overlay", True):
            self.overlay.set_recording_state(False)
            self.overlay.show()

        threading.Thread(target=self._process_text_worker, args=(text, req_id), daemon=True).start()

    def _process_text_worker(self, text: str, req_id: int):
        try:
            res = self.ai_analyzer.analyze_text_direct(text)
            if req_id != self._request_counter:
                logger.info(f"Discarding stale text response (req_id {req_id} != {self._request_counter})")
                return

            if "error" in res and res["error"]:
                self.signals.analysis_error.emit(res["error"])
                return

            transcription = res.get("transcription", text)
            offenses = res.get("offenses", [])
            ease_p = self.cfg.get("ease_percent", 0)

            calc_result = self.calculator.calculate(offenses, ease_percent=ease_p)
            self.signals.analysis_done.emit(calc_result, transcription)
        except Exception as e:
            if req_id == self._request_counter:
                logger.error(f"Error in _process_text_worker: {e}", exc_info=True)
                self.signals.analysis_error.emit(f"Hiba a szöveg feldolgozása során: {e}")

    def _on_recording_started(self):
        if self.cfg.get("enable_overlay", True):
            self.overlay.set_recording_state(True)

    def _on_recording_stopped(self):
        if self.cfg.get("enable_overlay", True):
            self.overlay.set_recording_state(False)

    def _on_analysis_done(self, calc_result: dict, transcription: str):
        # 1. Overlay HUD
        if self.cfg.get("enable_overlay", True):
            dur = self.cfg.get("overlay_duration_sec", 10)
            self.overlay.show_result(calc_result, transcription=transcription, auto_hide_sec=dur)

        # 2. Clipboard with robust retry loop (prevents sharing violations when game is active)
        if self.cfg.get("enable_clipboard", True):
            copy_text = calc_result.get("copy_text", "")
            if copy_text:
                for attempt in range(3):
                    try:
                        pyperclip.copy(copy_text)
                        logger.info(f"Copied to clipboard: {copy_text}")
                        break
                    except Exception as e:
                        logger.warning(f"Clipboard copy retry {attempt+1}/3: {e}")
                        time.sleep(0.04)

        # 3. TTS Speech
        if self.cfg.get("enable_tts", True):
            tts_text = calc_result.get("tts_text", "")
            if tts_text:
                self.tts.speak(tts_text)

    def _on_analysis_error(self, err_msg: str):
        if self.cfg.get("enable_overlay", True):
            self.overlay.show_error(err_msg)
        if self.cfg.get("enable_tts", True):
            self.tts.speak("Hiba történt a beszédelemzés során.")

    def quit(self):
        if self._hotkey_listener:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
        self.tts.shutdown()
        self.app.quit()

def main():
    if sys.platform == "win32":
        try:
            import ctypes
            myappid = "seepd.btk.assistant.app.1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            # Notify Windows Explorer shell to refresh icon caches
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    assistant = BTKVoiceApp(app)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
