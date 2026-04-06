from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QDateEdit, QComboBox, QMessageBox, QHeaderView, QFrame,
    QListWidget, QListWidgetItem, QAbstractItemView, QFileDialog
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from database.connection import get_session
from models.student import Student
from models.payment import Payment
from models.billing import Billing
from services.payment_service import (
    get_student_payment_summary,
    add_payment,
    get_payments_for_student,
)
from services.billing_service import generate_bill_pdf
from datetime import date
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY, BTN_SUCCESS,
    TABLE_STYLE, INPUT_STYLE, COMBO_STYLE, DATE_STYLE,
    DIALOG_STYLE, FORM_LABEL_STYLE, PAGE_TITLE_STYLE,
    PANEL_TITLE_STYLE, CARD_STYLE, SECTION_LABEL_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
    STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG,
)
from ui.event_bus import bus
from ui.widgets import Toast


class PaymentsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self.selected_student_id = None
        self._build_ui()
        self._load_students()
        # Refresh when payment added from anywhere
        bus.payment_added.connect(self._refresh_payment_panel)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("Payments")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        root.addWidget(title)

        self.toast = Toast()
        root.addWidget(self.toast)

        from PyQt5.QtWidgets import QSplitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(10)
        splitter.setStyleSheet("QSplitter::handle { background: #e0e0e0; }")
        splitter.addWidget(self._build_student_panel())
        splitter.addWidget(self._build_payment_panel())
        splitter.setSizes([300, 700])
        root.addWidget(splitter)

    # ── Student list panel ────────────────────────────────────────────────────

    def _build_student_panel(self):
        frame = QFrame()
        frame.setStyleSheet(CARD_STYLE)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hdr = QLabel("Students")
        hdr.setStyleSheet(PANEL_TITLE_STYLE)
        layout.addWidget(hdr)

        self.student_search = QLineEdit()
        self.student_search.setPlaceholderText("Search…")
        self.student_search.setStyleSheet(INPUT_STYLE)
        self.student_search.setFixedHeight(34)
        self.student_search.textChanged.connect(self._filter_students)
        layout.addWidget(self.student_search)

        self.student_list = QListWidget()
        self.student_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0; border-radius: 6px;
                background: #ffffff; font-size: 13px;
                color: #1a1a1a; padding: 4px;
            }
            QListWidget::item {
                padding: 8px 10px; border-radius: 4px; margin: 1px 0;
            }
            QListWidget::item:selected {
                background: #2c2c2c; color: #ffffff;
            }
            QListWidget::item:hover:!selected { background: #f0f0f0; }
        """)
        self.student_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.student_list.itemSelectionChanged.connect(
            self._on_student_selected
        )
        layout.addWidget(self.student_list)
        return frame

    # ── Payment detail panel ──────────────────────────────────────────────────

    def _build_payment_panel(self):
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Summary row
        summary_row = QHBoxLayout()
        summary_row.setSpacing(12)
        self.card_fee     = self._summary_card(
            "Total Fee",  "Rs. 0", "#333333", "#f0f0f0")
        self.card_paid    = self._summary_card(
            "Total Paid", "Rs. 0", STATUS_PRESENT, STATUS_PRESENT_BG)
        self.card_balance = self._summary_card(
            "Balance Due","Rs. 0", STATUS_ABSENT,  STATUS_ABSENT_BG)
        summary_row.addWidget(self.card_fee)
        summary_row.addWidget(self.card_paid)
        summary_row.addWidget(self.card_balance)
        layout.addLayout(summary_row)

        # Payment history card
        hist_frame = QFrame()
        hist_frame.setStyleSheet(CARD_STYLE)
        hist_layout = QVBoxLayout(hist_frame)
        hist_layout.setContentsMargins(0, 0, 0, 0)
        hist_layout.setSpacing(0)

        # Header bar inside card
        hdr_w = QWidget()
        hdr_w.setStyleSheet(
            "background: #ffffff; border-bottom: 1px solid #eeeeee;"
        )
        hdr_l = QHBoxLayout(hdr_w)
        hdr_l.setContentsMargins(16, 12, 16, 12)

        hist_lbl = QLabel("Payment History")
        hist_lbl.setStyleSheet(PANEL_TITLE_STYLE)

        self.add_pay_btn = QPushButton("+ Add Payment")
        self.add_pay_btn.setStyleSheet(BTN_PRIMARY)
        self.add_pay_btn.setEnabled(False)
        self.add_pay_btn.clicked.connect(self._add_payment)

        hdr_l.addWidget(hist_lbl)
        hdr_l.addStretch()
        hdr_l.addWidget(self.add_pay_btn)
        hist_layout.addWidget(hdr_w)

        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(5)
        self.payment_table.setHorizontalHeaderLabels(
            ["Date", "Amount (Rs.)", "Method", "Note", "Actions"]
        )
        hh = self.payment_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.Fixed)
        self.payment_table.setColumnWidth(4, 100)
        self.payment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.payment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.payment_table.setAlternatingRowColors(True)
        self.payment_table.setStyleSheet(TABLE_STYLE)
        self.payment_table.verticalHeader().setVisible(False)
        self.payment_table.setFrameShape(QFrame.NoFrame)
        hist_layout.addWidget(self.payment_table)
        layout.addWidget(hist_frame)
        return frame

    def _summary_card(self, label, value, fg, bg):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
        """)
        card.setMinimumHeight(80)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(4)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {fg};"
            "background: transparent; border: none;"
        )
        t_lbl = QLabel(label)
        t_lbl.setStyleSheet(
            f"font-size: 12px; color: {fg}; font-weight: bold;"
            "background: transparent; border: none;"
        )
        inner.addWidget(val_lbl)
        inner.addWidget(t_lbl)
        card._val = val_lbl
        return card

    # ── Data ─────────────────────────────────────────────────────────────────

    def _load_students(self):
        session = get_session()
        self._all_students = [
            {"id": s.id, "name": s.name, "uid": s.user_id}
            for s in session.query(Student).order_by(Student.name).all()
        ]
        session.close()
        self._render_student_list(self._all_students)

    def _render_student_list(self, students):
        self.student_list.clear()
        for s in students:
            item = QListWidgetItem(f"  {s['name']}  ({s['uid']})")
            item.setData(Qt.UserRole, s["id"])
            self.student_list.addItem(item)

    def _filter_students(self):
        q = self.student_search.text().strip().lower()
        filtered = (
            [s for s in self._all_students
             if q in s["name"].lower() or q in s["uid"].lower()]
            if q else self._all_students
        )
        self._render_student_list(filtered)

    def _on_student_selected(self):
        item = self.student_list.currentItem()
        if not item:
            return
        self.selected_student_id = item.data(Qt.UserRole)
        self.add_pay_btn.setEnabled(True)
        self._refresh_payment_panel()

    def _refresh_payment_panel(self):
        if not self.selected_student_id:
            return
        summary = get_student_payment_summary(self.selected_student_id)
        self.card_fee._val.setText(f"Rs. {summary['total_fee']:,.0f}")
        self.card_paid._val.setText(f"Rs. {summary['total_paid']:,.0f}")
        self.card_balance._val.setText(f"Rs. {summary['balance']:,.0f}")

        payments = get_payments_for_student(self.selected_student_id)
        self.payment_table.setRowCount(len(payments))
        for row, p in enumerate(payments):
            for col, val in enumerate([
                p["date"],
                f"Rs. {p['amount']:,.0f}",
                p["method"],
                p["note"],
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.payment_table.setItem(row, col, item)

            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(
                lambda _, pid=p["id"]: self._delete_payment(pid)
            )
            self.payment_table.setCellWidget(row, 4, del_btn)
            self.payment_table.setRowHeight(row, 40)

        # Auto-update billing status
        self._sync_billing_status(self.selected_student_id, summary)

    def _sync_billing_status(self, student_id, summary):
        """Mark bills Paid if total_paid >= total_fee."""
        session = get_session()
        bills = session.query(Billing).filter_by(
            student_id=student_id
        ).all()
        remaining = summary["total_paid"]
        changed = False
        for b in bills:
            if remaining >= b.amount and b.paid != "Paid":
                b.paid    = "Paid"
                remaining -= b.amount
                changed   = True
            elif remaining > 0 and b.paid == "Unpaid":
                b.paid   = "Partial"
                changed  = True
        if changed:
            session.commit()
            bus.billing_updated.emit()
        session.close()

    def _add_payment(self):
        if not self.selected_student_id:
            return
        dlg = AddPaymentDialog(self.selected_student_id, parent=self)
        if dlg.exec_():
            self.toast.success("Payment recorded successfully.")
            self._refresh_payment_panel()
            bus.payment_added.emit()

            # Offer receipt
            if QMessageBox.question(
                self, "Receipt",
                "Generate PDF receipt for this payment?",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes:
                self._generate_receipt(dlg.saved_payment_id)

    def _generate_receipt(self, payment_id):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Receipt", f"receipt_{payment_id}.pdf",
            "PDF Files (*.pdf)"
        )
        if path:
            from services.payment_service import generate_payment_receipt
            generate_payment_receipt(payment_id, path)
            QMessageBox.information(
                self, "Saved", f"Receipt saved:\n{path}"
            )

    def _delete_payment(self, pid):
        if QMessageBox.question(
            self, "Confirm", "Delete this payment record?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            session = get_session()
            p = session.query(Payment).get(pid)
            if p:
                session.delete(p)
                session.commit()
            session.close()
            self.toast.success("Payment deleted.")
            self._refresh_payment_panel()
            bus.payment_added.emit()


class AddPaymentDialog(QDialog):
    def __init__(self, student_id, parent=None):
        super().__init__(parent)
        self.student_id      = student_id
        self.saved_payment_id = None
        self.setWindowTitle("Add Payment")
        self.setMinimumWidth(400)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(28, 28, 28, 28)
        fl.setSpacing(14)

        def row(lbl_text, widget):
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(FORM_LABEL_STYLE)
            fl.addWidget(lbl)
            fl.addWidget(widget)
            fl.addSpacing(2)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("e.g. 1500")
        self.amount_input.setStyleSheet(INPUT_STYLE)
        self.amount_input.setFixedHeight(36)

        self.method_combo = QComboBox()
        self.method_combo.addItems(
            ["Cash", "Bank Transfer", "Online", "Cheque"]
        )
        self.method_combo.setStyleSheet(COMBO_STYLE)
        self.method_combo.setFixedHeight(36)

        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet(DATE_STYLE)
        self.date_input.setFixedHeight(36)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional note")
        self.note_input.setStyleSheet(INPUT_STYLE)
        self.note_input.setFixedHeight(36)

        row("Amount (Rs.)  *", self.amount_input)
        row("Payment Method",  self.method_combo)
        row("Payment Date",    self.date_input)
        row("Note",            self.note_input)
        root.addWidget(inner)

        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: #f5f5f5; border-top: 1px solid #e8e8e8; }"
        )
        br = QHBoxLayout(footer)
        br.setContentsMargins(28, 16, 28, 16)
        br.addStretch()

        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(BTN_SECONDARY)
        cancel.clicked.connect(self.reject)

        save = QPushButton("Save Payment")
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self._save)

        br.addWidget(cancel)
        br.addSpacing(10)
        br.addWidget(save)
        root.addWidget(footer)

    def _save(self):
        try:
            amount = float(self.amount_input.text().strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self, "Validation", "Enter a valid positive amount."
            )
            self.amount_input.setFocus()
            return

        d = self.date_input.date()
        pid = add_payment(
            student_id   = self.student_id,
            amount       = amount,
            method       = self.method_combo.currentText(),
            note         = self.note_input.text().strip(),
            payment_date = date(d.year(), d.month(), d.day()),
        )
        self.saved_payment_id = pid
        self.accept()