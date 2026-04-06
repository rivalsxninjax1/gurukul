from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QComboBox,
    QTimeEdit, QMessageBox, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt, QTime
from database.connection import get_session
from models.schedule import Schedule, DAYS
from models.class_group import Class, Group
from models.teacher import Teacher
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY,
    TABLE_STYLE, COMBO_STYLE, DIALOG_STYLE,
    FORM_LABEL_STYLE, PAGE_TITLE_STYLE, CARD_STYLE, INPUT_STYLE
)


class SchedulePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Schedule")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        add_btn = QPushButton("+ Add Schedule")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_schedule)
        header.addWidget(title); header.addStretch(); header.addWidget(add_btn)
        layout.addLayout(header)

        card = QFrame(); card.setStyleSheet(CARD_STYLE)
        cl = QVBoxLayout(card); cl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Day", "Class", "Group", "Teacher", "Subject", "Start", "End"]
        )
        hh = self.table.horizontalHeader()
        for i in range(7):
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.verticalHeader().setVisible(False)
        self.table.setFrameShape(QFrame.NoFrame)
        cl.addWidget(self.table)
        layout.addWidget(card)

    def refresh_table(self):
        session = get_session()
        scheds = session.query(Schedule).all()
        rows = []
        for s in scheds:
            rows.append({
                "id":      s.id,
                "day":     s.day_of_week,
                "class":   s.class_.name   if s.class_   else "—",
                "group":   s.group.name    if s.group    else "—",
                "teacher": s.teacher.name  if s.teacher  else "—",
                "subject": s.subject or "—",
                "start":   str(s.start_time),
                "end":     str(s.end_time),
            })
        session.close()

        # Sort by day order
        rows.sort(key=lambda r: DAYS.index(r["day"]) if r["day"] in DAYS else 99)

        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate([
                row["day"], row["class"], row["group"],
                row["teacher"], row["subject"], row["start"], row["end"]
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.table.setItem(r, c, item)
            self.table.setRowHeight(r, 40)

    def _add_schedule(self):
        if ScheduleDialog(parent=self).exec_(): 
            self.refresh_table()


class ScheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Schedule")
        self.setMinimumWidth(420)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(28, 28, 28, 28); fl.setSpacing(14)

        def row(lbl_text, widget):
            lbl = QLabel(lbl_text); lbl.setStyleSheet(FORM_LABEL_STYLE)
            fl.addWidget(lbl); fl.addWidget(widget); fl.addSpacing(2)

        session = get_session()
        classes  = [(c.id, c.name) for c in session.query(Class).all()]
        teachers = [(t.id, t.name) for t in session.query(Teacher).all()]
        session.close()

        self.day_combo = QComboBox(); self.day_combo.setStyleSheet(COMBO_STYLE)
        self.day_combo.setFixedHeight(36); self.day_combo.addItems(DAYS)

        self.class_combo = QComboBox(); self.class_combo.setStyleSheet(COMBO_STYLE)
        self.class_combo.setFixedHeight(36)
        self.class_combo.addItem("— Select Class —", None)
        for cid, cname in classes: self.class_combo.addItem(cname, cid)
        self.class_combo.currentIndexChanged.connect(self._load_groups)

        self.group_combo = QComboBox(); self.group_combo.setStyleSheet(COMBO_STYLE)
        self.group_combo.setFixedHeight(36)
        self.group_combo.addItem("— All Groups —", None)

        self.teacher_combo = QComboBox(); self.teacher_combo.setStyleSheet(COMBO_STYLE)
        self.teacher_combo.setFixedHeight(36)
        self.teacher_combo.addItem("— No Teacher —", None)
        for tid, tname in teachers: self.teacher_combo.addItem(tname, tid)

        from PyQt5.QtWidgets import QLineEdit
        self.subject_input = QLineEdit(); self.subject_input.setStyleSheet(INPUT_STYLE)
        self.subject_input.setFixedHeight(36); self.subject_input.setPlaceholderText("e.g. Mathematics")

        self.start_time = QTimeEdit()
        self.start_time.setStyleSheet("")
        self.start_time.setDisplayFormat("hh:mm AP")
        self.start_time.setTime(QTime(8, 0)); self.start_time.setFixedHeight(36)
        self.start_time.setStyleSheet("""
            QTimeEdit { border: 1.5px solid #cccccc; border-radius: 5px;
                        padding: 7px 10px; font-size: 13px; color: #1a1a1a; background: #ffffff; }
            QTimeEdit:focus { border-color: #1a1a1a; }
        """)

        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("hh:mm AP")
        self.end_time.setTime(QTime(10, 0)); self.end_time.setFixedHeight(36)
        self.end_time.setStyleSheet("""
            QTimeEdit { border: 1.5px solid #cccccc; border-radius: 5px;
                        padding: 7px 10px; font-size: 13px; color: #1a1a1a; background: #ffffff; }
            QTimeEdit:focus { border-color: #1a1a1a; }
        """)

        row("Day of Week",  self.day_combo)
        row("Class  *",     self.class_combo)
        row("Group",        self.group_combo)
        row("Teacher",      self.teacher_combo)
        row("Subject",      self.subject_input)
        row("Start Time",   self.start_time)
        row("End Time",     self.end_time)
        root.addWidget(inner)

        footer = QFrame()
        footer.setStyleSheet("QFrame { background: #f5f5f5; border-top: 1px solid #e8e8e8; }")
        btn_row = QHBoxLayout(footer)
        btn_row.setContentsMargins(28, 16, 28, 16); btn_row.addStretch()
        cancel = QPushButton("Cancel"); cancel.setStyleSheet(BTN_SECONDARY); cancel.clicked.connect(self.reject)
        save   = QPushButton("Save");   save.setStyleSheet(BTN_PRIMARY);    save.clicked.connect(self._save)
        btn_row.addWidget(cancel); btn_row.addSpacing(10); btn_row.addWidget(save)
        root.addWidget(footer)

    def _load_groups(self):
        class_id = self.class_combo.currentData()
        self.group_combo.clear()
        self.group_combo.addItem("— All Groups —", None)
        if class_id:
            session = get_session()
            groups = session.query(Group).filter_by(class_id=class_id).all()
            for g in groups: self.group_combo.addItem(g.name, g.id)
            session.close()

    def _save(self):
        class_id = self.class_combo.currentData()
        if not class_id:
            QMessageBox.warning(self, "Error", "Class is required.")
            return
        st = self.start_time.time(); et = self.end_time.time()
        from datetime import time
        session = get_session()
        s = Schedule(
            day_of_week = self.day_combo.currentText(),
            class_id    = class_id,
            group_id    = self.group_combo.currentData(),
            teacher_id  = self.teacher_combo.currentData(),
            subject     = self.subject_input.text().strip(),
            start_time  = time(st.hour(), st.minute()),
            end_time    = time(et.hour(), et.minute()),
        )
        session.add(s); session.commit(); session.close()
        self.accept()