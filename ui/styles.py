# ui/styles.py — single source of truth for all styles

BTN_PRIMARY = """
    QPushButton {
        background: #1a1a1a;
        color: #ffffff;
        padding: 7px 18px;
        border-radius: 5px;
        font-size: 13px;
        font-weight: bold;
        border: none;
    }
    QPushButton:hover   { background: #3a3a3a; }
    QPushButton:pressed { background: #000000; }
    QPushButton:disabled { background: #cccccc; color: #888888; }
"""

BTN_DANGER = """
    QPushButton {
        background: #b02020;
        color: #ffffff;
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 12px;
        border: none;
    }
    QPushButton:hover   { background: #d32f2f; }
    QPushButton:pressed { background: #8b0000; }
    QPushButton:disabled { background: #cccccc; color: #888888; }
"""

BTN_SECONDARY = """
    QPushButton {
        background: #4a4a4a;
        color: #ffffff;
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 12px;
        border: none;
    }
    QPushButton:hover   { background: #666666; }
    QPushButton:pressed { background: #333333; }
"""

BTN_SUCCESS = """
    QPushButton {
        background: #2d6a2d;
        color: #ffffff;
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 12px;
        border: none;
    }
    QPushButton:hover   { background: #3a8a3a; }
    QPushButton:pressed { background: #1a4a1a; }
    QPushButton:disabled { background: #cccccc; color: #888888; }
"""

TABLE_STYLE = """
    QTableWidget {
        border: none;
        gridline-color: #eeeeee;
        background: #ffffff;
        alternate-background-color: #f7f7f7;
        font-size: 13px;
        color: #1a1a1a;
        outline: none;
    }
    QHeaderView::section {
        background: #2c2c2c;
        color: #ffffff;
        padding: 10px 8px;
        font-size: 13px;
        font-weight: bold;
        border: none;
        border-right: 1px solid #444444;
    }
    QHeaderView::section:last {
        border-right: none;
    }
    QTableWidget::item {
        padding: 6px 8px;
        color: #1a1a1a;
        border: none;
    }
    QTableWidget::item:selected {
        background: #e0e0e0;
        color: #1a1a1a;
    }
    QTableWidget::item:alternate {
        background: #f7f7f7;
        color: #1a1a1a;
    }
    QScrollBar:vertical {
        border: none;
        background: #f5f5f5;
        width: 8px;
    }
    QScrollBar::handle:vertical {
        background: #cccccc;
        border-radius: 4px;
    }
"""

INPUT_STYLE = """
    QLineEdit {
        border: 1.5px solid #cccccc;
        border-radius: 5px;
        padding: 8px 10px;
        font-size: 13px;
        color: #1a1a1a;
        background: #ffffff;
    }
    QLineEdit:focus {
        border-color: #1a1a1a;
        background: #ffffff;
    }
    QLineEdit:disabled {
        background: #f0f0f0;
        color: #999999;
    }
"""

COMBO_STYLE = """
    QComboBox {
        border: 1.5px solid #cccccc;
        border-radius: 5px;
        padding: 7px 10px;
        font-size: 13px;
        color: #1a1a1a;
        background: #ffffff;
    }
    QComboBox:focus { border-color: #1a1a1a; }
    QComboBox::drop-down {
        border: none;
        width: 24px;
    }
    QComboBox QAbstractItemView {
        background: #ffffff;
        border: 1px solid #cccccc;
        color: #1a1a1a;
        selection-background-color: #2c2c2c;
        selection-color: #ffffff;
        font-size: 13px;
        padding: 4px;
    }
"""

DATE_STYLE = """
    QDateEdit {
        border: 1.5px solid #cccccc;
        border-radius: 5px;
        padding: 7px 10px;
        font-size: 13px;
        color: #1a1a1a;
        background: #ffffff;
    }
    QDateEdit:focus { border-color: #1a1a1a; }
    QDateEdit::drop-down {
        border: none;
        width: 24px;
    }
"""

# Applied to QDialog only — do NOT cascade to QLabel here
DIALOG_STYLE = "QDialog { background: #f5f5f5; }"

PAGE_TITLE_STYLE    = "font-size: 22px; font-weight: bold; color: #1a1a1a; background: transparent;"
PANEL_TITLE_STYLE   = "font-size: 15px; font-weight: bold; color: #1a1a1a; background: transparent;"
SECTION_LABEL_STYLE = "font-size: 11px; color: #888888; font-weight: bold; letter-spacing: 1px; background: transparent;"
FORM_LABEL_STYLE    = "font-size: 13px; color: #1a1a1a; font-weight: bold; background: transparent;"
HINT_LABEL_STYLE    = "font-size: 12px; color: #888888; background: transparent;"

CARD_STYLE = """
    QFrame {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
    }
"""

PANEL_STYLE = CARD_STYLE   # alias used in classes_page

STATUS_PRESENT    = "#1a5c1a"
STATUS_INCOMPLETE = "#7a4f00"
STATUS_ABSENT     = "#8b0000"

STATUS_PRESENT_BG    = "#e6f4e6"
STATUS_INCOMPLETE_BG = "#fdf3e0"
STATUS_ABSENT_BG     = "#fdeaea"