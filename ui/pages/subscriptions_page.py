from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QComboBox, QMessageBox, QHeaderView, QFrame,
    QListWidget, QListWidgetItem, QAbstractItemView,
    QFileDialog, QSpinBox, QDoubleSpinBox, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from database.connection import get_session
from models.student import Student
from models.subscription import StudentSubscription, SubscriptionPayment
from services.subscription_service import (
    get_active_subscription,
    get_subscription_history,
    get_payments_for_subscription,
    get_all_payments_for_student,
    add_payment,
    renew_subscription,
    generate_payment_receipt,
)
from utils.bs_converter import bs_str
from ui.bs_widgets import BSDateEdit
from datetime import date
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY,
    TABLE_STYLE, INPUT_STYLE, COMBO_STYLE, SPINBOX_STYLE,
    DIALOG_STYLE, FORM_LABEL_STYLE, PAGE_TITLE_STYLE,
    PANEL_TITLE_STYLE, CARD_STYLE, SECTION_LABEL_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
    STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG,
    LIST_STYLE,
)
from ui.event_bus import bus
from ui.widgets import Toast


PAY_STATUS_STYLE = {
    "paid":    (STATUS_PRESENT,    STATUS_PRESENT_BG),
    "partial": (STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG),
    "unpaid":  (STATUS_ABSENT,     STATUS_ABSENT_BG),
}


class SubscriptionsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self.selected_student_id = None
        self._build_ui()
        self._load_students()
        bus.student_saved.connect(self._load_students)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("Subscriptions & Payments")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        root.addWidget(title)

        self.toast = Toast()
        root.addWidget(self.toast)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(10)
        splitter.setStyleSheet(
            "QSplitter::handle { background: #e0e0e0; }"
        )
        splitter.addWidget(self._build_student_panel())
        splitter.addWidget(self._build_detail_panel())
        splitter.setSizes([280, 720])
        root.addWidget(splitter)

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
        self.student_list.setStyleSheet(LIST_STYLE)
        self.student_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.student_list.itemSelectionChanged.connect(
            self._on_student_selected
        )
        layout.addWidget(self.student_list)
        return frame

    def _build_detail_panel(self):
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none;")
        self._detail_layout = QVBoxLayout(frame)
        self._detail_layout.setContentsMargins(0, 0, 0, 0)
        self._detail_layout.setSpacing(14)

        self._active_card = self._build_active_sub_card()
        self._detail_layout.addWidget(self._active_card)

        pay_lbl = QLabel("PAYMENT HISTORY")
        pay_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._detail_layout.addWidget(pay_lbl)

        pay_frame = QFrame()
        pay_frame.setStyleSheet(CARD_STYLE)
        pay_cl = QVBoxLayout(pay_frame)
        pay_cl.setContentsMargins(0, 0, 0, 0)
        pay_cl.setSpacing(0)

        pay_hdr_w = QWidget()
        pay_hdr_w.setStyleSheet(
            "background: #ffffff; border-bottom: 1px solid #eeeeee;"
        )
        pay_hdr_l = QHBoxLayout(pay_hdr_w)
        pay_hdr_l.setContentsMargins(16, 10, 16, 10)
        pay_title = QLabel("Payments for Active Subscription")
        pay_title.setStyleSheet(PANEL_TITLE_STYLE)

        self.add_pay_btn = QPushButton("+ Add Payment")
        self.add_pay_btn.setStyleSheet(BTN_PRIMARY)
        self.add_pay_btn.setEnabled(False)
        self.add_pay_btn.clicked.connect(self._add_payment)

        pay_hdr_l.addWidget(pay_title)
        pay_hdr_l.addStretch()
        pay_hdr_l.addWidget(self.add_pay_btn)
        pay_cl.addWidget(pay_hdr_w)

        self.pay_table = QTableWidget()
        self.pay_table.setColumnCount(5)
        self.pay_table.setHorizontalHeaderLabels(
            ["Date (BS)", "Amount (Rs.)", "Method", "Note", "Receipt"]
        )
        ph = self.pay_table.horizontalHeader()
        ph.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        ph.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        ph.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        ph.setSectionResizeMode(3, QHeaderView.Stretch)
        ph.setSectionResizeMode(4, QHeaderView.Fixed)
        self.pay_table.setColumnWidth(4, 90)
        self.pay_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.pay_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pay_table.setAlternatingRowColors(True)
        self.pay_table.setStyleSheet(TABLE_STYLE)
        self.pay_table.verticalHeader().setVisible(False)
        self.pay_table.setFrameShape(QFrame.NoFrame)
        self.pay_table.setMaximumHeight(220)
        pay_cl.addWidget(self.pay_table)
        self._detail_layout.addWidget(pay_frame)

        hist_lbl = QLabel("SUBSCRIPTION HISTORY")
        hist_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._detail_layout.addWidget(hist_lbl)

        hist_frame = QFrame()
        hist_frame.setStyleSheet(CARD_STYLE)
        hist_cl = QVBoxLayout(hist_frame)
        hist_cl.setContentsMargins(0, 0, 0, 0)

        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(6)
        self.hist_table.setHorizontalHeaderLabels(
            ["Start (BS)", "End (BS)", "Total Fee",
             "Paid", "Balance", "Status"]
        )
        hh = self.hist_table.horizontalHeader()
        for i in range(6):
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        self.hist_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.hist_table.setAlternatingRowColors(True)
        self.hist_table.setStyleSheet(TABLE_STYLE)
        self.hist_table.verticalHeader().setVisible(False)
        self.hist_table.setFrameShape(QFrame.NoFrame)
        self.hist_table.setMaximumHeight(180)
        hist_cl.addWidget(self.hist_table)
        self._detail_layout.addWidget(hist_frame)

        self._detail_layout.addStretch()
        return frame

    def _build_active_sub_card(self):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("Active Subscription")
        title.setStyleSheet(PANEL_TITLE_STYLE)
        self.renew_btn = QPushButton("Renew Plan")
        self.renew_btn.setStyleSheet(BTN_SECONDARY)
        self.renew_btn.setEnabled(False)
        self.renew_btn.clicked.connect(self._renew)
        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(self.renew_btn)
        layout.addLayout(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #eeeeee; border: none;")
        layout.addWidget(sep)

        info_row = QHBoxLayout()
        info_row.setSpacing(0)
        self._sub_info = {}
        for key in ["Period (BS)", "Days Left", "Total Fee"]:
            col = QVBoxLayout()
            col.setSpacing(4)
            k_lbl = QLabel(key)
            k_lbl.setStyleSheet(
                "font-size: 11px; color: #888888; font-weight: bold;"
                "background: transparent; letter-spacing: 1px; border: none;"
            )
            v_lbl = QLabel("—")
            v_lbl.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #1a1a1a;"
                "background: transparent; border: none;"
            )
            col.addWidget(k_lbl)
            col.addWidget(v_lbl)
            info_row.addLayout(col)
            info_row.addSpacing(40)
            self._sub_info[key] = v_lbl
        layout.addLayout(info_row)

        pay_row = QHBoxLayout()
        pay_row.setSpacing(12)
        self._paid_card  = self._mini_summary(
            "Paid",       "Rs. 0", STATUS_PRESENT,    STATUS_PRESENT_BG)
        self._bal_card   = self._mini_summary(
            "Balance",    "Rs. 0", STATUS_ABSENT,     STATUS_ABSENT_BG)
        self._pstat_card = self._mini_summary(
            "Pay Status", "—",     "#333333",          "#f0f0f0")
        pay_row.addWidget(self._paid_card)
        pay_row.addWidget(self._bal_card)
        pay_row.addWidget(self._pstat_card)
        pay_row.addStretch()
        layout.addLayout(pay_row)
        return card

    def _mini_summary(self, title, value, fg, bg):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }}
        """)
        card.setFixedHeight(64)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(14, 8, 14, 8)
        inner.setSpacing(3)
        t = QLabel(title)
        t.setStyleSheet(
            f"font-size: 11px; font-weight: bold; color: {fg};"
            "background: transparent; border: none;"
        )
        v = QLabel(value)
        v.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {fg};"
            "background: transparent; border: none;"
        )
        inner.addWidget(t)
        inner.addWidget(v)
        card._val = v
        return card

    def _load_students(self):
        session = get_session()
        self._all_students = [
            {"id": s.id, "name": s.name, "uid": s.user_id}
            for s in session.query(Student).order_by(Student.name).all()
        ]
        session.close()
        self._render_student_list(self._all_students)

    def _render_student_list(self, students):
        prev_id = self.selected_student_id
        self.student_list.clear()
        for s in students:
            item = QListWidgetItem(f"  {s['name']}  ({s['uid']})")
            item.setData(Qt.UserRole, s["id"])
            self.student_list.addItem(item)
            if s["id"] == prev_id:
                self.student_list.setCurrentItem(item)

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
        self._refresh_detail()

    def _refresh_detail(self):
        if not self.selected_student_id:
            return
        sub = get_active_subscription(self.selected_student_id)

        if sub:
            self._sub_info["Period (BS)"].setText(
                f"{bs_str(sub['start_date'])}  →  {bs_str(sub['end_date'])}"
            )
            self._sub_info["Days Left"].setText(f"{sub['days_left']} days")
            self._sub_info["Total Fee"].setText(
                f"Rs. {sub['total_fee']:,.0f}"
            )
            self._paid_card._val.setText(f"Rs. {sub['total_paid']:,.0f}")
            self._bal_card._val.setText(f"Rs. {sub['balance']:,.0f}")
            self._pstat_card._val.setText(sub["pay_status"].capitalize())

            fg, bg = PAY_STATUS_STYLE.get(
                sub["pay_status"], ("#333333", "#f0f0f0")
            )
            self._pstat_card._val.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {fg};"
                "background: transparent; border: none;"
            )
            self.add_pay_btn.setEnabled(True)
            self.renew_btn.setEnabled(True)
            self._load_payments(sub["id"])
        else:
            for key in self._sub_info:
                self._sub_info[key].setText("—")
            self._paid_card._val.setText("—")
            self._bal_card._val.setText("—")
            self._pstat_card._val.setText("No active subscription")
            self.add_pay_btn.setEnabled(False)
            self.renew_btn.setEnabled(True)
            self.pay_table.setRowCount(0)

        self._load_history()

    def _load_payments(self, subscription_id):
        pays = get_payments_for_subscription(subscription_id)
        self.pay_table.setRowCount(len(pays))
        for r, p in enumerate(pays):
            d = p["date"]
            d_str = bs_str(d) if hasattr(d, "year") else str(d)
            for c, val in enumerate([
                d_str,
                f"Rs. {p['amount']:,.0f}",
                p["method"],
                p["note"],
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.pay_table.setItem(r, c, item)

            rcpt_btn = QPushButton("PDF")
            rcpt_btn.setStyleSheet(BTN_SECONDARY)
            rcpt_btn.clicked.connect(
                lambda _, pid=p["id"]: self._get_receipt(pid)
            )
            self.pay_table.setCellWidget(r, 4, rcpt_btn)
            self.pay_table.setRowHeight(r, 38)

    def _load_history(self):
        history = get_subscription_history(self.selected_student_id)
        self.hist_table.setRowCount(len(history))
        for r, h in enumerate(history):
            sd = h["start_date"]
            ed = h["end_date"]
            sd_str = bs_str(sd) if hasattr(sd, "year") else str(sd)
            ed_str = bs_str(ed) if hasattr(ed, "year") else str(ed)
            for c, val in enumerate([
                sd_str, ed_str,
                f"Rs. {h['total_fee']:,.0f}",
                f"Rs. {h['total_paid']:,.0f}",
                f"Rs. {h['balance']:,.0f}",
                h["status"].capitalize(),
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                if c == 5:
                    if h["status"] == "active":
                        item.setForeground(QColor(STATUS_PRESENT))
                        item.setBackground(QColor(STATUS_PRESENT_BG))
                    else:
                        item.setForeground(QColor(STATUS_ABSENT))
                        item.setBackground(QColor(STATUS_ABSENT_BG))
                self.hist_table.setItem(r, c, item)
            self.hist_table.setRowHeight(r, 36)

    def _add_payment(self):
        if not self.selected_student_id:
            return
        sub = get_active_subscription(self.selected_student_id)
        if not sub:
            QMessageBox.information(
                self, "No Active Subscription",
                "This student has no active subscription.\nPlease renew first."
            )
            return
        dlg = AddPaymentDialog(
            self.selected_student_id, sub["id"],
            sub["balance"], parent=self
        )
        if dlg.exec_():
            self.toast.success("Payment recorded.")
            self._refresh_detail()
            bus.payment_added.emit()

            if QMessageBox.question(
                self, "Receipt",
                "Generate PDF receipt for this payment?",
                QMessageBox.Yes | QMessageBox.No
            ) == QMessageBox.Yes:
                self._get_receipt(dlg.saved_payment_id)

    def _renew(self):
        if not self.selected_student_id:
            return
        sub = get_active_subscription(self.selected_student_id)
        default_start = sub["end_date"] if sub else date.today()
        dlg = RenewDialog(
            self.selected_student_id, default_start, parent=self
        )
        if dlg.exec_():
            self.toast.success("Subscription renewed.")
            self._refresh_detail()
            bus.payment_added.emit()

    def _get_receipt(self, payment_id):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Receipt", f"receipt_{payment_id}.pdf",
            "PDF Files (*.pdf)"
        )
        if path:
            generate_payment_receipt(payment_id, path)
            QMessageBox.information(self, "Saved", f"Receipt saved:\n{path}")


# ── Add Payment Dialog ────────────────────────────────────────────────────────

class AddPaymentDialog(QDialog):
    def __init__(self, student_id, subscription_id,
                 balance, parent=None):
        super().__init__(parent)
        self.student_id       = student_id
        self.subscription_id  = subscription_id
        self.balance          = balance
        self.saved_payment_id = None
        self.setWindowTitle("Add Payment")
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

        bal_lbl = QLabel(f"Balance due: Rs. {self.balance:,.0f}")
        bal_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {STATUS_ABSENT};"
            f"background: {STATUS_ABSENT_BG}; border-radius: 5px;"
            "padding: 8px 12px; border: none;"
        )
        fl.addWidget(bal_lbl)

        def row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(FORM_LABEL_STYLE)
            fl.addWidget(lbl)
            fl.addWidget(widget)
            fl.addSpacing(2)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 999999)
        self.amount_spin.setValue(max(self.balance, 0.01))
        self.amount_spin.setDecimals(0)
        self.amount_spin.setPrefix("Rs. ")
        self.amount_spin.setStyleSheet(SPINBOX_STYLE)
        self.amount_spin.setFixedHeight(36)

        self.method_combo = QComboBox()
        self.method_combo.addItems(
            ["Cash", "Bank Transfer", "Online", "Cheque"]
        )
        self.method_combo.setStyleSheet(COMBO_STYLE)
        self.method_combo.setFixedHeight(36)

        # BS date picker — defaults to today
        self.date_input = BSDateEdit()
        self.date_input.set_today()

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional note")
        self.note_input.setStyleSheet(INPUT_STYLE)
        self.note_input.setFixedHeight(36)

        row("Amount (Rs.)  *",   self.amount_spin)
        row("Payment Method",    self.method_combo)
        row("Payment Date (BS)", self.date_input)
        row("Note",              self.note_input)
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
        save = QPushButton("Save Payment")
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self._save)
        br.addWidget(cancel)
        br.addSpacing(10)
        br.addWidget(save)
        root.addWidget(footer)

    def _save(self):
        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(
                self, "Validation",
                "Amount must be greater than zero."
            )
            return
        payment_date = self.date_input.get_ad_date()
        if not payment_date:
            QMessageBox.warning(
                self, "Validation",
                "Payment Date (BS) is invalid."
            )
            return
        pid = add_payment(
            student_id      = self.student_id,
            subscription_id = self.subscription_id,
            amount          = amount,
            method          = self.method_combo.currentText(),
            note            = self.note_input.text().strip(),
            payment_date    = payment_date,
        )
        self.saved_payment_id = pid
        self.accept()


# ── Renew Dialog ──────────────────────────────────────────────────────────────

class RenewDialog(QDialog):
    def __init__(self, student_id, default_start, parent=None):
        super().__init__(parent)
        self.student_id    = student_id
        self.default_start = default_start
        self.setWindowTitle("Renew Subscription")
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

        info = QLabel(
            "A new subscription will be created.\n"
            "The previous subscription is kept as history."
        )
        info.setStyleSheet(
            "font-size: 12px; color: #555555; background: #f8f8f8;"
            "border: 1px solid #e8e8e8; border-radius: 5px; padding: 10px;"
        )
        info.setWordWrap(True)
        fl.addWidget(info)

        def row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(FORM_LABEL_STYLE)
            fl.addWidget(lbl)
            fl.addWidget(widget)
            fl.addSpacing(2)

        # BS date picker — defaults to subscription end date or today
        self.start_input = BSDateEdit()
        if hasattr(self.default_start, "year"):
            self.start_input.set_from_ad(self.default_start)
        else:
            self.start_input.set_today()

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 24)
        self.duration_spin.setValue(1)
        self.duration_spin.setSuffix("  month(s)")
        self.duration_spin.setStyleSheet(SPINBOX_STYLE)
        self.duration_spin.setFixedHeight(36)

        self.fee_spin = QDoubleSpinBox()
        self.fee_spin.setRange(0, 999999)
        self.fee_spin.setValue(2000)
        self.fee_spin.setPrefix("Rs. ")
        self.fee_spin.setDecimals(0)
        self.fee_spin.setStyleSheet(SPINBOX_STYLE)
        self.fee_spin.setFixedHeight(36)

        row("Start Date (BS)", self.start_input)
        row("Duration",        self.duration_spin)
        row("Total Fee",       self.fee_spin)
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
        save = QPushButton("Renew")
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self._save)
        br.addWidget(cancel)
        br.addSpacing(10)
        br.addWidget(save)
        root.addWidget(footer)

    def _save(self):
        start_ad = self.start_input.get_ad_date()
        if not start_ad:
            QMessageBox.warning(
                self, "Validation",
                "Start Date (BS) is invalid."
            )
            return
        renew_subscription(
            student_id      = self.student_id,
            start_date      = start_ad,
            duration_months = self.duration_spin.value(),
            total_fee       = self.fee_spin.value(),
        )
        self.accept()