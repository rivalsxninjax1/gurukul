# ui/styles.py — complete, with QMessageBox popup fix

BTN_PRIMARY = """
    QPushButton {
        background: #1a1a1a; color: #ffffff;
        padding: 7px 18px; border-radius: 5px;
        font-size: 13px; font-weight: bold;
        border: none; min-height: 32px;
    }
    QPushButton:hover   { background: #3a3a3a; }
    QPushButton:pressed { background: #000000; }
    QPushButton:disabled { background: #cccccc; color: #888888; }
"""

BTN_PRINT = """
    QPushButton {
        background: #2d4a7a; color: #ffffff;
        padding: 7px 18px; border-radius: 5px;
        font-size: 13px; font-weight: bold;
        border: none; min-height: 32px;
    }
    QPushButton:hover   { background: #3a5fa0; }
    QPushButton:pressed { background: #1e3560; }
    QPushButton:disabled { background: #9bb3da; color: #e7ecf7; }
"""

BTN_DANGER = """
    QPushButton {
        background: #b02020; color: #ffffff;
        padding: 5px 12px; border-radius: 5px;
        font-size: 12px; border: none; min-height: 28px;
    }
    QPushButton:hover   { background: #d32f2f; }
    QPushButton:pressed { background: #8b0000; }
    QPushButton:disabled { background: #cccccc; color: #888888; }
"""

BTN_SECONDARY = """
    QPushButton {
        background: #4a4a4a; color: #ffffff;
        padding: 5px 12px; border-radius: 5px;
        font-size: 12px; border: none; min-height: 28px;
    }
    QPushButton:hover   { background: #666666; }
    QPushButton:pressed { background: #333333; }
    QPushButton:disabled { background: #cccccc; color: #888888; }
"""

BTN_SUCCESS = """
    QPushButton {
        background: #2d6a2d; color: #ffffff;
        padding: 5px 12px; border-radius: 5px;
        font-size: 12px; border: none; min-height: 28px;
    }
    QPushButton:hover   { background: #3a8a3a; }
    QPushButton:pressed { background: #1a4a1a; }
    QPushButton:disabled { background: #cccccc; color: #888888; }
"""

# Input fields — white bg, dark text, always visible
INPUT_STYLE = """
    QLineEdit {
        border: 1.5px solid #cccccc;
        border-radius: 5px;
        padding: 8px 10px;
        font-size: 13px;
        color: #1a1a1a;
        background: #ffffff;
        min-height: 20px;
        selection-background-color: #2c2c2c;
        selection-color: #ffffff;
    }
    QLineEdit:focus   { border-color: #1a1a1a; background: #ffffff; }
    QLineEdit:disabled { background: #f0f0f0; color: #888888; }
"""

INPUT_READONLY_STYLE = """
    QLineEdit {
        border: 1.5px solid #dddddd;
        border-radius: 5px;
        padding: 8px 10px;
        font-size: 13px;
        color: #555555;
        background: #f5f5f5;
        min-height: 20px;
    }
"""

# Dropdown — visible arrow, visible text
COMBO_STYLE = """
    QComboBox {
        border: 1.5px solid #cccccc;
        border-radius: 5px;
        padding: 7px 32px 7px 10px;
        font-size: 13px;
        color: #1a1a1a;
        background: #ffffff;
        min-height: 20px;
        selection-background-color: #2c2c2c;
        selection-color: #ffffff;
    }
    QComboBox:focus   { border-color: #1a1a1a; }
    QComboBox:disabled { background: #f0f0f0; color: #888888; }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid #dddddd;
        border-radius: 0 5px 5px 0;
        background: #f0f0f0;
    }
    QComboBox::down-arrow {
        image: none;
        width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 7px solid #333333;
        margin-right: 4px;
    }
    QComboBox QAbstractItemView {
        background: #ffffff;
        border: 1px solid #cccccc;
        color: #1a1a1a;
        selection-background-color: #2c2c2c;
        selection-color: #ffffff;
        font-size: 13px;
        padding: 4px;
        outline: none;
    }
"""

