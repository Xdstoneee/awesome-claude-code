"""
Background QThread workers — one per source.
Each worker runs on its own thread so a slow fetch doesn't freeze the GUI.
"""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from palantir.models import SourceResult


class FetchWorker(QThread):
    """Generic fetch worker: calls fn() in a background thread and emits the result."""

    finished = pyqtSignal(object)   # SourceResult
    error    = pyqtSignal(str, str) # source_name, error_message

    def __init__(self, source_name: str, fn, parent=None, **kwargs):
        super().__init__(parent)
        self.source_name = source_name
        self._fn = fn
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result: SourceResult = self._fn(**self._kwargs)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(self.source_name, str(exc))
