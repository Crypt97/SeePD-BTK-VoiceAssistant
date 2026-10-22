"""
SVG Icons Module
Professional vector SVG icons sourced from allsvgicons.com (Lucide / Tabler Police & Security packs).
Renders vector SVGs cleanly into QPixmap and QIcon without emojis.
"""
import os
import sys
from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QPainter, QPixmap, QIcon
from PyQt6.QtSvg import QSvgRenderer

# Police Badge with Officer Star
SVG_POLICE_BADGE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2l7 3v6c0 5.5-3.8 10.7-7 12-3.2-1.3-7-6.5-7-12V5l7-3z"/>
  <polygon points="12 7 13.3 9.8 16.3 10.2 14.1 12.3 14.6 15.3 12 13.9 9.4 15.3 9.9 12.3 7.7 10.2 10.7 9.8 12 7" fill="#38bdf8" stroke="#38bdf8" stroke-width="0.5"/>
</svg>
"""

# Police Shield Tray Icon (Solid fill for high visibility in system tray)
SVG_TRAY_BADGE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none">
  <path d="M12 2l7 3.2v6.4c0 5.6-3.8 10.5-7 11.9-3.2-1.4-7-6.3-7-11.9V5.2L12 2z" fill="#2563eb" stroke="#ffffff" stroke-width="1.2"/>
  <polygon points="12 6.5 13.5 9.7 17 10.1 14.5 12.5 15.1 16 12 14.3 8.9 16 9.5 12.5 7 10.1 10.5 9.7 12 6.5" fill="#f8fafc"/>
</svg>
"""

# Recording Microphone (Red pulsing active)
SVG_MIC = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" fill="#ef4444"/>
  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
  <line x1="12" x2="12" y1="19" y2="22"/>
  <line x1="8" x2="16" y1="22" y2="22"/>
</svg>
"""

# AI Spinner / Processing (Amber)
SVG_SPINNER = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
</svg>
"""

# Success Checkmark (Green)
SVG_CHECK = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="20 6 9 17 4 12"/>
</svg>
"""

# Clipboard / Copy (Sky blue)
SVG_CLIPBOARD = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect width="13" height="13" x="8" y="8" rx="2" ry="2"/>
  <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
</svg>
"""

# Alert / Error (Red)
SVG_ALERT = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <line x1="12" x2="12" y1="8" y2="12"/>
  <line x1="12" x2="12.01" y1="16" y2="16"/>
</svg>
"""

# Settings Gear
SVG_SETTINGS = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/>
  <circle cx="12" cy="12" r="3"/>
</svg>
"""

# Refresh
SVG_REFRESH = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>
  <path d="M3 3v5h5"/>
  <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"/>
  <path d="M16 16h5v5"/>
</svg>
"""

# Close / Power / Exit
SVG_CLOSE = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M18.36 6.64a9 9 0 1 1-12.73 0"/>
  <line x1="12" x2="12" y1="2" y2="12"/>
</svg>
"""

# Keyboard icon for text input
SVG_KEYBOARD = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect width="20" height="16" x="2" y="4" rx="2" ry="2"/>
  <path d="M6 8h.001M10 8h.001M14 8h.001M18 8h.001M8 12h.001M12 12h.001M16 12h.001M7 16h10"/>
</svg>
"""

def get_pixmap(svg_code: str, width: int = 18, height: int = 18) -> QPixmap:
    """Renders SVG XML string to QPixmap cleanly."""
    renderer = QSvgRenderer(QByteArray(svg_code.strip().encode('utf-8')))
    pix = QPixmap(width, height)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, width, height))
    painter.end()
    return pix

def get_icon(svg_code: str, size: int = 24) -> QIcon:
    """Renders SVG XML string to QIcon."""
    return QIcon(get_pixmap(svg_code, size, size))

def get_asset_path(filename: str) -> str:
    """Locates an asset file whether running in development or PyInstaller frozen bundle."""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            p = os.path.join(sys._MEIPASS, filename)
            if os.path.exists(p):
                return p
        exe_dir = os.path.dirname(sys.executable)
        p = os.path.join(exe_dir, filename)
        if os.path.exists(p):
            return p
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)

def get_app_icon() -> QIcon:
    """Returns the official application shield icon."""
    ico_path = get_asset_path("app.ico")
    if os.path.exists(ico_path):
        return QIcon(ico_path)
    png_path = get_asset_path("icon.png")
    if os.path.exists(png_path):
        return QIcon(png_path)
    return get_icon(SVG_TRAY_BADGE, 32)

def get_app_pixmap(w: int = 18, h: int = 18) -> QPixmap:
    """Returns the official application shield pixmap smoothly scaled."""
    png_path = get_asset_path("icon.png")
    if os.path.exists(png_path):
        pm = QPixmap(png_path)
        if not pm.isNull():
            return pm.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    return get_pixmap(SVG_POLICE_BADGE, w, h)
