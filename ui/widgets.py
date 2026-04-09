from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from ui.styles import FILTER_LABEL_STYLE


class LoadingOverlay(QWidget):
    """Semi-transparent overlay with spinner text. Parent = page widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("background: rgba(245,245,245,200);")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        box = QFrame()
        box.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        box.setFixedSize(220, 80)
        inner = QVBoxLayout(box)
        inner.setAlignment(Qt.AlignCenter)

        self._label = QLabel("Processing…")
        self._label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #1a1a1a;"
            "background: transparent; border: none;"
        )
        self._label.setAlignment(Qt.AlignCenter)
        inner.addWidget(self._label)
        layout.addWidget(box)
        self.hide()

    def show_with_text(self, text="Processing…"):
        self._label.setText(text)
        self.resize(self.parent().size())
        self.raise_()
        self.show()

    def resizeEvent(self, event):
        if self.parent():
            self.resize(self.parent().size())


class Toast(QLabel):
    """Brief status message that fades after 2.5 seconds."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(36)
        self.hide()
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def success(self, msg):
        self._show(msg, "#1a5c1a", "#e6f4e6", "#b8ddb8")

    def error(self, msg):
        self._show(msg, "#8b0000", "#fdeaea", "#f5b8b8")

    def info(self, msg):
        self._show(msg, "#1a3a6b", "#e8f0fb", "#b8cef5")

    def _show(self, msg, fg, bg, border):
        self.setText(msg)
        self.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {fg};"
            f"background: {bg}; border: 1px solid {border};"
            f"border-radius: 5px; padding: 0 16px;"
        )
        self.show()
        self._timer.start(2500)


class FilterField(QWidget):
    """
    Stack a bold label above any input widget to keep filter rows consistent.

    The wrapped widget keeps a 36px height, consistent padding, and optional
    fixed width so attendance/ reports/ student lists all align visually and
    never overlap when the window is resized.
    """

    def __init__(self, label: str, control: QWidget,
                 width: int | None = None, parent=None):
        super().__init__(parent)
        self._control = control
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setStyleSheet(FILTER_LABEL_STYLE)
        layout.addWidget(lbl)
        layout.addWidget(control)

        if hasattr(control, "setFixedHeight"):
            control.setFixedHeight(36)
        if width and hasattr(control, "setFixedWidth"):
            control.setFixedWidth(width)
        elif hasattr(control, "setMinimumWidth"):
            control.setMinimumWidth(150)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    @property
    def control(self) -> QWidget:
        """Return the wrapped widget for additional configuration."""
        return self._control
