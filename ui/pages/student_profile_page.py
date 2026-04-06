from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from calendar import month_name
from database.connection import get_session
from models.student import Student
from services.subscription_service import (
    get_active_subscription,
    get_subscription_history,
    get_all_payments_for_student,
)
from services.attendance_analytics_service import get_two_month_analytics
from services.exam_service import get_results_for_student
from services.export_service import export_student_profile_pdf
from services.settings_service import get_setting
from utils.bs_converter import bs_str
from ui.styles import (
    BTN_PRIMARY, BTN_SECONDARY, TABLE_STYLE, PAGE_TITLE_STYLE,
    CARD_STYLE, SECTION_LABEL_STYLE, PANEL_TITLE_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
    STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG,
)
from ui.event_bus import bus


class StudentProfilePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._student_id = None
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

        # Back + title + export
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

        # Two-column: info + subscription
        cols = QHBoxLayout()
        cols.setSpacing(16)
        self._info_card = self._build_info_card()
        self._sub_card  = self._build_sub_card()
        cols.addWidget(self._info_card, 1)
        cols.addWidget(self._sub_card,  1)
        self._layout.addLayout(cols)

        # Monthly attendance analytics
        att_analytics_lbl = QLabel("MONTHLY ATTENDANCE ANALYTICS")
        att_analytics_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(att_analytics_lbl)
        self._analytics_card = self._build_analytics_card()
        self._layout.addWidget(self._analytics_card)

        # Attendance history
        att_lbl = QLabel("ATTENDANCE HISTORY")
        att_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(att_lbl)

        att_frame = QFrame()
        att_frame.setStyleSheet(CARD_STYLE)
        att_cl = QVBoxLayout(att_frame)
        att_cl.setContentsMargins(0, 0, 0, 0)
        self.att_table = self._make_table(
            ["Date (BS)", "Entry", "Exit", "Status"], max_h=240
        )
        att_cl.addWidget(self.att_table)
        self._layout.addWidget(att_frame)

        # Exam results
        exam_lbl = QLabel("EXAMINATION RESULTS")
        exam_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(exam_lbl)
        self._exam_results_container = QWidget()
        self._exam_results_container.setStyleSheet(
            "background: transparent;"
        )
        self._exam_results_layout = QVBoxLayout(
            self._exam_results_container
        )
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
            ["Start (BS)", "End (BS)", "Fee", "Paid", "Balance", "Status"],
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

    # ── Card builders ─────────────────────────────────────────────────────────

    def _build_info_card(self):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        hdr = QLabel("Personal Details")
        hdr.setStyleSheet(PANEL_TITLE_STYLE)
        layout.addWidget(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #eeeeee; border: none;")
        layout.addWidget(sep)

        self._info_vals = {}
        for key in [
            "User ID", "Phone", "Address",
            "Date of Birth (BS)", "Join Date (BS)",
            "Class", "Group"
        ]:
            row = QHBoxLayout()
            k = QLabel(key + ":")
            k.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #666666;"
                "background: transparent; min-width: 130px; border: none;"
            )
            k.setFixedWidth(145)
            v = QLabel("—")
            v.setStyleSheet(
                "font-size: 13px; color: #1a1a1a; background: transparent;"
                "border: none;"
            )
            v.setWordWrap(True)
            row.addWidget(k)
            row.addWidget(v)
            row.addStretch()
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

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #eeeeee; border: none;")
        layout.addWidget(sep)

        self._sub_vals = {}
        for key in [
            "Start Date (BS)", "End Date (BS)", "Days Left",
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
                "font-size: 13px; color: #1a1a1a; background: transparent;"
                "border: none;"
            )
            row.addWidget(k)
            row.addWidget(v)
            row.addStretch()
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

        # Two rows: current month + previous month
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
                ("working_days", "Working Days", "#333333", "#f0f0f0"),
                ("present",      "Present",      STATUS_PRESENT,    STATUS_PRESENT_BG),
                ("absent",       "Absent",       STATUS_ABSENT,     STATUS_ABSENT_BG),
                ("incomplete",   "Incomplete",   "#7a4f00",         "#fdf3e0"),
                ("holiday",      "Holiday",      "#555555",         "#eeeeee"),
            ]:
                mini = QFrame()
                mini.setStyleSheet(f"""
                    QFrame {{
                        background: {bg};
                        border: 1px solid #e0e0e0;
                        border-radius: 6px;
                    }}
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
                inner.addWidget(t)
                inner.addWidget(v)
                cards_row.addWidget(mini)
                stat_cards[key] = v

            layout.addLayout(cards_row)
            self._analytics_rows[period] = {
                "label":      period_lbl,
                "stat_cards": stat_cards,
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

    # ── Load data ─────────────────────────────────────────────────────────────

    def load_student(self, student_id):
        if student_id < 0:
            return
        self._student_id = student_id

        session = get_session()
        s = session.query(Student).get(student_id)
        if not s:
            session.close()
            return

        self._name_label.setText(s.name)

        self._info_vals["User ID"].setText(s.user_id)
        self._info_vals["Phone"].setText(s.phone or "—")
        self._info_vals["Address"].setText(s.address or "—")
        self._info_vals["Date of Birth (BS)"].setText(
            bs_str(s.dob) if s.dob else "—"
        )
        self._info_vals["Join Date (BS)"].setText(
            bs_str(s.join_date) if s.join_date else "—"
        )
        self._info_vals["Class"].setText(
            s.class_.name if s.class_ else "—"
        )
        self._info_vals["Group"].setText(
            s.group.name if s.group else "—"
        )

        # Attendance table
        atts = sorted(s.attendances, key=lambda a: a.date, reverse=True)
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

        # Active subscription
        sub = get_active_subscription(student_id)
        if sub:
            self._sub_vals["Start Date (BS)"].setText(
                bs_str(sub["start_date"])
            )
            self._sub_vals["End Date (BS)"].setText(
                bs_str(sub["end_date"])
            )
            self._sub_vals["Days Left"].setText(f"{sub['days_left']} days")
            self._sub_vals["Total Fee"].setText(
                f"Rs. {sub['total_fee']:,.0f}"
            )
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
                "font-size: 13px; color: #888888; background: transparent;"
                "border: none;"
            )

        # Monthly attendance analytics
        analytics = get_two_month_analytics(student_id)
        for period_key in ("current", "previous"):
            data = analytics[period_key]
            row_info = self._analytics_rows[period_key]
            mn = month_name[data["month"]]
            row_info["label"].setText(
                f"{mn} {data['year']}"
            )
            for key, val in [
                ("working_days", str(data["working_days"])),
                ("present",      str(data["present"])),
                ("absent",       str(data["absent"])),
                ("incomplete",   str(data["incomplete"])),
                ("holiday",      str(data["holiday"])),
            ]:
                row_info["stat_cards"][key].setText(val)

        # Subscription history
        history = get_subscription_history(student_id)
        self.sub_hist_table.setRowCount(len(history))
        for r, h in enumerate(history):
            sd = h["start_date"]
            ed = h["end_date"]
            for c, val in enumerate([
                bs_str(sd) if hasattr(sd, "year") else str(sd),
                bs_str(ed) if hasattr(ed, "year") else str(ed),
                f"Rs. {h['total_fee']:,.0f}",
                f"Rs. {h['total_paid']:,.0f}",
                f"Rs. {h['balance']:,.0f}",
                h["status"].capitalize(),
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                if c == 5:
                    fg = (STATUS_PRESENT if h["status"] == "active"
                          else STATUS_ABSENT)
                    bg = (STATUS_PRESENT_BG if h["status"] == "active"
                          else STATUS_ABSENT_BG)
                    item.setForeground(QColor(fg))
                    item.setBackground(QColor(bg))
                self.sub_hist_table.setItem(r, c, item)
            self.sub_hist_table.setRowHeight(r, 36)

        # Payment history
        pays = get_all_payments_for_student(student_id)
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
            self.pay_table.setRowHeight(r, 36)

        # Exam results
        self._load_exam_results(student_id)

    def _load_exam_results(self, student_id):
        # Clear previous
        while self._exam_results_layout.count():
            item = self._exam_results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        exam_data = get_results_for_student(student_id)

        if not exam_data:
            empty = QLabel("No exam results yet.")
            empty.setStyleSheet(
                "font-size: 12px; color: #aaaaaa; padding: 12px;"
                "background: #ffffff; border: 1px solid #e0e0e0;"
                "border-radius: 6px;"
            )
            self._exam_results_layout.addWidget(empty)
            return

        for exam in exam_data:
            # Exam card
            exam_card = QFrame()
            exam_card.setStyleSheet(CARD_STYLE)
            ec_layout = QVBoxLayout(exam_card)
            ec_layout.setContentsMargins(0, 0, 0, 0)
            ec_layout.setSpacing(0)

            # Exam header
            hdr_w = QWidget()
            hdr_w.setStyleSheet(
                "background: #2c2c2c; border-radius: 7px 7px 0 0;"
                "border: none;"
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
                if exam["has_results"] else "No marks entered"
            )
            pct_lbl.setStyleSheet(
                "font-size: 12px; color: #cccccc;"
                "background: transparent; border: none;"
            )
            hdr_l.addWidget(exam_name_lbl)
            hdr_l.addStretch()
            hdr_l.addWidget(pct_lbl)
            ec_layout.addWidget(hdr_w)

            # Subjects table
            tbl = QTableWidget()
            tbl.setColumnCount(5)
            tbl.setHorizontalHeaderLabels(
                ["Subject", "Full Marks", "Pass Marks",
                 "Obtained", "Result"]
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
                    "Fail" if sub_r["passed"] is False else
                    "—"
                )
                obtained_str = (
                    str(sub_r["marks"]) if sub_r["marks"] is not None
                    else "—"
                )
                for c, val in enumerate([
                    sub_r["subject"],
                    str(sub_r["full"]),
                    str(sub_r["pass"]),
                    obtained_str,
                    result_str,
                ]):
                    item = QTableWidgetItem(val)
                    item.setForeground(Qt.black)
                    if c == 4 and sub_r["passed"] is not None:
                        if sub_r["passed"]:
                            item.setForeground(QColor(STATUS_PRESENT))
                            item.setBackground(QColor(STATUS_PRESENT_BG))
                        else:
                            item.setForeground(QColor(STATUS_ABSENT))
                            item.setBackground(QColor(STATUS_ABSENT_BG))
                    tbl.setItem(r, c, item)
                tbl.setRowHeight(r, 36)

            row_count = len(exam["subjects"])
            tbl.setFixedHeight(40 + row_count * 36)
            ec_layout.addWidget(tbl)
            self._exam_results_layout.addWidget(exam_card)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _export_pdf(self):
        if not self._student_id:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Profile PDF",
            f"student_profile_{self._student_id}.pdf",
            "PDF Files (*.pdf)"
        )
        if path:
            centre = get_setting("centre_name", "Tuition Centre")
            export_student_profile_pdf(self._student_id, path, centre)
            QMessageBox.information(
                self, "Exported", f"Profile saved:\n{path}"
            )

    def _go_back(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "_switch_page"):
                parent._switch_page(1)
                break
            parent = parent.parent()