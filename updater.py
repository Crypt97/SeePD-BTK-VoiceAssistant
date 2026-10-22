"""
SeePD BTK Assistant - Auto-Updater Module
Checks GitHub Releases for new versions, downloads updates with a progress bar,
and seamlessly restarts the application using a self-replacing Windows updater script.
"""
import os
import sys
import json
import logging
import subprocess
import tempfile
import urllib.request
from typing import Optional, Dict, Any, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from icons import get_app_icon, get_app_pixmap

logger = logging.getLogger(__name__)

APP_VERSION = "1.0.18"
GITHUB_REPO = "Crypt97/SeePD-BTK-VoiceAssistant"
GITHUB_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

def parse_version(v_str: str) -> Tuple[int, ...]:
    """Converts 'v1.0.5' or '1.0.5' into a comparable tuple (1, 0, 5)."""
    clean = v_str.strip().lower().lstrip("v")
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)

def check_for_updates_sync() -> Dict[str, Any]:
    """
    Synchronously queries GitHub Releases API for the latest release.
    Returns dict with update status and metadata.
    """
    req = urllib.request.Request(
        GITHUB_RELEASES_URL,
        headers={"User-Agent": "SeePD-BTK-Assistant-Updater"}
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                remote_ver = parse_version(tag_name)
                local_ver = parse_version(APP_VERSION)

                setup_url = None
                setup_size = 0
                exe_url = None
                exe_size = 0
                for asset in data.get("assets", []):
                    name = asset.get("name", "")
                    if name == "SeePDBTKAssistant-Setup.exe":
                        setup_url = asset.get("browser_download_url")
                        setup_size = asset.get("size", 0)
                    elif name == "SeePDBTKAssistant.exe":
                        exe_url = asset.get("browser_download_url")
                        exe_size = asset.get("size", 0)

                # Prefer official installer if available
                is_setup = setup_url is not None
                chosen_url = setup_url if is_setup else exe_url
                chosen_size = setup_size if is_setup else exe_size

                update_available = remote_ver > local_ver and chosen_url is not None

                return {
                    "success": True,
                    "update_available": update_available,
                    "latest_version": tag_name,
                    "current_version": f"v{APP_VERSION}",
                    "download_url": chosen_url,
                    "size_bytes": chosen_size,
                    "is_setup": is_setup,
                    "release_notes": data.get("body", ""),
                    "release_url": data.get("html_url", "")
                }
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return {
            "success": False,
            "error": str(e),
            "update_available": False,
            "current_version": f"v{APP_VERSION}"
        }

class DownloadWorker(QThread):
    progress = pyqtSignal(int, int) # (downloaded_bytes, total_bytes)
    finished_download = pyqtSignal(str) # downloaded file path
    error = pyqtSignal(str)

    def __init__(self, download_url: str, dest_path: str):
        super().__init__()
        self.download_url = download_url
        self.dest_path = dest_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": "SeePD-BTK-Assistant-Updater"}
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                total_size = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024 # 64 KB

                with open(self.dest_path, "wb") as f:
                    while True:
                        if self._is_cancelled:
                            break
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total_size)

            if self._is_cancelled:
                if os.path.exists(self.dest_path):
                    try:
                        os.remove(self.dest_path)
                    except Exception:
                        pass
                return

            self.finished_download.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))

