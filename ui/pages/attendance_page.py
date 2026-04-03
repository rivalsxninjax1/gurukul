from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QDialog,
    QMessageBox, QHeaderView, QDateEdit, QProgressBar,
    QComboBox, QFrame
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QColor
import pandas as pd
from services.attendance_service import import_attendance_excel
from database.connection import get_session
from models.attendance import Attendance
from ui.styles import (
    BTN_PRIMARY, BTN_SECONDARY, TABLE_STYLE, COMBO_STYLE,
    DATE_STYLE, DIALOG_STYLE, FORM_LABEL_STYLE, PAGE_TITLE_STYLE,
    CARD_STYLE, SECTION_LABEL_STYLE,
    STATUS_PRESENT, STATUS_INCOMPLETE, STATUS_ABSENT,
    STATUS_PRESENT_BG, STATUS_INCOMPLETE_BG, STATUS_ABSENT_BG
)


class ImportWorker(QThread):
    finished = pyqtSignal(dict)

    def __init__(self, filepath, col_map):
        super().__init__()
        self.filepath = filepath
        self.col_map  = col_map

    def run(self):
        self.finished.emit(import_attendance_excel(self.filepath, self.col_map))


class AttendancePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("Attendance")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(title)

        # ── Filter bar card
        filter_card = QFrame()
        filter_card.setStyleSheet(CARD_STYLE)
        fl = QHBoxLayout(filter_card)
        fl.setContentsMargins(16, 14, 16, 14)
        fl.setSpacing(14)

        date_lbl = QLabel("Date:")
        date_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #333333; background: transparent;")

        self.date_filter = QDateEdit()
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setStyleSheet(DATE_STYLE)
        self.date_filter.setFixedWidth(150)
        self.date_filter.setFixedHeight(36)
        self.date_filter.dateChanged.connect(self.refresh_table)

        self.badge_present = self._status_badge("Present: 0", STATUS_PRESENT, STATUS_PRESENT_BG)
        self.badge_incomplete = self._status_badge("Incomplete: 0", STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG)
        self.badge_absent = self._status_badge("Absent: 0", STATUS_ABSENT, STATUS_ABSENT_BG)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(100)
        self.progress.setFixedHeight(20)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc; border-radius: 4px;
                background: #f0f0f0;
            }
            QProgressBar::chunk { background: #2c2c2c; border-radius: 3px; }
        """)

        import_btn = QPushButton("Import Excel")
        import_btn.setStyleSheet(BTN_PRIMARY)
        import_btn.clicked.connect(self.open_import_dialog)

        fl.addWidget(date_lbl)
        fl.addWidget(self.date_filter)
        fl.addSpacing(10)
        fl.addWidget(self.badge_present)
        fl.addWidget(self.badge_incomplete)
        fl.addWidget(self.badge_absent)
        fl.addStretch()
        fl.addWidget(self.progress)
        fl.addWidget(import_btn)
        layout.addWidget(filter_card)

        # ── Table card
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["User ID", "Student Name", "Date", "Entry Time", "Exit Time", "Status"]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.verticalHeader().setVisible(False)
        self.table.setFrameShape(QFrame.NoFrame)

        card_layout.addWidget(self.table)
        layout.addWidget(card)

    def _status_badge(self, text, fg, bg):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {fg};"
            f"background: {bg}; border-radius: 4px; padding: 4px 12px; border: none;"
        )
        return lbl

    def refresh_table(self):
        selected_date = self.date_filter.date().toPyDate()
        session = get_session()
        records = session.query(Attendance).filter_by(date=selected_date).all()

        rows = []
        for att in records:
            s = att.student
            rows.append({
                "uid":    s.user_id if s else "",
                "name":   s.name    if s else "Unknown",
                "date":   str(att.date),
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

        self.table.setRowCount(len(rows))
        for row, r in enumerate(rows):
            for col, val in enumerate([
                r["uid"], r["name"], r["date"], r["entry"], r["exit"]
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.table.setItem(row, col, item)

            status_item = QTableWidgetItem(r["status"])
            if r["status"] == "Present":
                status_item.setForeground(QColor(STATUS_PRESENT))
                status_item.setBackground(QColor(STATUS_PRESENT_BG))
            elif r["status"] == "Incomplete":
                status_item.setForeground(QColor(STATUS_INCOMPLETE))
                status_item.setBackground(QColor(STATUS_INCOMPLETE_BG))
            elif r["status"] == "Absent":
                status_item.setForeground(QColor(STATUS_ABSENT))
                status_item.setBackground(QColor(STATUS_ABSENT_BG))
            else:
                status_item.setForeground(Qt.black)
            self.table.setItem(row, 5, status_item)
            self.table.setRowHeight(row, 42)

    def open_import_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Attendance Excel", "", "Excel Files (*.xlsx *.xls)"
        )
        if not filepath:
            return
        try:
            df = pd.read_excel(filepath, nrows=0)
            columns = list(df.columns)
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Cannot read file:\n{e}")
            return

        dlg = ColumnMapDialog(columns, parent=self)
        if dlg.exec_():
            col_map = dlg.get_mapping()
            self.progress.setVisible(True)
            self.worker = ImportWorker(filepath, col_map)
            self.worker.finished.connect(self._on_import_done)
            self.worker.start()

    def _on_import_done(self, result):
        self.progress.setVisible(False)
        lines = [f"Successfully imported: {result['success']} record(s)"]
        if result["errors"]:
            lines.append(f"Errors ({len(result['errors'])}):")
            lines += result["errors"][:5]
        if result["unknown_ids"]:
            lines.append(f"Unknown IDs: {', '.join(result['unknown_ids'][:10])}")
        QMessageBox.information(self, "Import Complete", "\n".join(lines))
        self.refresh_table()


class ColumnMapDialog(QDialog):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map Excel Columns")
        self.setMinimumWidth(400)
        self.setStyleSheet(DIALOG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        form_layout = QVBoxLayout(inner)
        form_layout.setContentsMargins(28, 28, 28, 28)
        form_layout.setSpacing(14)

        info = QLabel("Match your Excel columns to the required fields below:")
        info.setStyleSheet("font-size: 12px; color: #666666; background: transparent;")
        info.setWordWrap(True)
        form_layout.addWidget(info)
        form_layout.addSpacing(6)

        def row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(FORM_LABEL_STYLE)
            form_layout.addWidget(lbl)
            form_layout.addWidget(widget)

        self.uid_combo = QComboBox()
        self.uid_combo.setStyleSheet(COMBO_STYLE)
        self.uid_combo.setFixedHeight(36)
        self.uid_combo.addItems(columns)

        self.ts_combo = QComboBox()
        self.ts_combo.setStyleSheet(COMBO_STYLE)
        self.ts_combo.setFixedHeight(36)
        self.ts_combo.addItems(columns)

        for i, col in enumerate(columns):
            if col.lower() in ("user_id", "userid", "id", "employee_id", "student_id"):
                self.uid_combo.setCurrentIndex(i)
            if col.lower() in ("timestamp", "datetime", "time", "date_time", "punch_time"):
                self.ts_combo.setCurrentIndex(i)

        row("User ID column:", self.uid_combo)
        row("Timestamp column:", self.ts_combo)

        root.addWidget(inner)

        footer = QFrame()
        footer.setStyleSheet("QFrame { background: #f5f5f5; border-top: 1px solid #e8e8e8; }")
        btn_layout = QHBoxLayout(footer)
        btn_layout.setContentsMargins(28, 16, 28, 16)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel"); cancel_btn.setStyleSheet(BTN_SECONDARY); cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("Confirm Mapping"); ok_btn.setStyleSheet(BTN_PRIMARY); ok_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(ok_btn)
        root.addWidget(footer)

    def get_mapping(self):
        return {
            "user_id":   self.uid_combo.currentText(),
            "timestamp": self.ts_combo.currentText(),
        }