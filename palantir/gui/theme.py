"""
Cyberpunk / hacker terminal aesthetic stylesheet and constants.

Color palette:
  BG_DEEP   #080808  — near-black window background
  BG_PANEL  #0d0d0d  — slightly lighter panels
  BG_ROW    #111111  — table row alternating bg
  GREEN     #00ff41  — Matrix-green primary text & borders
  CYAN      #00d4ff  — aircraft / secondary accent
  AMBER     #ffaa00  — warnings / weather
  RED       #ff0040  — alerts / seismic
  ORANGE    #ff6600  — fire detections
  PURPLE    #cc00ff  — satellites
  PINK      #ff00cc  — events
  YELLOW    #ffff00  — traffic
  DIM       #005514  — dimmed/muted green text
"""

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

BG_DEEP  = "#080808"
BG_PANEL = "#0d0d0d"
BG_ROW   = "#111111"
GREEN    = "#00ff41"
CYAN     = "#00d4ff"
AMBER    = "#ffaa00"
RED      = "#ff0040"
ORANGE   = "#ff6600"
PURPLE   = "#cc00ff"
PINK     = "#ff00cc"
YELLOW   = "#ffff00"
DIM      = "#005514"
WHITE    = "#e0e0e0"

LAYER_COLORS = {
    "aircraft":  CYAN,
    "maritime":  GREEN,
    "seismic":   RED,
    "weather":   AMBER,
    "fire":      ORANGE,
    "satellite": PURPLE,
    "events":    PINK,
    "traffic":   YELLOW,
}

QSS = f"""
/* ─── Global ─────────────────────────────────────────────────── */
QMainWindow, QWidget {{
    background-color: {BG_DEEP};
    color: {GREEN};
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    selection-background-color: {GREEN};
    selection-color: {BG_DEEP};
}}

/* ─── Group boxes ─────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {GREEN};
    border-radius: 0px;
    margin-top: 14px;
    padding-top: 6px;
    color: {GREEN};
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    color: {GREEN};
    background-color: {BG_DEEP};
}}

/* ─── Labels ──────────────────────────────────────────────────── */
QLabel {{
    color: {GREEN};
    background: transparent;
}}
QLabel#header {{
    color: {GREEN};
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 3px;
}}
QLabel#status_ok  {{ color: {GREEN}; }}
QLabel#status_err {{ color: {RED};   }}
QLabel#status_off {{ color: {DIM};   }}

/* ─── Buttons ─────────────────────────────────────────────────── */
QPushButton {{
    background-color: {BG_PANEL};
    color: {GREEN};
    border: 1px solid {GREEN};
    border-radius: 0px;
    padding: 4px 12px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
    letter-spacing: 1px;
}}
QPushButton:hover {{
    background-color: {GREEN};
    color: {BG_DEEP};
}}
QPushButton:pressed {{
    background-color: {DIM};
    color: {GREEN};
}}
QPushButton:disabled {{
    color: {DIM};
    border-color: {DIM};
}}

/* ─── Checkboxes ──────────────────────────────────────────────── */
QCheckBox {{
    color: {GREEN};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 12px; height: 12px;
    border: 1px solid {GREEN};
    background: {BG_DEEP};
}}
QCheckBox::indicator:checked {{
    background: {GREEN};
}}

/* ─── Scroll bars ─────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 8px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {GREEN};
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {BG_PANEL};
    height: 8px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {GREEN};
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* ─── List / Tree views ───────────────────────────────────────── */
QListWidget, QTreeWidget, QTableWidget {{
    background-color: {BG_PANEL};
    color: {GREEN};
    border: 1px solid {GREEN};
    gridline-color: {DIM};
    alternate-background-color: {BG_ROW};
    outline: none;
}}
QListWidget::item:selected, QTreeWidget::item:selected,
QTableWidget::item:selected {{
    background-color: {GREEN};
    color: {BG_DEEP};
}}
QHeaderView::section {{
    background-color: {BG_DEEP};
    color: {GREEN};
    border: 1px solid {DIM};
    padding: 3px 6px;
    font-weight: bold;
    letter-spacing: 1px;
}}

/* ─── Splitter ────────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: {DIM};
}}
QSplitter::handle:horizontal {{ width: 2px; }}
QSplitter::handle:vertical   {{ height: 2px; }}

/* ─── Status bar ──────────────────────────────────────────────── */
QStatusBar {{
    background-color: {BG_PANEL};
    color: {GREEN};
    border-top: 1px solid {GREEN};
    font-size: 11px;
}}

/* ─── Combo box ───────────────────────────────────────────────── */
QComboBox {{
    background-color: {BG_PANEL};
    color: {GREEN};
    border: 1px solid {GREEN};
    padding: 2px 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    color: {GREEN};
    selection-background-color: {GREEN};
    selection-color: {BG_DEEP};
}}

/* ─── Spin box ────────────────────────────────────────────────── */
QSpinBox {{
    background-color: {BG_PANEL};
    color: {GREEN};
    border: 1px solid {GREEN};
}}

/* ─── Tool tips ───────────────────────────────────────────────── */
QToolTip {{
    background-color: {BG_PANEL};
    color: {GREEN};
    border: 1px solid {GREEN};
    padding: 4px;
    font-family: "Consolas", "Courier New", monospace;
}}

/* ─── Tab widget ──────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {GREEN};
}}
QTabBar::tab {{
    background: {BG_DEEP};
    color: {DIM};
    border: 1px solid {DIM};
    padding: 4px 12px;
    letter-spacing: 1px;
}}
QTabBar::tab:selected {{
    background: {BG_PANEL};
    color: {GREEN};
    border-color: {GREEN};
}}
"""


def apply(app: QApplication) -> None:
    """Apply the cyberpunk stylesheet to the application."""
    app.setStyleSheet(QSS)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,          QColor(BG_DEEP))
    palette.setColor(QPalette.ColorRole.WindowText,      QColor(GREEN))
    palette.setColor(QPalette.ColorRole.Base,            QColor(BG_PANEL))
    palette.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG_ROW))
    palette.setColor(QPalette.ColorRole.Text,            QColor(GREEN))
    palette.setColor(QPalette.ColorRole.Button,          QColor(BG_PANEL))
    palette.setColor(QPalette.ColorRole.ButtonText,      QColor(GREEN))
    palette.setColor(QPalette.ColorRole.Highlight,       QColor(GREEN))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(BG_DEEP))
    app.setPalette(palette)

    font = QFont("Consolas")
    if not font.exactMatch():
        font = QFont("Courier New")
    font.setPointSize(10)
    app.setFont(font)
