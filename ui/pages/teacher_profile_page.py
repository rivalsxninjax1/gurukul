from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QScrollArea, QDialog, QLineEdit, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QColor, QDesktopServices
from database.connection import get_session
from models.teacher import Teacher
from models.attendance import TeacherAttendance
from models.schedule import Schedule
from utils.bs_converter import bs_str, ad_to_bs, today_bs_tuple
from services.attendance_analytics_service import (
    bs_month_name, get_teacher_monthly_analytics
)
from services.export_service import export_teacher_profile_pdf
from services.settings_service import get_setting
from ui.styles import (
    BTN_PRIMARY, BTN_PRINT, BTN_SECONDARY, TABLE_STYLE, PAGE_TITLE_STYLE,
    CARD_STYLE, SECTION_LABEL_STYLE, PANEL_TITLE_STYLE,
    FORM_LABEL_STYLE, INPUT_STYLE, DIALOG_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
    apply_msgbox_style,
)
from ui.event_bus import bus
from ui.widgets import Toast
from datetime import date

CENTRE_NAME    = "GURUKUL ACADEMY AND TRAINING CENTER"
CENTRE_ADDRESS = "Biratnagar-1, Bhatta Chowk"


class TeacherProfilePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._teacher_id = None
        self._join_date  = None
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

        # Back
        top = QHBoxLayout()
        back = QPushButton("← Back to Teachers")
        back.setStyleSheet(BTN_SECONDARY)
        back.clicked.connect(self._go_back)
        top.addWidget(back)
        top.addStretch()
        print_btn = QPushButton("🖨  Print Profile")
        print_btn.setStyleSheet(BTN_PRINT)
        print_btn.clicked.connect(self._print_profile)
        top.addWidget(print_btn)
        top.addSpacing(8)

        export_btn = QPushButton("⬇  Download PDF")
        export_btn.setStyleSheet(BTN_PRIMARY)
        export_btn.clicked.connect(self._export_pdf)
        top.addWidget(export_btn)
        self._layout.addLayout(top)

        self._name_label = QLabel("Teacher Profile")
        self._name_label.setStyleSheet(PAGE_TITLE_STYLE)
        self._layout.addWidget(self._name_label)

        self.toast = Toast()
        self._layout.addWidget(self.toast)

        # Personal details card
        details_card = QFrame()
        details_card.setStyleSheet(CARD_STYLE)
        dcl = QVBoxLayout(details_card)
        dcl.setContentsMargins(20, 16, 20, 16)
        dcl.setSpacing(10)

        hdr_row = QHBoxLayout()
        hdr_lbl = QLabel("Personal Details")
        hdr_lbl.setStyleSheet(PANEL_TITLE_STYLE)
        self.edit_details_btn = QPushButton("Edit Details")
        self.edit_details_btn.setStyleSheet(BTN_SECONDARY)
        self.edit_details_btn.clicked.connect(self._edit_details)
        self.edit_id_btn = QPushButton("Edit Teacher ID")
        self.edit_id_btn.setStyleSheet(BTN_SECONDARY)
        self.edit_id_btn.clicked.connect(self._edit_id)
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()
        hdr_row.addWidget(self.edit_details_btn)
        hdr_row.addSpacing(6)
        hdr_row.addWidget(self.edit_id_btn)
        dcl.addLayout(hdr_row)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1); sep.setStyleSheet("background: #eeeeee; border: none;")
        dcl.addWidget(sep)

        self._info_vals = {}
        for key in [
            "Teacher ID", "Phone", "Subject",
            "Address", "Join Date (BS)"
        ]:
            row = QHBoxLayout()
            k = QLabel(key + ":")
            k.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #666666;"
                "background: transparent; min-width: 110px; border: none;"
            )
            k.setFixedWidth(130)
            v = QLabel("—")
            v.setStyleSheet(
                "font-size: 13px; color: #1a1a1a; background: transparent; border: none;"
            )
            v.setWordWrap(True)
            row.addWidget(k); row.addWidget(v); row.addStretch()
            dcl.addLayout(row)
            self._info_vals[key] = v

        self._layout.addWidget(details_card)

        # ── Monthly attendance analytics ──────────────────────────────────────
        att_analytics_lbl = QLabel("MONTHLY ATTENDANCE ANALYTICS")
        att_analytics_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(att_analytics_lbl)
        self._analytics_card = self._build_analytics_card()
        self._layout.addWidget(self._analytics_card)

        # ── Attendance history ────────────────────────────────────────────────
        att_lbl = QLabel("ATTENDANCE HISTORY")
        att_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(att_lbl)

        att_frame = QFrame()
        att_frame.setStyleSheet(CARD_STYLE)
        att_cl = QVBoxLayout(att_frame)
        att_cl.setContentsMargins(0, 0, 0, 0)

        self.att_table = QTableWidget()
        self.att_table.setColumnCount(4)
        self.att_table.setHorizontalHeaderLabels(
            ["Date (BS)", "Entry Time", "Exit Time", "Status"]
        )
        ah = self.att_table.horizontalHeader()
        ah.setSectionResizeMode(0, QHeaderView.Stretch)
        ah.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        ah.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        ah.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.att_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.att_table.setAlternatingRowColors(True)
        self.att_table.setStyleSheet(TABLE_STYLE)
        self.att_table.verticalHeader().setVisible(False)
        self.att_table.setFrameShape(QFrame.NoFrame)
        self.att_table.setMaximumHeight(260)
        att_cl.addWidget(self.att_table)
        self._layout.addWidget(att_frame)

        # ── Schedule ──────────────────────────────────────────────────────────
        sch_lbl = QLabel("ASSIGNED SCHEDULE")
        sch_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(sch_lbl)

        sch_frame = QFrame()
        sch_frame.setStyleSheet(CARD_STYLE)
        sch_cl = QVBoxLayout(sch_frame)
        sch_cl.setContentsMargins(0, 0, 0, 0)

        self.sch_table = QTableWidget()
        self.sch_table.setColumnCount(5)
        self.sch_table.setHorizontalHeaderLabels(
            ["Day", "Class", "Group", "Subject", "Time"]
        )
        sh = self.sch_table.horizontalHeader()
        for i in range(5):
            sh.setSectionResizeMode(i, QHeaderView.Stretch)
        self.sch_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sch_table.setAlternatingRowColors(True)
        self.sch_table.setStyleSheet(TABLE_STYLE)
        self.sch_table.verticalHeader().setVisible(False)
        self.sch_table.setFrameShape(QFrame.NoFrame)
        self.sch_table.setMaximumHeight(200)
        sch_cl.addWidget(self.sch_table)
        self._layout.addWidget(sch_frame)

        self._layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _build_analytics_card(self):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        info_lbl = QLabel("Analytics reflect the BS month this teacher joined.")
        info_lbl.setStyleSheet(
            "font-size: 11px; color: #777777; background: transparent; border: none;"
        )
        layout.addWidget(info_lbl)

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
        self._analytics_section = {
            "label": period_lbl,
            "stat_cards": stat_cards,
        }
        return card

    def _resolve_join_bs_month(self):
        if self._join_date:
            bs = ad_to_bs(self._join_date)
        else:
            bs = today_bs_tuple()
        if not bs or bs[0] is None:
            bs = today_bs_tuple()
        return bs[0], bs[1]

    def _update_analytics_view(self, analytics: dict | None):
        section = getattr(self, "_analytics_section", None)
        if not section:
            return
        if analytics and analytics.get("bs_year"):
            section["label"].setText(
                f"{bs_month_name(analytics['bs_month'])} {analytics['bs_year']}"
            )
        else:
            section["label"].setText("—")
        for key in ["working_days", "present", "absent", "incomplete", "holiday"]:
            val = analytics.get(key) if analytics else None
            section["stat_cards"][key].setText(str(val if val is not None else 0))

    def load_teacher(self, teacher_id):
        if teacher_id < 0:
            return
        self._teacher_id = teacher_id

        session = get_session()
        t = session.query(Teacher).get(teacher_id)
        if not t:
            session.close()
            return

        self._join_date = t.join_date
        self._name_label.setText(t.name)
        self._info_vals["Teacher ID"].setText(t.user_id)
        self._info_vals["Phone"].setText(t.phone or "—")
        self._info_vals["Subject"].setText(t.subject or "—")
        self._info_vals["Address"].setText(t.address or "—")
        self._info_vals["Join Date (BS)"].setText(
            bs_str(t.join_date) if t.join_date else "—"
        )

        # Attendance history
        atts = sorted(t.attendances, key=lambda a: a.date, reverse=True)
        if self._join_date:
            atts = [a for a in atts if a.date >= self._join_date]
        self.att_table.setRowCount(len(atts))
        for r, att in enumerate(atts):
            vals = [
                bs_str(att.date),
                str(att.entry_time) if att.entry_time else "—",
                str(att.exit_time)  if att.exit_time  else "—",
                att.status or "Present",
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
                self.att_table.setItem(r, c, item)
            self.att_table.setRowHeight(r, 36)

        # Schedule
        scheds = session.query(Schedule).filter_by(
            teacher_id=teacher_id
        ).all()
        sch_rows = [{
            "day":     s.day_of_week,
            "class":   s.class_.name  if s.class_  else "—",
            "group":   s.group.name   if s.group   else "—",
            "subject": s.subject or "—",
            "time":    f"{s.start_time}  –  {s.end_time}",
        } for s in scheds]
        session.close()

        self.sch_table.setRowCount(len(sch_rows))
        for r, sr in enumerate(sch_rows):
            for c, val in enumerate([
                sr["day"], sr["class"], sr["group"],
                sr["subject"], sr["time"]
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.sch_table.setItem(r, c, item)
            self.sch_table.setRowHeight(r, 36)

        # Monthly attendance analytics (join month only)
        by, bm = self._resolve_join_bs_month()
        analytics = get_teacher_monthly_analytics(
            teacher_id, by, bm, self._join_date
        )
        self._update_analytics_view(analytics)

    def _edit_details(self):
        if not self._teacher_id:
            return
        from ui.pages.teachers_page import TeacherDialog
        dlg = TeacherDialog(teacher_id=self._teacher_id, parent=self)
        if dlg.exec_():
            self.toast.success("Teacher details updated.")
            self.load_teacher(self._teacher_id)

    def _edit_id(self):
        if not self._teacher_id:
            return
        session = get_session()
        t = session.query(Teacher).get(self._teacher_id)
        current_id = t.user_id if t else ""
        session.close()

        dlg = EditIDDialog("Edit Teacher ID", current_id, parent=self)
        if dlg.exec_():
            new_id = dlg.get_value()
            if not new_id:
                return
            session = get_session()
            dup = session.query(Teacher).filter(
                Teacher.user_id == new_id,
                Teacher.id      != self._teacher_id
            ).first()
            if dup:
                mb = QMessageBox(self)
                mb.setWindowTitle("Duplicate")
                mb.setText(f"Teacher ID '{new_id}' is already in use.")
                apply_msgbox_style(mb)
                mb.exec_()
                session.close()
                return
            t = session.query(Teacher).get(self._teacher_id)
            if t:
                t.user_id = new_id
                session.commit()
                self._info_vals["Teacher ID"].setText(new_id)
                self.toast.success("Teacher ID updated.")
            session.close()

    def _print_profile(self):
        if not self._teacher_id:
            return
        import tempfile

        centre_name, centre_address = self._centre_meta()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_path = tmp.name
        tmp.close()

        mb = QMessageBox(self)
        try:
            export_teacher_profile_pdf(
                self._teacher_id, tmp_path, centre_name, centre_address
            )
        except Exception as exc:
            mb.setWindowTitle("Error")
            mb.setText(f"Failed to prepare PDF:\n{exc}")
            apply_msgbox_style(mb)
            mb.exec_()
            return

        opened = self._open_pdf(tmp_path)
        if opened:
            mb.setWindowTitle("Profile Ready")
            mb.setText("Profile PDF opened in your default viewer.\nPlease print it from there.")
        else:
            mb.setWindowTitle("Viewer Unavailable")
            mb.setText(
                "Couldn't open the profile PDF automatically.\n"
                "Please use Download PDF instead."
            )
        apply_msgbox_style(mb)
        mb.exec_()

    def _export_pdf(self):
        if not self._teacher_id:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Download Profile PDF",
            f"teacher_profile_{self._teacher_id}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return
        centre_name, centre_address = self._centre_meta()
        mb = QMessageBox(self)
        try:
            export_teacher_profile_pdf(
                self._teacher_id, path, centre_name, centre_address
            )
        except Exception as exc:
            mb.setWindowTitle("Error")
            mb.setText(f"Failed to save PDF:\n{exc}")
        else:
            mb.setWindowTitle("Downloaded")
            mb.setText(f"Profile saved:\n{path}")
        apply_msgbox_style(mb)
        mb.exec_()

    def _centre_meta(self):
        name = get_setting("centre_name", CENTRE_NAME)
        addr = get_setting("centre_address", CENTRE_ADDRESS)
        return name or CENTRE_NAME, addr or CENTRE_ADDRESS
    def _open_pdf(self, pdf_path: str) -> bool:
        url = QUrl.fromLocalFile(pdf_path)
        return QDesktopServices.openUrl(url)

    def _go_back(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "_switch_page"):
                parent._switch_page(2)
                break
            parent = parent.parent()


class EditIDDialog(QDialog):
    def __init__(self, title, current_value, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(360)
        self.setStyleSheet(DIALOG_STYLE)
        self.setSizeGripEnabled(False)
        self._build_ui(current_value)

    def _build_ui(self, current_value):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(28, 28, 28, 20)
        fl.setSpacing(12)

        lbl = QLabel("New Teacher ID:")
        lbl.setStyleSheet(FORM_LABEL_STYLE)
        fl.addWidget(lbl)

        self.input = QLineEdit(current_value)
        self.input.setStyleSheet(INPUT_STYLE)
        self.input.setFixedHeight(36)
        self.input.returnPressed.connect(self.accept)
        fl.addWidget(self.input)
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
        save = QPushButton("Save")
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self.accept)
        br.addWidget(cancel)
        br.addSpacing(10)
        br.addWidget(save)
        root.addWidget(footer)

    def get_value(self):
        return self.input.text().strip()
