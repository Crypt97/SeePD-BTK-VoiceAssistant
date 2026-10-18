"""
Quick Text Input Dialog for SeePD BTK Assistant
Allows officers to type offenses directly without speaking into a microphone.
Matches the dark borderless glass aesthetic of the HUD overlay.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent

from icons import SVG_POLICE_BADGE, SVG_KEYBOARD, SVG_CLOSE, get_pixmap, get_icon

class QuickTextInputDialog(QWidget):
    submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Main Card Container
        self.card = QFrame(self)
        self.card.setObjectName("textInputCard")
        self.card.setStyleSheet("""
            QFrame#textInputCard {
                background-color: rgba(15, 17, 23, 0.96);
                border: none;
                border-radius: 14px;
            }
            QLabel {
                border: none;
                background: transparent;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 220))
        shadow.setOffset(0, 6)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)

        # Header Row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Badge
        badge_frame = QFrame(self.card)
        badge_frame.setObjectName("badgeFrame")
        badge_frame.setFixedHeight(24)
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
        badge_layout.setContentsMargins(7, 0, 8, 0)
        badge_layout.setSpacing(6)

        icon_badge = QLabel(badge_frame)
        icon_badge.setPixmap(get_pixmap(SVG_POLICE_BADGE, 14, 14))
        badge_layout.addWidget(icon_badge)

        lbl_badge = QLabel("SeePD BTK", badge_frame)
        lbl_badge.setStyleSheet("font-size: 11px; font-weight: bold; color: #38bdf8;")
        badge_layout.addWidget(lbl_badge)
        header_layout.addWidget(badge_frame)

        # Title
        title = QLabel("Szöveges Szabálysértés Bevitel", self.card)
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Close button [X]
        btn_close = QPushButton(self.card)
        btn_close.setIcon(get_icon(SVG_CLOSE, 14))
        btn_close.setFixedSize(22, 22)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 11px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
        """)
        btn_close.clicked.connect(self.hide)
        header_layout.addWidget(btn_close)

        card_layout.addLayout(header_layout)

        # Input Row (Keyboard Icon + LineEdit)
        input_frame = QFrame(self.card)
        input_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 9px;
            }
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 4, 10, 4)
        input_layout.setSpacing(8)

        icon_kb = QLabel(input_frame)
        icon_kb.setPixmap(get_pixmap(SVG_KEYBOARD, 16, 16))
        icon_kb.setStyleSheet("border: none; background: transparent;")
        input_layout.addWidget(icon_kb)

        self.input_text = QLineEdit(input_frame)
        self.input_text.setPlaceholderText("Írd be a szabálysértéseket (pl. gyorshajtás, piros lámpa, fegyverbirtoklás)...")
        self.input_text.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #f8fafc;
                font-size: 13px;
                padding: 6px 0px;
            }
            QLineEdit::placeholder {
                color: #64748b;
            }
        """)
        self.input_text.returnPressed.connect(self._on_submit)
        input_layout.addWidget(self.input_text)

        card_layout.addWidget(input_frame)

        # Footer Row (Hint + Submit Button)
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        lbl_hint = QLabel("Enter = Beküldés • Esc = Mégse", self.card)
        lbl_hint.setStyleSheet("font-size: 11px; color: #64748b;")
        footer_layout.addWidget(lbl_hint)

        footer_layout.addStretch()

        btn_submit = QPushButton("Kalkuláció (Enter)", self.card)
        btn_submit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_submit.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        btn_submit.clicked.connect(self._on_submit)
        footer_layout.addWidget(btn_submit)

        card_layout.addLayout(footer_layout)

        main_layout.addWidget(self.card)
        self.setFixedWidth(540)

    def show_and_focus(self):
        """Centers on screen, shows and gives immediate keyboard focus."""
        screen = self.screen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 3
        self.move(x, y)
        self.input_text.clear()
        self.show()
        self.raise_()
        self.activateWindow()
        self.input_text.setFocus()

    def _on_submit(self):
        text = self.input_text.text().strip()
        if text:
            self.hide()
            self.submitted.emit(text)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            event.accept()
        else:
            super().keyPressEvent(event)
