from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from database.connection import get_session
from models.student import Student
from services.subscription_service import (
    get_active_subscription, get_subscription_history,
    get_outstanding_balance, get_all_payments_for_student,
)
from services.attendance_analytics_service import (
    get_two_month_analytics, bs_month_name
)
from services.exam_service import get_results_for_student
from services.export_service import export_student_profile_pdf
from services.settings_service import get_setting
from utils.bs_converter import bs_str
from utils.logo_helper import logo_pixmap
from ui.styles import (
    BTN_PRIMARY, BTN_SECONDARY, TABLE_STYLE, PAGE_TITLE_STYLE,
    CARD_STYLE, SECTION_LABEL_STYLE, PANEL_TITLE_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
    STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG,
    apply_msgbox_style,
)

CENTRE_NAME    = "GURUKUL ACADEMY AND TRAINING CENTER"
CENTRE_ADDRESS = "Biratnagar-1, Bhatta Chowk"


def _make_logo_label(w: int = 38, h: int = 38) -> QLabel:
    """Create a QLabel with logo PNG or fallback."""
    lbl = QLabel()
    lbl.setFixedSize(w, h)
    lbl.setAlignment(Qt.AlignCenter)
    pix = logo_pixmap(w, h)
    if pix:
        lbl.setPixmap(pix)
        lbl.setStyleSheet("background: transparent; border: none;")
    else:
        rad = min(w, h) // 2
        lbl.setText("G")
        lbl.setStyleSheet(f"""
            QLabel {{
                background: #ffffff; border-radius: {rad}px;
                color: #1a1a1a;
                font-size: {int(w * 0.45)}px; font-weight: bold;
                border: none;
            }}
        """)
    return lbl


class StudentProfilePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._student_id  = None
        self._join_date   = None
        self._att_visible = False
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: #f5f5f5; border: none; }"
        )
        content = QWidget()
        content.setStyleSheet("background: #f5f5f5;")
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(20)

        # ── Branding strip ────────────────────────────────────────────────────
        brand_strip = QFrame()
        brand_strip.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                border-radius: 8px;
                border: none;
            }
        """)
        brand_strip.setFixedHeight(62)
        bs_layout = QHBoxLayout(brand_strip)
        bs_layout.setContentsMargins(16, 0, 16, 0)
        bs_layout.setSpacing(12)

        # Logo
        logo_lbl = _make_logo_label(42, 42)
        bs_layout.addWidget(logo_lbl)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(1)
        brand_name = QLabel(CENTRE_NAME)
        brand_name.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #ffffff;"
            "background: transparent; border: none;"
        )
        brand_name.setWordWrap(True)
        brand_addr = QLabel(CENTRE_ADDRESS)
        brand_addr.setStyleSheet(
            "font-size: 10px; color: #888888; background: transparent; border: none;"
        )
        brand_col.addWidget(brand_name)
        brand_col.addWidget(brand_addr)
        bs_layout.addLayout(brand_col)
        bs_layout.addStretch()

        page_tag = QLabel("Student Profile")
        page_tag.setStyleSheet(
            "font-size: 11px; color: #666666; background: transparent; border: none;"
        )
        bs_layout.addWidget(page_tag)
        self._layout.addWidget(brand_strip)

        # ── Back + export ─────────────────────────────────────────────────────
        top = QHBoxLayout()
        back = QPushButton("← Back to Students")
        back.setStyleSheet(BTN_SECONDARY)
        back.clicked.connect(self._go_back)
        top.addWidget(back)
        top.addStretch()
        export_btn = QPushButton("Export Profile PDF")
        export_btn.setStyleSheet(BTN_PRIMARY)
        export_btn.clicked.connect(self._export_pdf)
        top.addWidget(export_btn)
        self._layout.addLayout(top)

        self._name_label = QLabel("Student Profile")
        self._name_label.setStyleSheet(PAGE_TITLE_STYLE)
        self._layout.addWidget(self._name_label)

        # Outstanding balance warning
        self._outstanding_warning = QLabel("")
        self._outstanding_warning.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {STATUS_ABSENT};"
            f"background: {STATUS_ABSENT_BG}; border: 1px solid #f5b8b8;"
            "border-radius: 5px; padding: 10px 14px;"
        )
        self._outstanding_warning.setWordWrap(True)
        self._outstanding_warning.hide()
        self._layout.addWidget(self._outstanding_warning)

        # Two-column: info + subscription
        cols = QHBoxLayout()
        cols.setSpacing(16)
        self._info_card = self._build_info_card()
        self._sub_card  = self._build_sub_card()
        cols.addWidget(self._info_card, 1)
        cols.addWidget(self._sub_card,  1)
        self._layout.addLayout(cols)

        # Monthly analytics
        att_analytics_lbl = QLabel("MONTHLY ATTENDANCE ANALYTICS")
        att_analytics_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(att_analytics_lbl)
        self._analytics_card = self._build_analytics_card()
        self._layout.addWidget(self._analytics_card)

        # Attendance history
        att_hdr_row = QHBoxLayout()
        att_section_lbl = QLabel("ATTENDANCE HISTORY")
        att_section_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        att_hdr_row.addWidget(att_section_lbl)
        att_hdr_row.addStretch()
        self._toggle_att_btn = QPushButton("View Attendance History")
        self._toggle_att_btn.setStyleSheet(BTN_SECONDARY)
        self._toggle_att_btn.clicked.connect(self._toggle_attendance)
        att_hdr_row.addWidget(self._toggle_att_btn)
        self._layout.addLayout(att_hdr_row)

        self._att_frame = QFrame()
        self._att_frame.setStyleSheet(CARD_STYLE)
        att_cl = QVBoxLayout(self._att_frame)
        att_cl.setContentsMargins(0, 0, 0, 0)
        self.att_table = self._make_table(
            ["Date (BS)", "Entry", "Exit", "Status"], max_h=300
        )
        att_cl.addWidget(self.att_table)
        self._att_frame.hide()
        self._layout.addWidget(self._att_frame)

        # Exam results
        exam_lbl = QLabel("EXAMINATION RESULTS")
        exam_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(exam_lbl)
        self._exam_results_container = QWidget()
        self._exam_results_container.setStyleSheet("background: transparent;")
        self._exam_results_layout = QVBoxLayout(self._exam_results_container)
        self._exam_results_layout.setContentsMargins(0, 0, 0, 0)
        self._exam_results_layout.setSpacing(12)
        self._layout.addWidget(self._exam_results_container)

        # Subscription history
        sub_hist_lbl = QLabel("SUBSCRIPTION HISTORY")
        sub_hist_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(sub_hist_lbl)
        sub_hist_frame = QFrame()
        sub_hist_frame.setStyleSheet(CARD_STYLE)
        shcl = QVBoxLayout(sub_hist_frame)
        shcl.setContentsMargins(0, 0, 0, 0)
        self.sub_hist_table = self._make_table(
            ["Start (BS)", "End (BS)", "Fee", "Paid", "Balance", "Status", "Days"],
            max_h=180
        )
        shcl.addWidget(self.sub_hist_table)
        self._layout.addWidget(sub_hist_frame)

        # Payment history
        pay_lbl = QLabel("PAYMENT HISTORY")
        pay_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(pay_lbl)
        pay_frame = QFrame()
        pay_frame.setStyleSheet(CARD_STYLE)
        pcl = QVBoxLayout(pay_frame)
        pcl.setContentsMargins(0, 0, 0, 0)
        self.pay_table = self._make_table(
            ["Date (BS)", "Amount (Rs.)", "Method", "Note"], max_h=200
        )
        pcl.addWidget(self.pay_table)
        self._layout.addWidget(pay_frame)

        self._layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _toggle_attendance(self):
        self._att_visible = not self._att_visible
        if self._att_visible:
            self._att_frame.show()
            self._toggle_att_btn.setText("Hide Attendance History")
        else:
            self._att_frame.hide()
            self._toggle_att_btn.setText("View Attendance History")

    def _build_info_card(self):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        hdr = QLabel("Personal Details")
        hdr.setStyleSheet(PANEL_TITLE_STYLE)
        layout.addWidget(hdr)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1); sep.setStyleSheet("background: #eeeeee; border: none;")
        layout.addWidget(sep)
        self._info_vals = {}
        for key in [
            "User ID", "Phone", "Guardian", "WhatsApp",
            "Address", "Date of Birth (BS)", "Join Date (BS)",
            "Class", "Group"
        ]:
            row = QHBoxLayout()
            k = QLabel(key + ":")
            k.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #666666;"
                "background: transparent; min-width: 130px; border: none;"
            )
            k.setFixedWidth(150)
            v = QLabel("—")
            v.setStyleSheet(
                "font-size: 13px; color: #1a1a1a; background: transparent; border: none;"
            )
            v.setWordWrap(True)
            row.addWidget(k); row.addWidget(v); row.addStretch()
            layout.addLayout(row)
            self._info_vals[key] = v
        return card

    def _build_sub_card(self):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        hdr = QLabel("Active Subscription")
        hdr.setStyleSheet(PANEL_TITLE_STYLE)
        layout.addWidget(hdr)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1); sep.setStyleSheet("background: #eeeeee; border: none;")
        layout.addWidget(sep)
        self._sub_vals = {}
        for key in [
            "Start Date (BS)", "End Date (BS)", "Days",
            "Total Fee", "Paid", "Balance", "Status"
        ]:
            row = QHBoxLayout()
            k = QLabel(key + ":")
            k.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #666666;"
                "background: transparent; min-width: 110px; border: none;"
            )
            k.setFixedWidth(120)
            v = QLabel("—")
            v.setStyleSheet(
                "font-size: 13px; color: #1a1a1a; background: transparent; border: none;"
            )
            row.addWidget(k); row.addWidget(v); row.addStretch()
            layout.addLayout(row)
            self._sub_vals[key] = v
        layout.addStretch()
        return card

    def _build_analytics_card(self):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)
        self._analytics_rows = {}
        for period in ["current", "previous"]:
            period_lbl = QLabel("—")
            period_lbl.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #888888;"
                "background: transparent; border: none;"
            )
            layout.addWidget(period_lbl)
            cards_row = QHBoxLayout()
            cards_row.setSpacing(10)
            stat_cards = {}
            for key, label, fg, bg in [
                ("working_days", "Working Days", "#333333",      "#f0f0f0"),
                ("present",      "Present",      STATUS_PRESENT, STATUS_PRESENT_BG),
                ("absent",       "Absent",       STATUS_ABSENT,  STATUS_ABSENT_BG),
                ("incomplete",   "Incomplete",   "#7a4f00",       "#fdf3e0"),
                ("holiday",      "Holiday",      "#555555",       "#eeeeee"),
            ]:
                mini = QFrame()
                mini.setStyleSheet(f"""
                    QFrame {{ background: {bg}; border: 1px solid #e0e0e0; border-radius: 6px; }}
                """)
                mini.setFixedHeight(64)
                inner = QVBoxLayout(mini)
                inner.setContentsMargins(12, 8, 12, 8)
                inner.setSpacing(2)
                t = QLabel(label)
                t.setStyleSheet(
                    f"font-size: 11px; font-weight: bold; color: {fg};"
                    "background: transparent; border: none;"
                )
                v = QLabel("—")
                v.setStyleSheet(
                    f"font-size: 18px; font-weight: bold; color: {fg};"
                    "background: transparent; border: none;"
                )
                inner.addWidget(t); inner.addWidget(v)
                cards_row.addWidget(mini)
                stat_cards[key] = v
            layout.addLayout(cards_row)
            self._analytics_rows[period] = {
                "label": period_lbl, "stat_cards": stat_cards,
            }
        return card

    def _make_table(self, headers, max_h=None):
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        hh = t.horizontalHeader()
        for i in range(len(headers)):
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.setStyleSheet(TABLE_STYLE)
        t.verticalHeader().setVisible(False)
        t.setFrameShape(QFrame.NoFrame)
        if max_h:
            t.setMaximumHeight(max_h)
        return t

    def load_student(self, student_id):
        if student_id < 0:
            return
        self._student_id = student_id
        self._att_visible = False
        self._att_frame.hide()
        self._toggle_att_btn.setText("View Attendance History")

        session = get_session()
        s = session.query(Student).get(student_id)
        if not s:
            session.close()
            return

        self._join_date = s.join_date
        self._name_label.setText(s.name)
        self._info_vals["User ID"].setText(s.user_id)
        self._info_vals["Phone"].setText(s.phone or "—")
        self._info_vals["Guardian"].setText(s.guardian_name or "—")
        self._info_vals["WhatsApp"].setText(s.whatsapp_number or "—")
        self._info_vals["Address"].setText(s.address or "—")
        self._info_vals["Date of Birth (BS)"].setText(
            bs_str(s.dob) if s.dob else "—"
        )
        self._info_vals["Join Date (BS)"].setText(
            bs_str(s.join_date) if s.join_date else "—"
        )
        self._info_vals["Class"].setText(s.class_.name if s.class_ else "—")
        self._info_vals["Group"].setText(s.group.name  if s.group  else "—")

        atts = sorted(
            [a for a in s.attendances
             if (s.join_date is None or a.date >= s.join_date)],
            key=lambda a: a.date, reverse=True
        )
        self.att_table.setRowCount(len(atts))
        for r, att in enumerate(atts):
            vals = [
                bs_str(att.date),
                str(att.entry_time) if att.entry_time else "—",
                str(att.exit_time)  if att.exit_time  else "—",
                att.status or "",
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                if c == 3:
                    if val == "Present":
                        item.setForeground(QColor(STATUS_PRESENT))
                        item.setBackground(QColor(STATUS_PRESENT_BG))
                    elif val == "Incomplete":
                        item.setForeground(QColor(STATUS_INCOMPLETE))
                        item.setBackground(QColor(STATUS_INCOMPLETE_BG))
                    elif val == "Absent":
                        item.setForeground(QColor(STATUS_ABSENT))
                        item.setBackground(QColor(STATUS_ABSENT_BG))
                self.att_table.setItem(r, c, item)
            self.att_table.setRowHeight(r, 36)
        session.close()

        outstanding = get_outstanding_balance(student_id)
        if outstanding > 0:
            self._outstanding_warning.setText(
                f"⚠  Outstanding balance across ALL subscriptions: "
                f"Rs. {outstanding:,.0f}  — Please clear dues."
            )
            self._outstanding_warning.show()
        else:
            self._outstanding_warning.hide()

        sub = get_active_subscription(student_id)
        if sub:
            self._sub_vals["Start Date (BS)"].setText(bs_str(sub["start_date"]))
            self._sub_vals["End Date (BS)"].setText(bs_str(sub["end_date"]))
            self._sub_vals["Days"].setText(sub["days_label"])
            self._sub_vals["Total Fee"].setText(f"Rs. {sub['total_fee']:,.0f}")
            self._sub_vals["Paid"].setText(f"Rs. {sub['total_paid']:,.0f}")
            self._sub_vals["Balance"].setText(f"Rs. {sub['balance']:,.0f}")
            ps = sub["pay_status"]
            fg = (STATUS_PRESENT    if ps == "paid"    else
                  STATUS_INCOMPLETE if ps == "partial" else
                  STATUS_ABSENT)
            v = self._sub_vals["Status"]
            v.setText(ps.capitalize())
            v.setStyleSheet(
                f"font-size: 13px; font-weight: bold; color: {fg};"
                "background: transparent; border: none;"
            )
        else:
            for key in self._sub_vals:
                self._sub_vals[key].setText("—")
            self._sub_vals["Status"].setText("No active subscription")
            self._sub_vals["Status"].setStyleSheet(
                "font-size: 13px; color: #888888; background: transparent; border: none;"
            )

        analytics = get_two_month_analytics(student_id, self._join_date)
        for period_key in ("current", "previous"):
            data     = analytics[period_key]
            row_info = self._analytics_rows[period_key]
            row_info["label"].setText(
                f"{bs_month_name(data['bs_month'])} {data['bs_year']}"
            )
            for key, val in [
                ("working_days", str(data["working_days"])),
                ("present",      str(data["present"])),
                ("absent",       str(data["absent"])),
                ("incomplete",   str(data["incomplete"])),
                ("holiday",      str(data["holiday"])),
            ]:
                row_info["stat_cards"][key].setText(val)

        history = get_subscription_history(student_id)
        self.sub_hist_table.setRowCount(len(history))
        for r, h in enumerate(history):
            sd = h["start_date"]; ed = h["end_date"]
            for c, val in enumerate([
                bs_str(sd) if hasattr(sd, "year") else str(sd),
                bs_str(ed) if hasattr(ed, "year") else str(ed),
                f"Rs. {h['total_fee']:,.0f}",
                f"Rs. {h['total_paid']:,.0f}",
                f"Rs. {h['balance']:,.0f}",
                h["status"].capitalize(),
                h["days_label"],
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                if c == 5:
                    fg = STATUS_PRESENT if h["status"] == "active" else STATUS_ABSENT
                    bg = STATUS_PRESENT_BG if h["status"] == "active" else STATUS_ABSENT_BG
                    item.setForeground(QColor(fg))
                    item.setBackground(QColor(bg))
                self.sub_hist_table.setItem(r, c, item)
            self.sub_hist_table.setRowHeight(r, 36)

        pays = get_all_payments_for_student(student_id)
        self.pay_table.setRowCount(len(pays))
        for r, p in enumerate(pays):
            d = p["date"]
            d_str = bs_str(d) if hasattr(d, "year") else str(d)
            for c, val in enumerate([
                d_str, f"Rs. {p['amount']:,.0f}", p["method"], p["note"],
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.pay_table.setItem(r, c, item)
            self.pay_table.setRowHeight(r, 36)

        self._load_exam_results(student_id)

    def _load_exam_results(self, student_id):
        while self._exam_results_layout.count():
            item = self._exam_results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        exam_data = [e for e in get_results_for_student(student_id)
                     if e["has_results"]]
        if not exam_data:
            empty = QLabel("No exam results yet.")
            empty.setStyleSheet(
                "font-size: 12px; color: #aaaaaa; padding: 12px;"
                "background: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px;"
            )
            self._exam_results_layout.addWidget(empty)
            return
        for exam in exam_data:
            exam_card = QFrame()
            exam_card.setStyleSheet(CARD_STYLE)
            ec_layout = QVBoxLayout(exam_card)
            ec_layout.setContentsMargins(0, 0, 0, 0)
            hdr_w = QWidget()
            hdr_w.setStyleSheet(
                "background: #2c2c2c; border-radius: 7px 7px 0 0; border: none;"
            )
            hdr_l = QHBoxLayout(hdr_w)
            hdr_l.setContentsMargins(16, 10, 16, 10)
            exam_name_lbl = QLabel(exam["exam"])
            exam_name_lbl.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #ffffff;"
                "background: transparent; border: none;"
            )
            pct_lbl = QLabel(
                f"{exam['percentage']}%  ({exam['total_scored']:.0f}"
                f" / {exam['total_full']:.0f})"
            )
            pct_lbl.setStyleSheet(
                "font-size: 12px; color: #cccccc; background: transparent; border: none;"
            )
            hdr_l.addWidget(exam_name_lbl); hdr_l.addStretch(); hdr_l.addWidget(pct_lbl)
            ec_layout.addWidget(hdr_w)
            tbl = QTableWidget()
            tbl.setColumnCount(5)
            tbl.setHorizontalHeaderLabels(
                ["Subject", "Full Marks", "Pass Marks", "Obtained", "Result"]
            )
            th = tbl.horizontalHeader()
            th.setSectionResizeMode(0, QHeaderView.Stretch)
            for i in range(1, 5):
                th.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            tbl.setEditTriggers(QTableWidget.NoEditTriggers)
            tbl.setAlternatingRowColors(True)
            tbl.setStyleSheet(TABLE_STYLE)
            tbl.verticalHeader().setVisible(False)
            tbl.setFrameShape(QFrame.NoFrame)
            tbl.setRowCount(len(exam["subjects"]))
            for r, sub_r in enumerate(exam["subjects"]):
                result_str = (
                    "Pass" if sub_r["passed"] is True  else
                    "Fail" if sub_r["passed"] is False else "—"
                )
                for c, val in enumerate([
                    sub_r["subject"], str(sub_r["full"]),
                    str(sub_r["pass"]),
                    str(sub_r["marks"]) if sub_r["marks"] is not None else "—",
                    result_str,
                ]):
                    item = QTableWidgetItem(val)
                    item.setForeground(Qt.black)
                    if c == 4 and sub_r["passed"] is not None:
                        item.setForeground(QColor(STATUS_PRESENT if sub_r["passed"] else STATUS_ABSENT))
                        item.setBackground(QColor(STATUS_PRESENT_BG if sub_r["passed"] else STATUS_ABSENT_BG))
                    tbl.setItem(r, c, item)
                tbl.setRowHeight(r, 36)
            tbl.setFixedHeight(40 + len(exam["subjects"]) * 36)
            ec_layout.addWidget(tbl)
            self._exam_results_layout.addWidget(exam_card)

    def _export_pdf(self):
        if not self._student_id:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Profile PDF",
            f"student_profile_{self._student_id}.pdf",
            "PDF Files (*.pdf)"
        )
        if path:
            centre = get_setting("centre_name", CENTRE_NAME)
            export_student_profile_pdf(self._student_id, path, centre)
            mb = QMessageBox(self)
            mb.setWindowTitle("Exported")
            mb.setText(f"Profile saved:\n{path}")
            apply_msgbox_style(mb)
            mb.exec_()

    def _go_back(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "_switch_page"):
                parent._switch_page(1)
                break
            parent = parent.parent()