class UpdateDialog(QDialog):
    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.download_worker: Optional[DownloadWorker] = None
        self.temp_exe_path: Optional[str] = None

        self.setWindowTitle("SeePD BTK Asszisztens - Frissítés")
        self.setWindowIcon(get_app_icon())
        self.setFixedSize(480, 360)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f1117;
                color: #f8fafc;
            }
            QLabel {
                color: #f8fafc;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3b82f6;
            }
            QPushButton#btnCancel {
                background-color: #334155;
                color: #cbd5e1;
            }
            QPushButton#btnCancel:hover {
                background-color: #475569;
            }
            QProgressBar {
                background-color: #1e293b;
                border-radius: 6px;
                text-align: center;
                color: white;
                font-weight: bold;
                height: 20px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 6px;
            }
            QTextEdit {
                background-color: #161b26;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 6px;
                font-size: 12px;
                padding: 6px;
            }
        """)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header with Logo & Version
        header = QHBoxLayout()
        header.setSpacing(12)

        icon_label = QLabel(self)
        icon_label.setPixmap(get_app_pixmap(40, 40))
        header.addWidget(icon_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel(f"Új verzió elérhető: {self.update_info['latest_version']}", self)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        title_box.addWidget(title)

        cur_lbl = QLabel(f"Jelenlegi verziód: {self.update_info['current_version']}", self)
        cur_lbl.setStyleSheet("font-size: 12px; color: #64748b;")
        title_box.addWidget(cur_lbl)

        header.addLayout(title_box)
        header.addStretch()
        layout.addLayout(header)

        # Release Notes / Description
        notes = self.update_info.get("release_notes", "").strip()
        if not notes:
            notes = "Hibajavítások és teljesítmény-optimalizációk."

        layout.addWidget(QLabel("Újdonságok a frissítésben:"))
        self.text_notes = QTextEdit(self)
        self.text_notes.setReadOnly(True)
        self.text_notes.setText(notes)
        layout.addWidget(self.text_notes)

        # Progress bar (Hidden until download starts)
        self.prog_bar = QProgressBar(self)
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setValue(0)
        self.prog_bar.hide()
        layout.addWidget(self.prog_bar)

        self.lbl_status = QLabel("", self)
        self.lbl_status.setStyleSheet("font-size: 11px; color: #94a3b8;")
        self.lbl_status.hide()
        layout.addWidget(self.lbl_status)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Később", self)
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_action = QPushButton("Frissítés most", self)
        self.btn_action.clicked.connect(self.start_download)
        btn_layout.addWidget(self.btn_action)

        layout.addLayout(btn_layout)

    def start_download(self):
        # If in source code mode (not frozen .exe), offer to open release page
        if not getattr(sys, 'frozen', False):
            import webbrowser
            webbrowser.open(self.update_info.get("release_url", GITHUB_RELEASES_URL))
            self.accept()
            return

        self.btn_action.setEnabled(False)
        self.btn_cancel.setText("Mégse")
        self.prog_bar.show()
        self.lbl_status.show()
        self.lbl_status.setText("Letöltés előkészítése...")

        # Determine destination path
        if self.update_info.get("is_setup"):
            temp_dir = tempfile.gettempdir()
            self.temp_exe_path = os.path.join(temp_dir, f"SeePDBTKAssistant-Setup-{self.update_info.get('latest_version')}.exe")
        else:
            current_exe = sys.executable
            exe_dir = os.path.dirname(current_exe)
            self.temp_exe_path = os.path.join(exe_dir, "SeePDBTKAssistant.update.tmp")

        self.download_worker = DownloadWorker(self.update_info["download_url"], self.temp_exe_path)
        self.download_worker.progress.connect(self._on_progress)
        self.download_worker.finished_download.connect(self._on_download_finished)
        self.download_worker.error.connect(self._on_download_error)
        self.download_worker.start()

    def _on_progress(self, downloaded: int, total: int):
        if total > 0:
            pct = int((downloaded / total) * 100)
            self.prog_bar.setValue(pct)
            mb_down = downloaded / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            self.lbl_status.setText(f"Letöltve: {mb_down:.1f} MB / {mb_tot:.1f} MB ({pct}%)")
        else:
            mb_down = downloaded / (1024 * 1024)
            self.lbl_status.setText(f"Letöltve: {mb_down:.1f} MB...")

    def _on_download_finished(self, temp_path: str):
        self.lbl_status.setText("Letöltés kész! A program újraindul...")
        self.prog_bar.setValue(100)
        self.apply_update_and_restart(temp_path)

    def _on_download_error(self, err_msg: str):
        QMessageBox.critical(self, "Frissítési hiba", f"Nem sikerült letölteni a frissítést:\n{err_msg}")
        self.btn_action.setEnabled(True)
        self.btn_cancel.setText("Bezárás")
        self.lbl_status.setText("A letöltés megszakadt.")

    def closeEvent(self, event):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.cancel()
            self.download_worker.wait(1500)
        super().closeEvent(event)

    def apply_update_and_restart(self, new_exe_temp: str):
        clean_env = os.environ.copy()
        clean_env.pop("_MEIPASS2", None)
        clean_env.pop("_MEIPASS", None)

        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

        # If downloaded asset is the Inno Setup installer, run silent background upgrade!
        if self.update_info.get("is_setup"):
            subprocess.Popen(
                [new_exe_temp, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/FORCECLOSEAPPLICATIONS"],
                env=clean_env,
                creationflags=creation_flags
            )
            try:
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    app.quit()
            except Exception:
                pass
            os._exit(0)

        # Fallback for standalone/portable .exe replacement
        current_exe = os.path.abspath(sys.executable)
        current_pid = os.getpid()
        exe_dir = os.path.dirname(current_exe)

        curr_escaped = current_exe.replace("'", "''")
        temp_escaped = new_exe_temp.replace("'", "''")
        dir_escaped = exe_dir.replace("'", "''")

        # Robust PowerShell script that:
        # 1. Force terminates the parent process to immediately release file locks
        # 2. Replaces exe with retry loop
        # 3. Purges _MEIPASS environment variables to prevent Python DLL load error
        # 4. Launches updated exe cleanly and detaches
        ps1_content = f"""# SeePD BTK Assistant - Updater Script