DATE_STYLE = """
    QDateEdit {
        border: 1.5px solid #cccccc; border-radius: 5px;
        padding: 7px 32px 7px 10px; font-size: 13px;
        color: #1a1a1a; background: #ffffff; min-height: 20px;
    }
    QDateEdit:focus { border-color: #1a1a1a; }
    QDateEdit::drop-down {
        width: 28px; border-left: 1px solid #dddddd;
        background: #f0f0f0; border-radius: 0 5px 5px 0;
    }
    QDateEdit::down-arrow {
        image: none; width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 7px solid #333333; margin-right: 4px;
    }
"""

TIME_STYLE = """
    QTimeEdit {
        border: 1.5px solid #cccccc; border-radius: 5px;
        padding: 7px 10px; font-size: 13px;
        color: #1a1a1a; background: #ffffff; min-height: 20px;
    }
    QTimeEdit:focus { border-color: #1a1a1a; }
    QTimeEdit::drop-down { width: 28px; border-left: 1px solid #dddddd; background: #f0f0f0; }
"""

SPINBOX_STYLE = """
    QSpinBox, QDoubleSpinBox {
        border: 1.5px solid #cccccc; border-radius: 5px;
        padding: 7px 10px; font-size: 13px;
        color: #1a1a1a; background: #ffffff; min-height: 20px;
        selection-background-color: #2c2c2c;
        selection-color: #ffffff;
    }
    QSpinBox:focus, QDoubleSpinBox:focus { border-color: #1a1a1a; }
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {
        background: #f0f0f0; border: none; width: 20px;
    }
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
        width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-bottom: 6px solid #333333;
    }
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
        width: 0; height: 0;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 6px solid #333333;
    }
"""

TABLE_STYLE = """
    QTableWidget {
        border: none; gridline-color: #eeeeee;
        background: #ffffff; alternate-background-color: #f7f7f7;
        font-size: 13px; color: #1a1a1a; outline: none;
    }
    QHeaderView::section {
        background: #2c2c2c; color: #ffffff;
        padding: 10px 8px; font-size: 13px;
        font-weight: bold; border: none;
        border-right: 1px solid #444444;
    }
    QHeaderView::section:last { border-right: none; }
    QTableWidget::item { padding: 6px 8px; color: #1a1a1a; border: none; }
    QTableWidget::item:selected { background: #e0e0e0; color: #1a1a1a; }
    QScrollBar:vertical { border: none; background: #f5f5f5; width: 8px; }
    QScrollBar::handle:vertical {
        background: #cccccc; border-radius: 4px; min-height: 20px;
    }
    QScrollBar:horizontal { border: none; background: #f5f5f5; height: 8px; }
    QScrollBar::handle:horizontal { background: #cccccc; border-radius: 4px; }
"""

LIST_STYLE = """
    QListWidget {
        border: 1px solid #e0e0e0; border-radius: 6px;
        background: #ffffff; font-size: 13px; color: #1a1a1a;
        padding: 4px; outline: none;
    }
    QListWidget::item { padding: 8px 10px; border-radius: 4px; margin: 1px 0; color: #1a1a1a; }
    QListWidget::item:selected { background: #2c2c2c; color: #ffffff; }
    QListWidget::item:hover:!selected { background: #f0f0f0; }
"""

TAB_STYLE = """
    QTabWidget::pane {
        border: 1px solid #e0e0e0; background: #ffffff;
        border-radius: 0px 8px 8px 8px;
    }
    QTabBar::tab {
        background: #eeeeee; color: #555555;
        padding: 9px 22px; font-size: 13px;
        border: 1px solid #e0e0e0; border-bottom: none;
        border-radius: 5px 5px 0 0; margin-right: 3px;
    }
    QTabBar::tab:selected { background: #ffffff; color: #1a1a1a; font-weight: bold; }
    QTabBar::tab:hover:!selected { background: #e0e0e0; }
"""

