"""
Left panel: source status indicators + layer toggles.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from palantir.gui.theme import AMBER, DIM, GREEN, LAYER_COLORS, RED


class SourceRow(QWidget):
    """One row per data source: ● NAME    COUNT  [toggle]"""

    toggled = pyqtSignal(str, bool)  # layer_name, visible

    def __init__(self, layer_name: str, display_name: str, parent=None):
        super().__init__(parent)
        self.layer_name = layer_name
        color = LAYER_COLORS.get(layer_name, GREEN)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(6)

        # Bullet indicator
        self._dot = QLabel("●")
        self._dot.setStyleSheet(f"color: {DIM}; font-size: 14px;")
        self._dot.setFixedWidth(16)
        layout.addWidget(self._dot)

        # Name
        name_lbl = QLabel(display_name.upper())
        name_lbl.setStyleSheet(f"color: {color}; font-size: 11px; letter-spacing: 1px;")
        name_lbl.setFixedWidth(90)
        layout.addWidget(name_lbl)

        # Count
        self._count = QLabel("--")
        self._count.setStyleSheet(f"color: {color}; font-size: 11px;")
        self._count.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._count.setFixedWidth(52)
        layout.addWidget(self._count)

        # Toggle checkbox
        self._chk = QCheckBox()
        self._chk.setChecked(True)
        self._chk.setToolTip(f"Toggle {display_name} layer on map")
        self._chk.toggled.connect(lambda v: self.toggled.emit(self.layer_name, v))
        layout.addWidget(self._chk)

    def set_status(self, count: int, ok: bool) -> None:
        if not ok:
            self._dot.setStyleSheet(f"color: {RED}; font-size: 14px;")
            self._count.setText("ERR")
        elif count == 0:
            self._dot.setStyleSheet(f"color: {DIM}; font-size: 14px;")
            self._count.setText("0")
        else:
            color = LAYER_COLORS.get(self.layer_name, GREEN)
            self._dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            self._count.setText(f"{count:,}")

    def set_fetching(self) -> None:
        self._dot.setStyleSheet(f"color: {AMBER}; font-size: 14px;")
        self._count.setText("...")


class SourcePanel(QWidget):
    """Left sidebar with per-source status and layer toggles."""

    layer_toggled = pyqtSignal(str, bool)

    _SOURCES = [
        ("aircraft",  "ADS-B"),
        ("maritime",  "AIS"),
        ("seismic",   "SEISMIC"),
        ("weather",   "WEATHER"),
        ("fire",      "FIRE"),
        ("satellite", "SAT-TLE"),
        ("events",    "GDELT"),
        ("traffic",   "TRAFFIC"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setFixedWidth(200)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        box = QGroupBox("// SOURCES //")
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(2)

        self._rows: dict[str, SourceRow] = {}
        for layer_name, display_name in self._SOURCES:
            row = SourceRow(layer_name, display_name)
            row.toggled.connect(self.layer_toggled)
            box_layout.addWidget(row)
            self._rows[layer_name] = row

        box_layout.addStretch()
        outer.addWidget(box)
        outer.addStretch()

    def set_fetching(self, layer_name: str) -> None:
        if row := self._rows.get(layer_name):
            row.set_fetching()

    def update_source(self, layer_name: str, count: int, ok: bool) -> None:
        if row := self._rows.get(layer_name):
            row.set_status(count, ok)
