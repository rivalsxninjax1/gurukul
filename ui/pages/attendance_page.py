from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QDialog,
    QMessageBox, QHeaderView, QComboBox, QFrame, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
import pandas as pd
from services.attendance_service import import_attendance_excel
from database.connection import get_session
from models.attendance import Attendance, TeacherAttendance
from models.class_group import Class, Group
from utils.bs_converter import bs_str
from ui.bs_widgets import BSDateEdit
from ui.styles import (
    BTN_PRIMARY, BTN_SECONDARY, TABLE_STYLE, COMBO_STYLE,
    DIALOG_STYLE, FORM_LABEL_STYLE, PAGE_TITLE_STYLE,
    CARD_STYLE, SECTION_LABEL_STYLE, TAB_STYLE,
    STATUS_PRESENT, STATUS_INCOMPLETE, STATUS_ABSENT,
    STATUS_PRESENT_BG, STATUS_INCOMPLETE_BG, STATUS_ABSENT_BG
)
from ui.event_bus import bus
from ui.widgets import LoadingOverlay, Toast


class ImportWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, filepath, col_map):
        super().__init__()
        self.filepath = filepath
        self.col_map  = col_map

    def run(self):
        self.finished.emit(
            import_attendance_excel(self.filepath, self.col_map)
        )


class AttendancePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._last_file    = None
        self._last_col_map = None
        self._build_ui()
        self.refresh_tables()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("Attendance")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        self.last_file_lbl = QLabel("No file imported yet")
        self.last_file_lbl.setStyleSheet(
            "font-size: 11px; color: #999999; background: transparent;"
        )
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(self.last_file_lbl)
        layout.addLayout(title_row)

        self.toast = Toast()
        layout.addWidget(self.toast)

        # Filter card
        filter_card = QFrame()
        filter_card.setStyleSheet(CARD_STYLE)
        fl = QHBoxLayout(filter_card)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(12)

        def lbl(t):
            l = QLabel(t)
            l.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #333333;"
                "background: transparent; border: none;"
            )
            return l

        # BS date filter — defaults to today
        self.date_filter = BSDateEdit()
        self.date_filter.set_today()
        self.date_filter.dateChanged.connect(
            lambda _: self.refresh_tables()
        )

        # Class filter
        session = get_session()
        classes = [(c.id, c.name) for c in session.query(Class).all()]
        session.close()

        self.class_filter = QComboBox()
        self.class_filter.setStyleSheet(COMBO_STYLE)
        self.class_filter.setFixedHeight(36)
        self.class_filter.setFixedWidth(150)
        self.class_filter.addItem("All Classes", None)
        for cid, cname in classes:
            self.class_filter.addItem(cname, cid)
        self.class_filter.currentIndexChanged.connect(
            self._reload_group_filter
        )
        self.class_filter.currentIndexChanged.connect(self.refresh_tables)

        self.group_filter = QComboBox()
        self.group_filter.setStyleSheet(COMBO_STYLE)
        self.group_filter.setFixedHeight(36)
        self.group_filter.setFixedWidth(150)
        self.group_filter.addItem("All Groups", None)
        self.group_filter.currentIndexChanged.connect(self.refresh_tables)

        self.badge_present    = self._badge(
            "Present: 0", STATUS_PRESENT, STATUS_PRESENT_BG)
        self.badge_incomplete = self._badge(
            "Incomplete: 0", STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG)
        self.badge_absent     = self._badge(
            "Absent: 0", STATUS_ABSENT, STATUS_ABSENT_BG)

        import_btn = QPushButton("Import Excel")
        import_btn.setStyleSheet(BTN_PRIMARY)
        import_btn.clicked.connect(self.open_import_dialog)

        fl.addWidget(lbl("Date (BS):"))
        fl.addWidget(self.date_filter)
        fl.addWidget(lbl("Class:"))
        fl.addWidget(self.class_filter)
        fl.addWidget(lbl("Group:"))
        fl.addWidget(self.group_filter)
        fl.addSpacing(8)
        fl.addWidget(self.badge_present)
        fl.addWidget(self.badge_incomplete)
        fl.addWidget(self.badge_absent)
        fl.addStretch()
        fl.addWidget(import_btn)
        layout.addWidget(filter_card)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TAB_STYLE)
        self.tabs.addTab(self._build_student_tab(), "Student Attendance")
        self.tabs.addTab(self._build_teacher_tab(), "Teacher Attendance")
        layout.addWidget(self.tabs)

        self.overlay = LoadingOverlay(self)

    def _build_student_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: #ffffff;")
        tl = QVBoxLayout(tab)
        tl.setContentsMargins(0, 0, 0, 0)

        self.student_table = QTableWidget()
        self.student_table.setColumnCount(6)
        self.student_table.setHorizontalHeaderLabels([
            "User ID", "Student Name", "Date (BS)",
            "Entry Time", "Exit Time", "Status"
        ])
        hh = self.student_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.student_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.student_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.student_table.setAlternatingRowColors(True)
        self.student_table.setStyleSheet(TABLE_STYLE)
        self.student_table.verticalHeader().setVisible(False)
        self.student_table.setFrameShape(QFrame.NoFrame)
        tl.addWidget(self.student_table)
        return tab

    def _build_teacher_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: #ffffff;")
        tl = QVBoxLayout(tab)
        tl.setContentsMargins(0, 0, 0, 0)

        self.teacher_table = QTableWidget()
        self.teacher_table.setColumnCount(5)
        self.teacher_table.setHorizontalHeaderLabels([
            "Teacher ID", "Teacher Name",
            "Date (BS)", "Entry Time", "Exit Time"
        ])
        th = self.teacher_table.horizontalHeader()
        th.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(1, QHeaderView.Stretch)
        th.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        th.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.teacher_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.teacher_table.setAlternatingRowColors(True)
        self.teacher_table.setStyleSheet(TABLE_STYLE)
        self.teacher_table.verticalHeader().setVisible(False)
        self.teacher_table.setFrameShape(QFrame.NoFrame)
        tl.addWidget(self.teacher_table)
        return tab

    def _badge(self, text, fg, bg):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {fg};"
            f"background: {bg}; border-radius: 4px; padding: 4px 12px;"
            "border: none;"
        )
        return lbl

    def _reload_group_filter(self):
        class_id = self.class_filter.currentData()
        self.group_filter.blockSignals(True)
        self.group_filter.clear()
        self.group_filter.addItem("All Groups", None)
        if class_id:
            session = get_session()
            groups = session.query(Group).filter_by(class_id=class_id).all()
            for g in groups:
                self.group_filter.addItem(g.name, g.id)
            session.close()
        self.group_filter.blockSignals(False)

    def refresh_tables(self):
        self._refresh_student_table()
        self._refresh_teacher_table()

    def _refresh_student_table(self):
        sel_date = self.date_filter.get_ad_date()
        if not sel_date:
            return
        class_id = self.class_filter.currentData()
        group_id = self.group_filter.currentData()

        session  = get_session()
        records  = session.query(Attendance).filter_by(date=sel_date).all()
        rows = []
        for att in records:
            s = att.student
            if not s:
                continue
            if class_id and s.class_id != class_id:
                continue
            if group_id and s.group_id != group_id:
                continue
            rows.append({
                "uid":    s.user_id,
                "name":   s.name,
                "date":   bs_str(att.date),
                "entry":  str(att.entry_time) if att.entry_time else "—",
                "exit":   str(att.exit_time)  if att.exit_time  else "—",
                "status": att.status or "",
            })
        session.close()

        present    = sum(1 for r in rows if r["status"] == "Present")
        incomplete = sum(1 for r in rows if r["status"] == "Incomplete")
        absent     = sum(1 for r in rows if r["status"] == "Absent")
        self.badge_present.setText(f"Present: {present}")
        self.badge_incomplete.setText(f"Incomplete: {incomplete}")
        self.badge_absent.setText(f"Absent: {absent}")

        self.student_table.setRowCount(len(rows))
        for row, r in enumerate(rows):
            for col, val in enumerate([
                r["uid"], r["name"], r["date"], r["entry"], r["exit"]
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.student_table.setItem(row, col, item)

            si = QTableWidgetItem(r["status"])
            if r["status"] == "Present":
                si.setForeground(QColor(STATUS_PRESENT))
                si.setBackground(QColor(STATUS_PRESENT_BG))
            elif r["status"] == "Incomplete":
                si.setForeground(QColor(STATUS_INCOMPLETE))
                si.setBackground(QColor(STATUS_INCOMPLETE_BG))
            elif r["status"] == "Absent":
                si.setForeground(QColor(STATUS_ABSENT))
                si.setBackground(QColor(STATUS_ABSENT_BG))
            else:
                si.setForeground(Qt.black)
            self.student_table.setItem(row, 5, si)
            self.student_table.setRowHeight(row, 40)

    def _refresh_teacher_table(self):
        sel_date = self.date_filter.get_ad_date()
        if not sel_date:
            return
        session  = get_session()
        records  = session.query(TeacherAttendance).filter_by(
            date=sel_date
        ).all()
        rows = []
        for att in records:
            t = att.teacher
            rows.append({
                "uid":   t.user_id if t else "—",
                "name":  t.name    if t else "Unknown",
                "date":  bs_str(att.date),
                "entry": str(att.entry_time) if att.entry_time else "—",
                "exit":  str(att.exit_time)  if att.exit_time  else "—",
            })
        session.close()

        self.teacher_table.setRowCount(len(rows))
        for row, r in enumerate(rows):
            for col, val in enumerate([
                r["uid"], r["name"], r["date"], r["entry"], r["exit"]
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.teacher_table.setItem(row, col, item)
            self.teacher_table.setRowHeight(row, 40)

    # ── Import flow ───────────────────────────────────────────────────────────

    def open_import_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Attendance Excel", "",
            "Excel Files (*.xlsx *.xls)"
        )
        if not filepath:
            return
        try:
            df      = pd.read_excel(filepath)
            columns = list(df.columns)
        except Exception as e:
            QMessageBox.critical(self, "File Error",
                                 f"Cannot read file:\n{e}")
            return

        map_dlg = ColumnMapDialog(columns, parent=self)
        if not map_dlg.exec_():
            return
        col_map = map_dlg.get_mapping()

        preview_dlg = PreviewDialog(filepath, col_map, parent=self)
        if not preview_dlg.exec_():
            return

        self._last_file    = filepath
        self._last_col_map = col_map
        self.overlay.show_with_text("Importing attendance…")

        self.worker = ImportWorker(filepath, col_map)
        self.worker.finished.connect(self._on_import_done)
        self.worker.start()

    def _on_import_done(self, result):
        self.overlay.hide()
        fname = (self._last_file.split("/")[-1]
                 if self._last_file else "")
        self.last_file_lbl.setText(f"Last import: {fname}")

        if result["success"] > 0:
            self.toast.success(
                f"Imported {result['success']} record(s) successfully."
            )
        else:
            self.toast.info("No new records imported.")

        if result["errors"]:
            lines = "\n".join(result["errors"][:6])
            QMessageBox.warning(
                self, "Import Warnings",
                f"{len(result['errors'])} error(s):\n{lines}"
            )
        if result["unknown_ids"]:
            QMessageBox.information(
                self, "Unknown IDs",
                "These IDs had no matching student or teacher:\n"
                + ", ".join(result["unknown_ids"][:15])
            )

        self.refresh_tables()
        bus.attendance_imported.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.resize(self.size())


# ── Column map dialog ─────────────────────────────────────────────────────────

class ColumnMapDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Step 1 — Map Columns")
        self.setMinimumWidth(460)
        self.setStyleSheet(DIALOG_STYLE)
        self.setSizeGripEnabled(True)
        self.columns  = columns
        self._mapping = None
        self._build_ui()

    def _build_ui(self):
        from PyQt5.QtWidgets import QScrollArea
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(28, 28, 28, 16)
        fl.setSpacing(14)

        hdr = QLabel("Map your Excel columns")
        hdr.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #1a1a1a;"
            "background: transparent;"
        )
        fl.addWidget(hdr)

        info = QLabel(
            "Format 1:  user_id + timestamp (single combined column)\n"
            "Format 2:  user_id + date + time (two separate columns)\n\n"
            "IDs starting with 'T' → Teacher attendance.\n"
            "Timestamps are in AD — system displays them in BS."
        )
        info.setStyleSheet(
            "font-size: 12px; color: #555555; background: #f8f8f8;"
            "border: 1px solid #e8e8e8; border-radius: 5px; padding: 10px;"
        )
        info.setWordWrap(True)
        fl.addWidget(info)

        NA = "— Not Used —"

        def mk_combo():
            c = QComboBox()
            c.setStyleSheet(COMBO_STYLE)
            c.setFixedHeight(36)
            return c

        def row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(FORM_LABEL_STYLE)
            fl.addWidget(lbl)
            fl.addWidget(widget)

        self.uid_combo  = mk_combo()
        self.uid_combo.addItems(self.columns)
        self.ts_combo   = mk_combo()
        self.ts_combo.addItem(NA)
        self.ts_combo.addItems(self.columns)
        self.date_combo = mk_combo()
        self.date_combo.addItem(NA)
        self.date_combo.addItems(self.columns)
        self.time_combo = mk_combo()
        self.time_combo.addItem(NA)
        self.time_combo.addItems(self.columns)

        for i, col in enumerate(self.columns):
            cl = col.lower().strip()
            if cl in ("user_id", "userid", "id", "student_id", "employee_id"):
                self.uid_combo.setCurrentIndex(i)
            if cl in ("timestamp", "datetime", "punch_time", "date_time"):
                self.ts_combo.setCurrentIndex(i + 1)
            if cl == "date":
                self.date_combo.setCurrentIndex(i + 1)
            if cl in ("time", "clock_time"):
                self.time_combo.setCurrentIndex(i + 1)

        row("User ID column  *",            self.uid_combo)
        row("Timestamp column (Format 1)",  self.ts_combo)
        row("Date column (Format 2)",       self.date_combo)
        row("Time column (Format 2)",       self.time_combo)
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
        ok = QPushButton("Next: Preview →")
        ok.setStyleSheet(BTN_PRIMARY)
        ok.clicked.connect(self._confirm)
        br.addWidget(cancel)
        br.addSpacing(10)
        br.addWidget(ok)
        root.addWidget(footer)

    def _confirm(self):
        NA  = "— Not Used —"
        uid = self.uid_combo.currentText()
        ts  = self.ts_combo.currentText()
        dt  = self.date_combo.currentText()
        tm  = self.time_combo.currentText()

        if ts != NA:
            self._mapping = {"user_id": uid, "timestamp": ts}
        elif dt != NA and tm != NA:
            self._mapping = {"user_id": uid, "date": dt, "time": tm}
        else:
            QMessageBox.warning(
                self, "Incomplete Mapping",
                "Select either a Timestamp column,\n"
                "OR both a Date AND a Time column."
            )
            return
        self.accept()

    def get_mapping(self):
        return self._mapping


# ── Preview dialog ────────────────────────────────────────────────────────────

class PreviewDialog(QDialog):
    def __init__(self, filepath, col_map, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Step 2 — Preview & Confirm")
        self.setMinimumSize(720, 480)
        self.setStyleSheet(DIALOG_STYLE)
        self.setSizeGripEnabled(True)
        self._errors = []
        self._rows   = []
        self._parse(filepath, col_map)
        self._build_ui()

    def _parse(self, filepath, col_map):
        try:
            df = pd.read_excel(filepath)
        except Exception as e:
            self._errors.append(f"Cannot read file: {e}")
            return

        uid_col = col_map.get("user_id", "user_id")
        if uid_col not in df.columns:
            self._errors.append(f"Column '{uid_col}' not found.")
            return

        df = df.rename(columns={uid_col: "user_id"})
        df = df.dropna(subset=["user_id"])
        df["user_id"] = df["user_id"].astype(str).str.strip()

        if "timestamp" in col_map and col_map["timestamp"] in df.columns:
            df = df.rename(columns={col_map["timestamp"]: "ts_raw"})
        elif "date" in col_map and "time" in col_map:
            dc, tc = col_map["date"], col_map["time"]
            if dc not in df.columns or tc not in df.columns:
                self._errors.append("Date or Time column not found.")
                return
            df["ts_raw"] = df[dc].astype(str) + " " + df[tc].astype(str)
        else:
            self._errors.append("Cannot determine timestamp columns.")
            return

        df["timestamp"] = pd.to_datetime(df["ts_raw"], errors="coerce")
        for _, r in df[df["timestamp"].isna()].iterrows():
            self._errors.append(
                f"Invalid datetime for {r['user_id']}: '{r['ts_raw']}'"
            )
        df = df.dropna(subset=["timestamp"])

        for _, r in df.head(200).iterrows():
            uid    = str(r["user_id"])
            ts_ad  = r["timestamp"]
            # Convert AD timestamp date → BS for display
            ts_bs_date = bs_str(ts_ad.date()) if hasattr(ts_ad, "date") else "—"
            ts_time    = ts_ad.strftime("%H:%M:%S") if hasattr(ts_ad, "strftime") else "—"
            self._rows.append({
                "user_id":  uid,
                "date_bs":  ts_bs_date,
                "time":     ts_time,
                "type": "Teacher" if uid.upper().startswith("T")
                        else "Student",
            })

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(24, 20, 24, 16)
        fl.setSpacing(12)

        summary = QLabel(
            f"Found {len(self._rows)} valid row(s)"
            + (f"  ·  {len(self._errors)} warning(s)"
               if self._errors else "")
        )
        summary.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #1a1a1a;"
            "background: transparent;"
        )
        fl.addWidget(summary)

        if self._errors:
            err_lbl = QLabel(
                "Warnings (rows will be skipped):\n"
                + "\n".join(self._errors[:6])
            )
            err_lbl.setStyleSheet(
                "font-size: 12px; color: #7a4f00; background: #fdf3e0;"
                "border: 1px solid #f5d98b; border-radius: 5px; padding: 8px;"
            )
            err_lbl.setWordWrap(True)
            fl.addWidget(err_lbl)

        tbl = QTableWidget()
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels(
            ["User ID", "Date (BS)", "Time", "Type"]
        )
        tbl.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeToContents)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet(TABLE_STYLE)
        tbl.verticalHeader().setVisible(False)
        tbl.setFrameShape(QFrame.NoFrame)
        tbl.setRowCount(len(self._rows))
        for r, row in enumerate(self._rows):
            for c, val in enumerate(
                [row["user_id"], row["date_bs"], row["time"], row["type"]]
            ):
                item = QTableWidgetItem(str(val))
                item.setForeground(Qt.black)
                tbl.setItem(r, c, item)
            tbl.setRowHeight(r, 34)
        fl.addWidget(tbl)
        root.addWidget(inner)

        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: #f5f5f5; border-top: 1px solid #e8e8e8; }"
        )
        br = QHBoxLayout(footer)
        br.setContentsMargins(24, 14, 24, 14)
        note = QLabel(
            f"Showing first {min(len(self._rows), 200)} rows. "
            "Dates shown in BS (Bikram Sambat)."
        )
        note.setStyleSheet(
            "font-size: 11px; color: #999999; background: transparent;"
        )
        br.addWidget(note)
        br.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        confirm = QPushButton("Confirm Import")
        confirm.setStyleSheet(BTN_PRIMARY)
        confirm.setEnabled(len(self._rows) > 0)
        confirm.clicked.connect(self.accept)
        br.addWidget(cancel)
        br.addSpacing(10)
        br.addWidget(confirm)
        root.addWidget(footer)