from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QMessageBox, QHeaderView, QFrame, QScrollArea,
    QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from database.connection import get_session
from models.expense import Expense
from services.expense_service import (
    add_expense, get_all_expenses, delete_expense,
    get_expense_dashboard_stats, get_total_revenue, get_net_balance,
)
from utils.bs_converter import bs_str
from ui.bs_widgets import BSDateEdit
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY,
    TABLE_STYLE, INPUT_STYLE, SPINBOX_STYLE,
    DIALOG_STYLE, FORM_LABEL_STYLE, PAGE_TITLE_STYLE,
    PANEL_TITLE_STYLE, CARD_STYLE, SECTION_LABEL_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
)
from ui.widgets import Toast
from datetime import date


class ExpensesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Expenses")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        add_btn = QPushButton("+ Add Expense")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_expense)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.toast = Toast()
        layout.addWidget(self.toast)

        # Summary cards
        summary_lbl = QLabel("FINANCIAL SUMMARY")
        summary_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        layout.addWidget(summary_lbl)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(12)

        self._card_revenue = self._stat_card(
            "Total Revenue", "Rs. 0",
            STATUS_PRESENT, STATUS_PRESENT_BG
        )
        self._card_expenses = self._stat_card(
            "Total Expenses", "Rs. 0",
            STATUS_ABSENT, STATUS_ABSENT_BG
        )
        self._card_net = self._stat_card(
            "Net Balance", "Rs. 0",
            "#1a3a6b", "#e8f0fb"
        )
        summary_row.addWidget(self._card_revenue)
        summary_row.addWidget(self._card_expenses)
        summary_row.addWidget(self._card_net)
        layout.addLayout(summary_row)

        # Monthly breakdown
        month_lbl = QLabel("MONTHLY BREAKDOWN")
        month_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        layout.addWidget(month_lbl)

        month_card = QFrame()
        month_card.setStyleSheet(CARD_STYLE)
        ml = QHBoxLayout(month_card)
        ml.setContentsMargins(16, 14, 16, 14)
        ml.setSpacing(12)

        self._cur_month_lbl  = QLabel("Current BS Month:  Rs. 0")
        self._cur_month_lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #333333;"
            "background: transparent; border: none;"
        )
        self._prev_month_lbl = QLabel("Previous BS Month:  Rs. 0")
        self._prev_month_lbl.setStyleSheet(
            "font-size: 13px; color: #666666;"
            "background: transparent; border: none;"
        )
        ml.addWidget(self._cur_month_lbl)
        ml.addWidget(self._prev_month_lbl)
        ml.addStretch()
        layout.addWidget(month_card)

        # Expense table
        exp_lbl = QLabel("ALL EXPENSES")
        exp_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        layout.addWidget(exp_lbl)

        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Date (BS)", "Title", "Amount (Rs.)", "Description", "Actions"]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 100)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.verticalHeader().setVisible(False)
        self.table.setFrameShape(QFrame.NoFrame)
        cl.addWidget(self.table)
        layout.addWidget(card)

    def _stat_card(self, label, value, fg, bg):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
        """)
        card.setMinimumHeight(90)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(4)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {fg};"
            "background: transparent; border: none;"
        )
        lbl_lbl = QLabel(label)
        lbl_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {fg};"
            "background: transparent; border: none;"
        )
        inner.addWidget(val_lbl)
        inner.addWidget(lbl_lbl)
        card._val = val_lbl
        return card

    def refresh(self):
        # Update summary cards
        revenue  = get_total_revenue()
        exp_stat = get_expense_dashboard_stats()
        net      = revenue - exp_stat["total_all_time"]

        self._card_revenue._val.setText(f"Rs. {revenue:,.0f}")
        self._card_expenses._val.setText(f"Rs. {exp_stat['total_all_time']:,.0f}")
        net_fg = STATUS_PRESENT if net >= 0 else STATUS_ABSENT
        self._card_net._val.setText(f"Rs. {net:,.0f}")
        self._card_net._val.setStyleSheet(
            f"font-size: 24px; font-weight: bold; color: {net_fg};"
            "background: transparent; border: none;"
        )

        self._cur_month_lbl.setText(
            f"Current BS Month:   Rs. {exp_stat['current_bs_month']:,.0f}"
        )
        self._prev_month_lbl.setText(
            f"Previous BS Month:  Rs. {exp_stat['previous_bs_month']:,.0f}"
        )

        # Refresh table
        expenses = get_all_expenses()
        self.table.setRowCount(len(expenses))
        for row, e in enumerate(expenses):
            for col, val in enumerate([
                bs_str(e["date"]) if hasattr(e["date"], "year") else str(e["date"]),
                e["title"],
                f"Rs. {e['amount']:,.0f}",
                e["description"],
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.table.setItem(row, col, item)

            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(
                lambda _, eid=e["id"]: self._delete_expense(eid)
            )
            self.table.setCellWidget(row, 4, del_btn)
            self.table.setRowHeight(row, 40)

    def _add_expense(self):
        dlg = AddExpenseDialog(parent=self)
        if dlg.exec_():
            self.refresh()
            self.toast.success("Expense recorded.")

    def _delete_expense(self, expense_id):
        if QMessageBox.question(
            self, "Confirm Delete", "Delete this expense record?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_expense(expense_id)
            self.refresh()
            self.toast.success("Expense deleted.")


class AddExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Expense")
        self.setMinimumWidth(420)
        self.setStyleSheet(DIALOG_STYLE)
        self.setSizeGripEnabled(True)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(28, 28, 28, 20)
        fl.setSpacing(14)

        def field(lbl_text, widget):
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(FORM_LABEL_STYLE)
            fl.addWidget(lbl)
            fl.addWidget(widget)
            fl.addSpacing(2)

        self.title_input = QLineEdit()
        self.title_input.setStyleSheet(INPUT_STYLE)
        self.title_input.setFixedHeight(36)
        self.title_input.setPlaceholderText("e.g. Rent, Utilities, Supplies")

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 9999999)
        self.amount_spin.setValue(0)
        self.amount_spin.setDecimals(0)
        self.amount_spin.setPrefix("Rs. ")
        self.amount_spin.setStyleSheet(SPINBOX_STYLE)
        self.amount_spin.setFixedHeight(36)

        self.date_input = BSDateEdit()
        self.date_input.set_today()

        self.desc_input = QLineEdit()
        self.desc_input.setStyleSheet(INPUT_STYLE)
        self.desc_input.setFixedHeight(36)
        self.desc_input.setPlaceholderText("Optional description")

        field("Title  *",        self.title_input)
        field("Amount (Rs.)  *", self.amount_spin)
        field("Date (BS)",       self.date_input)
        field("Description",     self.desc_input)
        root.addWidget(inner)

        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: #f5f5f5; border-top: 1px solid #e8e8e8; }"
        )
        br = QHBoxLayout(footer)
        br.setContentsMargins(28, 14, 28, 14)
        br.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save Expense")
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self._save)
        br.addWidget(cancel)
        br.addSpacing(10)
        br.addWidget(save)
        root.addWidget(footer)

    def _save(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation", "Title is required.")
            self.title_input.setFocus()
            return
        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, "Validation",
                                "Amount must be greater than zero.")
            return
        exp_date = self.date_input.get_ad_date()
        if not exp_date:
            QMessageBox.warning(self, "Validation", "Invalid date.")
            return
        add_expense(
            title       = title,
            amount      = amount,
            expense_date= exp_date,
            description = self.desc_input.text().strip(),
        )
        self.accept()