"""
SeeRPG In-Game HUD Overlay
A sleek, transparent, borderless always-on-top PyQt6 HUD overlay designed for FiveM / GTA V.
Uses crisp vector SVG icons from allsvgicons.com instead of emojis.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor

from icons import (
    SVG_POLICE_BADGE, SVG_MIC, SVG_SPINNER, SVG_CHECK, SVG_CLIPBOARD, SVG_ALERT,
    SVG_KEYBOARD, get_pixmap, get_icon, get_app_pixmap, get_app_icon
)

def format_huf(val: int) -> str:
    return f"{val:,}".replace(",", " ")

class InGameOverlay(QWidget):
    close_signal = pyqtSignal()
    text_input_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self.hide_overlay)

        self.init_ui()
        self.position_top_right()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Card container with smooth dark background - COMPLETELY BORDERLESS
        self.card = QFrame(self)
        self.card.setObjectName("mainCard")
        self.card.setStyleSheet("""
            QFrame#mainCard {
                background-color: rgba(15, 17, 23, 0.94);
                border: none;
                border-radius: 14px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

        # Drop shadow for depth without needing borders
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 210))
        shadow.setOffset(0, 5)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)

        # Header: App Badge + Status
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Badge container (SVG Police Badge + Text)
        badge_frame = QFrame(self.card)
        badge_frame.setObjectName("badgeFrame")
        badge_frame.setFixedHeight(26)
        badge_frame.setStyleSheet("""
            QFrame#badgeFrame {
                background-color: rgba(56, 189, 248, 0.15);
                border: none;
                border-radius: 6px;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        badge_layout = QHBoxLayout(badge_frame)
        badge_layout.setContentsMargins(8, 0, 8, 0)
        badge_layout.setSpacing(6)
        badge_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.badge_icon = QLabel(badge_frame)
        self.badge_icon.setStyleSheet("background: transparent; border: none;")
        self.badge_icon.setPixmap(get_app_pixmap(16, 16))
        self.badge_icon.setFixedHeight(16)
        badge_layout.addWidget(self.badge_icon)

        self.badge_label = QLabel("SeePD BTK", badge_frame)
        self.badge_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
            font-weight: bold;
            color: #38bdf8;
            background: transparent;
            border: none;
        """)
        badge_layout.addWidget(self.badge_label)
        header_layout.addWidget(badge_frame, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Status row (SVG Icon + Status text)
        status_frame = QFrame(self.card)
        status_frame.setObjectName("statusFrame")
        status_frame.setFixedHeight(26)
        status_frame.setStyleSheet("""
            QFrame#statusFrame {
                background: transparent;
                border: none;
            }
            QLabel {
                background: transparent;
                border: none;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.status_icon = QLabel(status_frame)
        self.status_icon.setStyleSheet("background: transparent; border: none;")
        self.status_icon.hide()
        status_layout.addWidget(self.status_icon)

        self.status_label = QLabel("Készenlétben", status_frame)
        self.status_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 12px;
            color: #94a3b8;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        status_layout.addWidget(self.status_label)
        header_layout.addWidget(status_frame, alignment=Qt.AlignmentFlag.AlignVCenter)
        header_layout.addStretch()

        # Keyboard button for typing offenses directly
        self.btn_open_text = QPushButton(self.card)
        self.btn_open_text.setIcon(get_icon(SVG_KEYBOARD, 14))
        self.btn_open_text.setFixedSize(24, 24)
        self.btn_open_text.setToolTip("Szöveges szabálysértés beírása (F10)")
        self.btn_open_text.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_text.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.06);
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(56, 189, 248, 0.25);
            }
        """)
        self.btn_open_text.clicked.connect(self.text_input_clicked.emit)
        header_layout.addWidget(self.btn_open_text, alignment=Qt.AlignmentFlag.AlignVCenter)

        card_layout.addLayout(header_layout)

        # Recognized transcription label
        self.transcript_label = QLabel("", self.card)
        self.transcript_label.setWordWrap(True)
        self.transcript_label.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
            font-style: italic;
            color: #94a3b8;
            border: none;
            padding: 2px 0px;
        """)
        self.transcript_label.hide()
        card_layout.addWidget(self.transcript_label)

        # Offenses container - clean text, no boxes or borders
        self.offenses_container = QVBoxLayout()
        self.offenses_container.setSpacing(5)
        card_layout.addLayout(self.offenses_container)

        # Dynamic 2-Tier Stats Container (Spacious, modern, never clipped)
        self.stats_container = QVBoxLayout()
        self.stats_container.setSpacing(8)

        # Row 1: Primary Metrics (Fine & Jail)
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(10)

        # Fine Hero Box
        self.fine_card = QFrame(self.card)
        self.fine_card.setStyleSheet("background-color: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.22); border-radius: 10px;")
        fine_l = QVBoxLayout(self.fine_card)
        fine_l.setContentsMargins(14, 10, 14, 10)
        fine_l.setSpacing(3)
        self.fine_title = QLabel("BÍRSÁG ÖSSZESEN", self.fine_card)
        self.fine_title.setStyleSheet("color: #10b981; font-size: 10px; font-weight: bold; border: none; background: transparent; letter-spacing: 0.5px;")
        self.fine_val = QLabel("0 Ft", self.fine_card)
        self.fine_val.setStyleSheet("color: #34d399; font-size: 16px; font-weight: bold; border: none; background: transparent;")
        fine_l.addWidget(self.fine_title)
        fine_l.addWidget(self.fine_val)
        metrics_row.addWidget(self.fine_card)

        # Jail Hero Box
        self.jail_card = QFrame(self.card)
        self.jail_card.setStyleSheet("background-color: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.22); border-radius: 10px;")
        jail_l = QVBoxLayout(self.jail_card)
        jail_l.setContentsMargins(14, 10, 14, 10)
        jail_l.setSpacing(3)
        self.jail_title = QLabel("SZABADSÁGVESZTÉS", self.jail_card)
        self.jail_title.setStyleSheet("color: #f59e0b; font-size: 10px; font-weight: bold; border: none; background: transparent; letter-spacing: 0.5px;")
        self.jail_val = QLabel("0 perc", self.jail_card)
        self.jail_val.setStyleSheet("color: #fbbf24; font-size: 16px; font-weight: bold; border: none; background: transparent;")
        jail_l.addWidget(self.jail_title)
        jail_l.addWidget(self.jail_val)
        metrics_row.addWidget(self.jail_card)

        self.stats_container.addLayout(metrics_row)

        # Row 2: Secondary Status Badges (Óvadék & Jogosítvány)
        badges_row = QHBoxLayout()
        badges_row.setSpacing(10)

        # Bail Badge
        self.bail_card = QFrame(self.card)
        self.bail_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;")
        bail_l = QHBoxLayout(self.bail_card)
        bail_l.setContentsMargins(10, 8, 10, 8)
        self.bail_val = QLabel("⚖️ Óvadék: -", self.bail_card)
        self.bail_val.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        bail_l.addWidget(self.bail_val, alignment=Qt.AlignmentFlag.AlignCenter)
        badges_row.addWidget(self.bail_card)

        # License Badge
        self.docs_card = QFrame(self.card)
        self.docs_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;")
        docs_l = QHBoxLayout(self.docs_card)
        docs_l.setContentsMargins(10, 8, 10, 8)
        self.docs_val = QLabel("🪪 Jogsi: Érintetlen", self.docs_card)
        self.docs_val.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: bold; border: none; background: transparent;")
        docs_l.addWidget(self.docs_val, alignment=Qt.AlignmentFlag.AlignCenter)
        badges_row.addWidget(self.docs_card)

        self.stats_container.addLayout(badges_row)

        card_layout.addLayout(self.stats_container)

        # Clipboard footer notice (SVG icon + text)
        clip_frame = QFrame(self.card)
        clip_layout = QHBoxLayout(clip_frame)
        clip_layout.setContentsMargins(0, 4, 0, 0)
        clip_layout.setSpacing(6)
        clip_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.clipboard_icon = QLabel(clip_frame)
        self.clipboard_icon.setPixmap(get_pixmap(SVG_CLIPBOARD, 14, 14))
        clip_layout.addWidget(self.clipboard_icon)

        self.clipboard_notice = QLabel("Vágólapra másolva (Ctrl+V)", clip_frame)
        self.clipboard_notice.setStyleSheet("""
            font-size: 11px;
            color: #38bdf8;
            font-weight: 500;
            border: none;
        """)
        clip_layout.addWidget(self.clipboard_notice)

        self.clip_container = clip_frame
        self.clip_container.hide()
        card_layout.addWidget(self.clip_container)

        main_layout.addWidget(self.card)
        self.setFixedWidth(440)

    def position_top_right(self):
        screen = self.screen().geometry()
        margin = 25
        self.move(screen.width() - self.width() - margin, margin + 40)

    def set_recording_state(self, is_recording: bool):
        if is_recording:
            self._auto_hide_timer.stop()
            self.status_icon.setPixmap(get_pixmap(SVG_MIC, 14, 14))
            self.status_icon.show()
            self.status_label.setText("Beszéd rögzítése...")
            self.status_label.setStyleSheet("font-size: 12px; color: #ef4444; font-weight: bold; border: none; background: transparent;")
            self.transcript_label.setText("")
            self.transcript_label.hide()
            self._clear_offenses()
            self.fine_val.setText("0 Ft")
            self.jail_val.setText("0 perc")
            self.bail_val.setText("⚖️ Óvadék: -")
            self.bail_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;")
            self.bail_val.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            self.docs_val.setText("🪪 Jogsi: Érintetlen")
            self.docs_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;")
            self.docs_val.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            self.clip_container.hide()
            self._fit_to_content()
            self.show()
        else:
            self.status_icon.setPixmap(get_pixmap(SVG_SPINNER, 14, 14))
            self.status_icon.show()
            self.status_label.setText("AI feldolgozás...")
            self.status_label.setStyleSheet("font-size: 12px; color: #f59e0b; font-weight: bold; border: none; background: transparent;")
            self._fit_to_content()

    def _fit_to_content(self):
        """Forces card and overlay window to shrink-wrap tightly around current content without gaps."""
        self.card.adjustSize()
        self.adjustSize()

    def show_result(self, calculation_data: dict, transcription: str = "", auto_hide_sec: int = 10):
        self.status_icon.setPixmap(get_pixmap(SVG_CHECK, 14, 14))
        self.status_icon.show()
        self.status_label.setText("Kész")
        self.status_label.setStyleSheet("font-size: 12px; color: #10b981; font-weight: bold; border: none;")

        if transcription:
            self.transcript_label.setText(f'„{transcription}”')
            self.transcript_label.show()
        else:
            self.transcript_label.hide()

        # Fill offenses - clean modern bullet points without borders or boxes
        self._clear_offenses()
        items = calculation_data.get("items", [])
        if not items:
            lbl = QLabel("Nem történt szabálysértés", self.card)
            lbl.setStyleSheet("font-size: 12px; color: #94a3b8; padding: 4px 0px; border: none;")
            self.offenses_container.addWidget(lbl)
        else:
            for it in items:
                point = it.get("point", {})
                code = point.get("pNumber", "")
                name = point.get("fullName", point.get("name", ""))
                count = it.get("count", 1)
                
                row = QLabel(f"• <font color='#38bdf8'><b>[{code}]</b></font> {name}" + (f" (x{count})" if count > 1 else ""), self.card)
                row.setStyleSheet("font-size: 13px; color: #f8fafc; padding: 2px 0px; border: none; background: transparent;")
                row.setWordWrap(True)
                self.offenses_container.addWidget(row)

        # Update stats
        f_min = calculation_data.get("fine_min", 0)
        f_max = calculation_data.get("fine_max", 0)
        if f_min == f_max:
            self.fine_val.setText(f"{format_huf(f_min)} Ft")
        else:
            self.fine_val.setText(f"{format_huf(f_min)} - {format_huf(f_max)} Ft")

        j_min = calculation_data.get("jail_min", 0)
        j_max = calculation_data.get("jail_max", 0)
        if j_min == j_max:
            self.jail_val.setText(f"{j_min} perc" if j_min > 0 else "0 perc")
        else:
            self.jail_val.setText(f"{j_min} - {j_max} perc")

        # Bail status (Óvadék)
        bail = calculation_data.get("bail_status", "-")
        if bail in ("Jár", "Van"):
            self.bail_val.setText("⚖️ Óvadék: Jár")
            self.bail_val.setStyleSheet("color: #34d399; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            self.bail_card.setStyleSheet("background-color: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px;")
        elif bail in ("Nem", "Nem adható"):
            self.bail_val.setText("⚖️ Óvadék: Nem adható")
            self.bail_val.setStyleSheet("color: #f87171; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            self.bail_card.setStyleSheet("background-color: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px;")
        else:
            self.bail_val.setText(f"⚖️ Óvadék: {bail}")
            self.bail_val.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            self.bail_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;")

        # Driver's License status (Jogosítvány)
        dl = calculation_data.get("revoke_dl", "Nem")
        if dl == "Kötelező bevonni":
            self.docs_val.setText("🪪 Jogsi: Kötelező bevonni")
            self.docs_val.setStyleSheet("color: #f87171; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            self.docs_card.setStyleSheet("background-color: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 8px;")
        elif dl == "Bevonható":
            self.docs_val.setText("🪪 Jogsi: Bevonható")
            self.docs_val.setStyleSheet("color: #fbbf24; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            self.docs_card.setStyleSheet("background-color: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px;")
        else:
            self.docs_val.setText("🪪 Jogsi: Érintetlen")
            self.docs_val.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            self.docs_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;")

        self.clip_container.show()
        self._fit_to_content()
        self.show()

        if auto_hide_sec > 0:
            self._auto_hide_timer.start(auto_hide_sec * 1000)

    def show_error(self, message: str):
        self.status_icon.setPixmap(get_pixmap(SVG_ALERT, 14, 14))
        self.status_icon.show()
        self.status_label.setText("Hiba")
        self.status_label.setStyleSheet("font-size: 12px; color: #ef4444; font-weight: bold; border: none; background: transparent;")
        self.transcript_label.setText(message)
        self.transcript_label.show()
        self._clear_offenses()
        self.clip_container.hide()
        self._fit_to_content()
        self.show()
        self._auto_hide_timer.start(8000)

    def _clear_offenses(self):
        while self.offenses_container.count():
            item = self.offenses_container.takeAt(0)
            w = item.widget()
            if w:
                w.hide()
                w.setParent(None)
                w.deleteLater()

    def hide_overlay(self):
        self.hide()