SCROLL_STYLE = """
    QScrollArea { background: #f5f5f5; border: none; }
    QScrollBar:vertical { border: none; background: #f5f5f5; width: 8px; }
    QScrollBar::handle:vertical { background: #cccccc; border-radius: 4px; min-height: 20px; }
"""

DIALOG_STYLE  = "QDialog { background: #f5f5f5; }"
CARD_STYLE    = """
    QFrame {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
"""
PANEL_STYLE = CARD_STYLE

# ── QMessageBox global style — ensures dark text on light bg ─────────────────
MSGBOX_STYLE = """
    QMessageBox {
        background-color: #ffffff;
    }
    QMessageBox QLabel {
        color: #1a1a1a;
        font-size: 13px;
        background: transparent;
    }
    QMessageBox QPushButton {
        background: #1a1a1a;
        color: #ffffff;
        border: none;
        border-radius: 5px;
        padding: 6px 20px;
        font-size: 13px;
        min-width: 80px;
        min-height: 28px;
    }
    QMessageBox QPushButton:hover   { background: #3a3a3a; }
    QMessageBox QPushButton:pressed { background: #000000; }
"""

# ── Label styles ──────────────────────────────────────────────────────────────
PAGE_TITLE_STYLE    = (
    "font-size: 22px; font-weight: bold; color: #1a1a1a;"
    "background: transparent; border: none;"
)
PANEL_TITLE_STYLE   = (
    "font-size: 15px; font-weight: bold; color: #1a1a1a;"
    "background: transparent; border: none;"
)
SECTION_LABEL_STYLE = (
    "font-size: 11px; color: #888888; font-weight: bold;"
    "letter-spacing: 1px; background: transparent; border: none;"
)
FORM_LABEL_STYLE    = (
    "font-size: 13px; color: #333333; font-weight: bold;"
    "background: transparent; border: none;"
)
FILTER_LABEL_STYLE  = (
    "font-size: 12px; font-weight: bold; color: #444444;"
    "background: transparent; border: none;"
)
HINT_LABEL_STYLE    = (
    "font-size: 12px; color: #888888;"
    "background: transparent; border: none;"
)
ID_BADGE_STYLE      = (
    "font-size: 13px; font-weight: bold; color: #555555;"
    "background: #f0f0f0; border: 1px solid #dddddd;"
    "border-radius: 5px; padding: 6px 12px;"
)

# ── Status colors ─────────────────────────────────────────────────────────────
STATUS_PRESENT       = "#1a5c1a"
STATUS_INCOMPLETE    = "#7a4f00"
STATUS_ABSENT        = "#8b0000"
STATUS_PRESENT_BG    = "#e6f4e6"
STATUS_INCOMPLETE_BG = "#fdf3e0"
STATUS_ABSENT_BG     = "#fdeaea"

# ── Message label colors ──────────────────────────────────────────────────────
MSG_SUCCESS_FG = "#1a5c1a";  MSG_SUCCESS_BG = "#e6f4e6";  MSG_SUCCESS_BD = "#b8ddb8"
MSG_ERROR_FG   = "#8b0000";  MSG_ERROR_BG   = "#fdeaea";  MSG_ERROR_BD   = "#f5b8b8"
MSG_WARNING_FG = "#7a4f00";  MSG_WARNING_BG = "#fdf3e0";  MSG_WARNING_BD = "#f5d98b"
MSG_INFO_FG    = "#1a3a6b";  MSG_INFO_BG    = "#e8f0fb";  MSG_INFO_BD    = "#b8cef5"


def apply_msgbox_style(msgbox):
    """Apply readable style to any QMessageBox instance."""
    msgbox.setStyleSheet(MSGBOX_STYLE)
    return msgbox
