"""
Right panel: scrolling live event feed — newest events at the top.
"""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from palantir.gui.theme import BG_DEEP, DIM, GREEN, LAYER_COLORS
from palantir.models import GeoRecord

_MAX_ITEMS = 500


class FeedPanel(QWidget):
    """Scrollable log of the most recent events across all sources."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setFixedWidth(280)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        box = QGroupBox("// LIVE FEED //")
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(4, 4, 4, 4)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setFont(QFont("Consolas", 9))
        box_layout.addWidget(self._list)

        layout.addWidget(box)

    def add_records(self, records: list[GeoRecord]) -> None:
        """Prepend new records (most recent first)."""
        for rec in records[:200]:  # cap per batch
            color = LAYER_COLORS.get(rec.layer.value, GREEN)
            ts    = rec.observed_at.strftime("%H:%M:%S")
            label = rec.label[:30]
            src   = rec.source_name[:8].upper()

            item = QListWidgetItem(f"{ts} │ {src:<8} │ {label}")
            item.setForeground(QColor(color))
            item.setBackground(QColor(BG_DEEP))
            item.setToolTip(
                f"Layer:  {rec.layer.value}\n"
                f"Source: {rec.source_name}\n"
                f"UID:    {rec.uid}\n"
                f"Time:   {rec.observed_at.isoformat()}\n"
                f"Lat/Lon: {rec.lat}, {rec.lon}"
            )
            self._list.insertItem(0, item)

        # Trim old items
        while self._list.count() > _MAX_ITEMS:
            self._list.takeItem(self._list.count() - 1)

    def add_message(self, msg: str, color: str = DIM) -> None:
        """Add a system message line."""
        ts   = datetime.utcnow().strftime("%H:%M:%S")
        item = QListWidgetItem(f"{ts} │ SYS      │ {msg}")
        item.setForeground(QColor(color))
        item.setBackground(QColor(BG_DEEP))
        self._list.insertItem(0, item)
        while self._list.count() > _MAX_ITEMS:
            self._list.takeItem(self._list.count() - 1)