$ErrorActionPreference = 'SilentlyContinue'
$TargetPid = {current_pid}
$CurrentExe = '{curr_escaped}'
$NewExeTemp = '{temp_escaped}'
$ExeDir = '{dir_escaped}'

# 1. Force terminate target process if still alive
try {{
    Stop-Process -Id $TargetPid -Force -ErrorAction SilentlyContinue
}} catch {{}}

# Wait 2 seconds for OS file handles to be completely released
Start-Sleep -Seconds 2

# 2. Retry loop for file replacement
$replaced = $false
for ($i = 0; $i -lt 20; $i++) {{
    try {{
        if (Test-Path -LiteralPath $CurrentExe) {{
            Remove-Item -LiteralPath $CurrentExe -Force -ErrorAction Stop
        }}
        Move-Item -LiteralPath $NewExeTemp -Destination $CurrentExe -Force -ErrorAction Stop
        $replaced = $true
        break
    }} catch {{
        Start-Sleep -Seconds 1
    }}
}}

# 3. Strip PyInstaller environment variables completely
Remove-Item Env:\\_MEIPASS2 -ErrorAction SilentlyContinue
Remove-Item Env:\\_MEIPASS -ErrorAction SilentlyContinue
[System.Environment]::SetEnvironmentVariable('_MEIPASS2', $null, 'Process')
[System.Environment]::SetEnvironmentVariable('_MEIPASS', $null, 'Process')

# 4. Launch the updated application detached
if ($replaced -and (Test-Path -LiteralPath $CurrentExe)) {{
    Start-Process -FilePath $CurrentExe -WorkingDirectory $ExeDir
}}

# 5. Clean up this script
Start-Sleep -Seconds 1
Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
"""
        ps1_path = os.path.join(tempfile.gettempdir(), f"seepd_updater_{current_pid}.ps1")
        with open(ps1_path, "w", encoding="utf-8") as f:
            f.write(ps1_content)

        clean_env = os.environ.copy()
        clean_env.pop("_MEIPASS2", None)
        clean_env.pop("_MEIPASS", None)

        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

        # Launch PowerShell script hidden and detached from current process tree
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", ps1_path],
            env=clean_env,
            creationflags=creation_flags
        )

        # Force terminate process immediately at Win32 OS level so no threads block shutdown
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.quit()
        except Exception:
            pass
        os._exit(0)
