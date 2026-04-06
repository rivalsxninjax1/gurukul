from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QFileDialog, QMessageBox, QTabWidget, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from database.connection import get_session
from models.class_group import Class
from services.report_service import (
    get_attendance_report, export_attendance_excel, export_attendance_pdf,
    get_revenue_report, export_revenue_excel, export_revenue_pdf
)
from utils.bs_converter import bs_str
from ui.bs_widgets import BSDateEdit
from ui.styles import (
    BTN_PRIMARY, BTN_SECONDARY, TABLE_STYLE, COMBO_STYLE,
    PAGE_TITLE_STYLE, CARD_STYLE, PANEL_TITLE_STYLE,
    SECTION_LABEL_STYLE, TAB_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
    STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG
)


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        title = QLabel("Reports")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.setStyleSheet(TAB_STYLE)
        tabs.addTab(self._build_attendance_tab(), "Attendance Report")
        tabs.addTab(self._build_revenue_tab(),    "Revenue Report")
        layout.addWidget(tabs)

    # ── Attendance tab ────────────────────────────────────────────────────────

    def _build_attendance_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: #ffffff;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        def lbl(t):
            l = QLabel(t)
            l.setStyleSheet(
                "font-size: 12px; font-weight: bold; color: #444444;"
                "background: transparent; border: none;"
            )
            return l

        # BS date pickers — default to today
        self.att_from = BSDateEdit()
        self.att_from.set_today()

        self.att_to = BSDateEdit()
        self.att_to.set_today()

        session = get_session()
        classes = [(c.id, c.name) for c in session.query(Class).all()]
        session.close()

        self.att_class_combo = QComboBox()
        self.att_class_combo.setStyleSheet(COMBO_STYLE)
        self.att_class_combo.setFixedHeight(36)
        self.att_class_combo.setFixedWidth(160)
        self.att_class_combo.addItem("All Classes", None)
        for cid, cname in classes:
            self.att_class_combo.addItem(cname, cid)

        gen_btn = QPushButton("Generate")
        gen_btn.setStyleSheet(BTN_PRIMARY)
        gen_btn.clicked.connect(self._gen_attendance)

        xl_btn = QPushButton("Export Excel")
        xl_btn.setStyleSheet(BTN_SECONDARY)
        xl_btn.clicked.connect(self._export_att_excel)

        pdf_btn = QPushButton("Export PDF")
        pdf_btn.setStyleSheet(BTN_SECONDARY)
        pdf_btn.clicked.connect(self._export_att_pdf)

        filter_row.addWidget(lbl("From (BS):"))
        filter_row.addWidget(self.att_from)
        filter_row.addWidget(lbl("To (BS):"))
        filter_row.addWidget(self.att_to)
        filter_row.addWidget(lbl("Class:"))
        filter_row.addWidget(self.att_class_combo)
        filter_row.addStretch()
        filter_row.addWidget(gen_btn)
        filter_row.addWidget(xl_btn)
        filter_row.addWidget(pdf_btn)
        layout.addLayout(filter_row)

        self.att_table = self._make_table(
            ["User ID", "Name", "Class", "Group",
             "Date (BS)", "Entry", "Exit", "Status"]
        )
        layout.addWidget(self.att_table)
        self._att_rows = []
        return tab

    def _gen_attendance(self):
        from_ad = self.att_from.get_ad_date()
        to_ad   = self.att_to.get_ad_date()
        if not from_ad or not to_ad:
            QMessageBox.warning(self, "Invalid Date",
                                "Please enter valid BS dates.")
            return
        if from_ad > to_ad:
            QMessageBox.warning(self, "Date Range",
                                "From date must be before To date.")
            return

        rows = get_attendance_report(
            from_ad, to_ad,
            self.att_class_combo.currentData()
        )
        self._att_rows = rows
        self.att_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            # Convert date to BS for display
            date_bs = bs_str_from_str(row["date"])
            vals = [
                row["user_id"], row["name"], row["class"],
                row["group"], date_bs,
                row["entry"], row["exit"], row["status"]
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setForeground(Qt.black)
                if c == 7:
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

    def _export_att_excel(self):
        if not self._att_rows:
            QMessageBox.information(self, "No Data",
                                    "Generate report first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel", "attendance_report.xlsx", "Excel (*.xlsx)"
        )
        if path:
            export_attendance_excel(self._att_rows, path)
            QMessageBox.information(self, "Saved", f"Saved to:\n{path}")

    def _export_att_pdf(self):
        if not self._att_rows:
            QMessageBox.information(self, "No Data",
                                    "Generate report first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "attendance_report.pdf", "PDF (*.pdf)"
        )
        if path:
            from_ad = self.att_from.get_ad_date()
            to_ad   = self.att_to.get_ad_date()
            export_attendance_pdf(
                self._att_rows, path,
                self.att_from.get_bs_str(),
                self.att_to.get_bs_str()
            )
            QMessageBox.information(self, "Saved", f"Saved to:\n{path}")

    # ── Revenue tab ───────────────────────────────────────────────────────────

    def _build_revenue_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background: #ffffff;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        btn_row = QHBoxLayout()
        gen_btn = QPushButton("Generate Revenue Report")
        gen_btn.setStyleSheet(BTN_PRIMARY)
        gen_btn.clicked.connect(self._gen_revenue)

        xl_btn = QPushButton("Export Excel")
        xl_btn.setStyleSheet(BTN_SECONDARY)
        xl_btn.clicked.connect(self._export_rev_excel)

        pdf_btn = QPushButton("Export PDF")
        pdf_btn.setStyleSheet(BTN_SECONDARY)
        pdf_btn.clicked.connect(self._export_rev_pdf)

        btn_row.addWidget(gen_btn)
        btn_row.addStretch()
        btn_row.addWidget(xl_btn)
        btn_row.addWidget(pdf_btn)
        layout.addLayout(btn_row)

        self.rev_table = self._make_table(
            ["User ID", "Name", "Class",
             "Total Fee", "Paid", "Balance", "Status"]
        )
        layout.addWidget(self.rev_table)
        self._rev_rows = []
        return tab

    def _gen_revenue(self):
        rows = get_revenue_report()
        self._rev_rows = rows
        self.rev_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            vals = [
                row["user_id"], row["name"], row["class"],
                f"Rs. {row['total_fee']:,.0f}",
                f"Rs. {row['paid']:,.0f}",
                f"Rs. {row['balance']:,.0f}",
                row["status"]
            ]
            for c, val in enumerate(vals):
                item = QTableWidgetItem(str(val))
                item.setForeground(Qt.black)
                if c == 6:
                    if val == "Paid":
                        item.setForeground(QColor(STATUS_PRESENT))
                        item.setBackground(QColor(STATUS_PRESENT_BG))
                    elif val == "Unpaid":
                        item.setForeground(QColor(STATUS_ABSENT))
                        item.setBackground(QColor(STATUS_ABSENT_BG))
                    elif val == "Partial":
                        item.setForeground(QColor(STATUS_INCOMPLETE))
                        item.setBackground(QColor(STATUS_INCOMPLETE_BG))
                self.rev_table.setItem(r, c, item)
            self.rev_table.setRowHeight(r, 36)

    def _export_rev_excel(self):
        if not self._rev_rows:
            QMessageBox.information(self, "No Data", "Generate report first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel", "revenue_report.xlsx", "Excel (*.xlsx)"
        )
        if path:
            export_revenue_excel(self._rev_rows, path)
            QMessageBox.information(self, "Saved", f"Saved to:\n{path}")

    def _export_rev_pdf(self):
        if not self._rev_rows:
            QMessageBox.information(self, "No Data", "Generate report first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", "revenue_report.pdf", "PDF (*.pdf)"
        )
        if path:
            export_revenue_pdf(self._rev_rows, path)
            QMessageBox.information(self, "Saved", f"Saved to:\n{path}")

    def _make_table(self, headers):
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        hh = t.horizontalHeader()
        for i in range(len(headers)):
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.setAlternatingRowColors(True)
        t.setStyleSheet(TABLE_STYLE)
        t.verticalHeader().setVisible(False)
        t.setFrameShape(QFrame.NoFrame)
        return t


# ── Helper used in _gen_attendance ────────────────────────────────────────────
def bs_str_from_str(date_str: str) -> str:
    """Convert AD date string from DB to BS display string."""
    if not date_str or date_str == "—":
        return date_str
    try:
        import datetime
        d = datetime.date.fromisoformat(date_str[:10])
        return bs_str(d)
    except Exception:
        return date_str