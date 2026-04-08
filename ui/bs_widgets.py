"""
BSDateEdit — a custom widget that accepts and displays Bikram Sambat dates.

Since PyQt5 QDateEdit is AD-only internally, this widget uses:
- A QLineEdit to show/input the BS date string (YYYY-MM-DD)
- Navigation buttons (< >) for month/day stepping
- Validation feedback inline
- Internally stores the equivalent AD datetime.date

Usage:
    widget = BSDateEdit(parent)
    widget.set_today()                      # set to today BS
    widget.set_bs_date(2082, 1, 15)         # set specific BS date
    widget.get_ad_date()                    # returns datetime.date (AD)
    widget.get_bs_str()                     # returns "2082-01-15"
    widget.dateChanged.connect(callback)    # emits when valid date set
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton,
    QLabel, QSizePolicy
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
import datetime
from utils.bs_converter import (
    ad_to_bs, bs_to_ad, bs_str, today_bs_tuple,
    days_in_bs_month, is_valid_bs_date
)


class BSDateEdit(QWidget):
    """
    Compact BS date input widget.
    Displays: [<] [YYYY-MM-DD input] [>]
    Valid dates show with white bg; invalid shows red border.
    """

    dateChanged = pyqtSignal(datetime.date)   # emits AD date when valid

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ad_date: datetime.date | None = None
        self._bs_year  = 2082
        self._bs_month = 1
        self._bs_day   = 1
        self._build_ui()
        self.set_today()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._prev_btn = QPushButton("‹")
        self._prev_btn.setFixedSize(28, 36)
        self._prev_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0; color: #333333;
                border: 1.5px solid #cccccc; border-radius: 5px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: #e0e0e0; }
            QPushButton:pressed { background: #cccccc; }
        """)
        self._prev_btn.clicked.connect(self._prev_day)

        self._input = QLineEdit()
        self._input.setPlaceholderText("YYYY-MM-DD (BS)")
        self._input.setFixedHeight(36)
        self._input.setMinimumWidth(130)
        self._input.setAlignment(Qt.AlignCenter)
        self._input.setStyleSheet(self._valid_style())
        self._input.editingFinished.connect(self._on_text_edited)
        self._input.textChanged.connect(self._on_text_changed)

        self._next_btn = QPushButton("›")
        self._next_btn.setFixedSize(28, 36)
        self._next_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0; color: #333333;
                border: 1.5px solid #cccccc; border-radius: 5px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: #e0e0e0; }
            QPushButton:pressed { background: #cccccc; }
        """)
        self._next_btn.clicked.connect(self._next_day)

        layout.addWidget(self._prev_btn)
        layout.addWidget(self._input)
        layout.addWidget(self._next_btn)

    # ── Style helpers ─────────────────────────────────────────────────────────

    def _valid_style(self):
        return """
            QLineEdit {
                border: 1.5px solid #cccccc;
                border-radius: 5px;
                padding: 0 8px;
                font-size: 13px;
                color: #1a1a1a;
                background: #ffffff;
            }
            QLineEdit:focus { border-color: #1a1a1a; }
        """

    def _invalid_style(self):
        return """
            QLineEdit {
                border: 1.5px solid #cc3333;
                border-radius: 5px;
                padding: 0 8px;
                font-size: 13px;
                color: #cc3333;
                background: #fff5f5;
            }
        """

    # ── Public API ────────────────────────────────────────────────────────────

    def set_today(self):
        """Set widget to today's BS date."""
        y, m, d = today_bs_tuple()
        if y:
            self.set_bs_date(y, m, d)

    def set_bs_date(self, bs_year: int, bs_month: int, bs_day: int):
        """Set a specific BS date."""
        if is_valid_bs_date(bs_year, bs_month, bs_day):
            self._bs_year  = bs_year
            self._bs_month = bs_month
            self._bs_day   = bs_day
            self._ad_date  = bs_to_ad(bs_year, bs_month, bs_day)
            self._input.blockSignals(True)
            self._input.setText(
                f"{bs_year}-{bs_month:02d}-{bs_day:02d}"
            )
            self._input.blockSignals(False)
            self._input.setStyleSheet(self._valid_style())
            if self._ad_date:
                self.dateChanged.emit(self._ad_date)

    def set_from_ad(self, ad_date: datetime.date):
        """Set widget from an AD datetime.date."""
        if ad_date is None:
            return
        y, m, d = ad_to_bs(ad_date)
        if y:
            self.set_bs_date(y, m, d)

    def get_ad_date(self) -> datetime.date | None:
        """Returns the currently selected date as AD datetime.date."""
        return self._ad_date

    def get_bs_str(self) -> str:
        """Returns BS date string 'YYYY-MM-DD'."""
        if self._ad_date:
            return f"{self._bs_year}-{self._bs_month:02d}-{self._bs_day:02d}"
        return ""

    def get_bs_tuple(self) -> tuple:
        return (self._bs_year, self._bs_month, self._bs_day)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _prev_day(self):
        if self._ad_date:
            new_ad = self._ad_date - datetime.timedelta(days=1)
            self.set_from_ad(new_ad)

    def _next_day(self):
        if self._ad_date:
            new_ad = self._ad_date + datetime.timedelta(days=1)
            self.set_from_ad(new_ad)

    # ── Text input handling ───────────────────────────────────────────────────

    def _on_text_changed(self, text: str):
        """Light validation as user types — only show red when clearly wrong."""
        if len(text) == 10:
            self._on_text_edited()

    def _on_text_edited(self):
        """Full validation on Enter/focus-out."""
        text = self._input.text().strip()
        if not text:
            self.set_today()
            return
        try:
            parts = text.split("-")
            if len(parts) != 3:
                raise ValueError
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            if not is_valid_bs_date(y, m, d):
                raise ValueError
            self._bs_year, self._bs_month, self._bs_day = y, m, d
            self._ad_date = bs_to_ad(y, m, d)
            self._input.setText(f"{y}-{m:02d}-{d:02d}")
            self._input.setStyleSheet(self._valid_style())
            if self._ad_date:
                self.dateChanged.emit(self._ad_date)
        except (ValueError, TypeError):
            self._input.setStyleSheet(self._invalid_style())