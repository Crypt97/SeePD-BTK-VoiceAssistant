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

        # Stats summary row (Fine + Jail + Docs) - completely borderless subtle pill
        self.stats_frame = QFrame(self.card)
        self.stats_frame.setObjectName("statsFrame")
        self.stats_frame.setStyleSheet("""
            QFrame#statsFrame {
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 10px;
            }
        """)
        stats_layout = QHBoxLayout(self.stats_frame)
        stats_layout.setContentsMargins(14, 10, 14, 10)
        stats_layout.setSpacing(16)

        # Fine box
        fine_box = QVBoxLayout()
        fine_box.setSpacing(2)
        fine_title = QLabel("Bírság", self.stats_frame)
        fine_title.setStyleSheet("font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: bold; border: none;")
        self.fine_val = QLabel("0 Ft", self.stats_frame)
        self.fine_val.setStyleSheet("font-size: 15px; font-weight: bold; color: #10b981; border: none;")
        fine_box.addWidget(fine_title)
        fine_box.addWidget(self.fine_val)
        stats_layout.addLayout(fine_box)

        # Jail box
        jail_box = QVBoxLayout()
        jail_box.setSpacing(2)
        jail_title = QLabel("Börtön", self.stats_frame)
        jail_title.setStyleSheet("font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: bold; border: none;")
        self.jail_val = QLabel("0 perc", self.stats_frame)
        self.jail_val.setStyleSheet("font-size: 15px; font-weight: bold; color: #f59e0b; border: none;")
        jail_box.addWidget(jail_title)
        jail_box.addWidget(self.jail_val)
        stats_layout.addLayout(jail_box)

        # Docs box
        docs_box = QVBoxLayout()
        docs_box.setSpacing(2)
        docs_title = QLabel("Jogosítvány", self.stats_frame)
        docs_title.setStyleSheet("font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: bold; border: none;")
        self.docs_val = QLabel("Nem", self.stats_frame)
        self.docs_val.setStyleSheet("font-size: 14px; font-weight: bold; color: #cbd5e1; border: none;")
        docs_box.addWidget(docs_title)
        docs_box.addWidget(self.docs_val)
        stats_layout.addLayout(docs_box)

        card_layout.addWidget(self.stats_frame)

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
        self.setFixedWidth(400)

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
            self.docs_val.setText("Nem")
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

        dl = calculation_data.get("revoke_dl", "Nem")
        self.docs_val.setText(dl)
        if dl == "Kötelező bevonni":
            self.docs_val.setStyleSheet("font-size: 13px; font-weight: bold; color: #ef4444; border: none;")
        elif dl == "Bevonható":
            self.docs_val.setStyleSheet("font-size: 13px; font-weight: bold; color: #f59e0b; border: none;")
        else:
            self.docs_val.setStyleSheet("font-size: 13px; font-weight: bold; color: #cbd5e1; border: none;")

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
