from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QDateEdit, QComboBox, QMessageBox, QHeaderView,
    QFileDialog, QFrame
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from database.connection import get_session
from models.billing import Billing
from models.student import Student
from datetime import date
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY, BTN_SUCCESS,
    TABLE_STYLE, INPUT_STYLE, COMBO_STYLE, DATE_STYLE,
    DIALOG_STYLE, FORM_LABEL_STYLE, PAGE_TITLE_STYLE
)


class BillingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # ── Header
        header = QHBoxLayout()
        title = QLabel("Billing")
        title.setStyleSheet(PAGE_TITLE_STYLE)

        add_btn = QPushButton("+ Generate Bill")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self.open_add_dialog)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_btn)
        layout.addLayout(header)

        # ── Summary bar
        summary_card = QFrame()
        summary_card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }
        """)
        sum_layout = QHBoxLayout(summary_card)
        sum_layout.setContentsMargins(16, 12, 16, 12)
        self.lbl_total   = QLabel("Total: 0")
        self.lbl_paid    = QLabel("Paid: 0")
        self.lbl_unpaid  = QLabel("Unpaid: 0")
        self.lbl_total.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #1a1a1a;"
            "background: #f0f0f0; border-radius: 4px; padding: 4px 10px;"
        )
        self.lbl_paid.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #27500a;"
            "background: #eaf3de; border-radius: 4px; padding: 4px 10px;"
        )
        self.lbl_unpaid.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #8b0000;"
            "background: #fcebeb; border-radius: 4px; padding: 4px 10px;"
        )
        sum_layout.addWidget(self.lbl_total)
        sum_layout.addWidget(self.lbl_paid)
        sum_layout.addWidget(self.lbl_unpaid)
        sum_layout.addStretch()
        layout.addWidget(summary_card)

        # ── Table card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Student", "Amount (Rs.)", "Due Date", "Status", "Note", "Actions"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.verticalHeader().setVisible(False)
        self.table.setFrameShape(QFrame.NoFrame)

        card_layout.addWidget(self.table)
        layout.addWidget(card)

    def refresh_table(self):
        session = get_session()
        bills = session.query(Billing).all()

        paid_count   = sum(1 for b in bills if b.paid == "Paid")
        unpaid_count = len(bills) - paid_count
        self.lbl_total.setText(f"Total Bills: {len(bills)}")
        self.lbl_paid.setText(f"Paid: {paid_count}")
        self.lbl_unpaid.setText(f"Unpaid: {unpaid_count}")

        self.table.setRowCount(len(bills))
        for row, b in enumerate(bills):
            id_item     = QTableWidgetItem(str(b.id))
            name_item   = QTableWidgetItem(b.student.name if b.student else "—")
            amt_item    = QTableWidgetItem(f"Rs. {b.amount:,.0f}")
            due_item    = QTableWidgetItem(str(b.due_date) if b.due_date else "—")
            status_item = QTableWidgetItem(b.paid)
            note_item   = QTableWidgetItem(b.note or "")

            # Color-code status
            if b.paid == "Paid":
                status_item.setForeground(QColor("#27500a"))
                status_item.setBackground(QColor("#eaf3de"))
            else:
                status_item.setForeground(QColor("#8b0000"))
                status_item.setBackground(QColor("#fcebeb"))

            for col, item in enumerate([
                id_item, name_item, amt_item, due_item,
                status_item, note_item
            ]):
                if col not in (4,):   # status already colored
                    item.setForeground(Qt.black)
                self.table.setItem(row, col, item)

            # Actions
            action_w = QWidget()
            al = QHBoxLayout(action_w)
            al.setContentsMargins(6, 3, 6, 3)
            al.setSpacing(6)

            pdf_btn = QPushButton("PDF")
            pdf_btn.setStyleSheet(BTN_SECONDARY)
            pdf_btn.clicked.connect(lambda _, bid=b.id: self.export_pdf(bid))

            mark_btn = QPushButton("Mark Paid")
            mark_btn.setStyleSheet(BTN_SUCCESS)
            mark_btn.setEnabled(b.paid != "Paid")
            mark_btn.clicked.connect(lambda _, bid=b.id: self.mark_paid(bid))

            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(lambda _, bid=b.id: self.delete_bill(bid))

            al.addWidget(pdf_btn)
            al.addWidget(mark_btn)
            al.addWidget(del_btn)
            self.table.setCellWidget(row, 6, action_w)
            self.table.setRowHeight(row, 44)

        session.close()

    def open_add_dialog(self):
        dlg = BillingDialog(parent=self)
        if dlg.exec_():
            self.refresh_table()

    def mark_paid(self, bid):
        session = get_session()
        b = session.query(Billing).get(bid)
        if b:
            b.paid = "Paid"
            session.commit()
        session.close()
        self.refresh_table()

    def delete_bill(self, bid):
        reply = QMessageBox.question(self, "Confirm", "Delete this bill?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            session = get_session()
            b = session.query(Billing).get(bid)
            if b:
                session.delete(b)
                session.commit()
            session.close()
            self.refresh_table()

    def export_pdf(self, bid):
        session = get_session()
        b = session.query(Billing).get(bid)
        if not b:
            session.close()
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", f"bill_{bid}.pdf", "PDF Files (*.pdf)"
        )
        if path:
            from services.billing_service import generate_bill_pdf
            generate_bill_pdf(b, path)
            QMessageBox.information(self, "Saved", f"PDF saved:\n{path}")
        session.close()


class BillingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Bill")
        self.setMinimumWidth(400)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        def lbl(text):
            l = QLabel(text)
            l.setStyleSheet(FORM_LABEL_STYLE)
            return l

        session = get_session()
        students = session.query(Student).all()
        session.close()

        self.student_combo = QComboBox()
        self.student_combo.setStyleSheet(COMBO_STYLE)
        for s in students:
            self.student_combo.addItem(f"{s.name}  ({s.user_id})", s.id)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 2000")
        self.amount_input.setStyleSheet(INPUT_STYLE)

        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate())
        self.due_date_input.setStyleSheet(DATE_STYLE)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional note")
        self.note_input.setStyleSheet(INPUT_STYLE)

        for label_text, widget in [
            ("Student *",      self.student_combo),
            ("Amount (Rs.) *", self.amount_input),
            ("Due Date",       self.due_date_input),
            ("Note",           self.note_input),
        ]:
            form.addRow(lbl(label_text), widget)

        layout.addLayout(form)
        layout.addSpacing(20)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Generate Bill")
        save_btn.setStyleSheet(BTN_PRIMARY)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(8)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _save(self):
        try:
            amount = float(self.amount_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Error", "Enter a valid numeric amount.")
            return
        dd = self.due_date_input.date()
        session = get_session()
        b = Billing(
            student_id = self.student_combo.currentData(),
            amount     = amount,
            due_date   = date(dd.year(), dd.month(), dd.day()),
            note       = self.note_input.text().strip(),
        )
        session.add(b)
        session.commit()
        session.close()
        self.accept()