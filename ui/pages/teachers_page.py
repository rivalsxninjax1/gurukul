from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QDialog,
    QMessageBox, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt
from database.connection import get_session
from models.teacher import Teacher
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY,
    TABLE_STYLE, INPUT_STYLE, DIALOG_STYLE,
    FORM_LABEL_STYLE, PAGE_TITLE_STYLE, CARD_STYLE
)


class TeachersPage(QWidget):
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
        title = QLabel("Teachers")
        title.setStyleSheet(PAGE_TITLE_STYLE)

        add_btn = QPushButton("+ Add Teacher")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self.open_add_dialog)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_btn)
        layout.addLayout(header)

        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "User ID", "Name", "Phone", "Subject", "Actions"]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 160)
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
        teachers = session.query(Teacher).all()
        rows = [{"id": str(t.id), "uid": t.user_id, "name": t.name,
                 "phone": t.phone or "", "subject": t.subject or "", "tid": t.id}
                for t in teachers]
        session.close()

        self.table.setRowCount(len(rows))
        for row, r in enumerate(rows):
            for col, val in enumerate([r["id"], r["uid"], r["name"], r["phone"], r["subject"]]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.table.setItem(row, col, item)

            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(6, 4, 6, 4)
            al.setSpacing(6)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(BTN_SECONDARY)
            edit_btn.clicked.connect(lambda _, tid=r["tid"]: self.open_edit_dialog(tid))

            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(lambda _, tid=r["tid"]: self.delete_teacher(tid))

            al.addWidget(edit_btn)
            al.addWidget(del_btn)
            al.addStretch()
            self.table.setCellWidget(row, 5, aw)
            self.table.setRowHeight(row, 44)

    def open_add_dialog(self):
        if TeacherDialog(parent=self).exec_():
            self.refresh_table()

    def open_edit_dialog(self, tid):
        if TeacherDialog(teacher_id=tid, parent=self).exec_():
            self.refresh_table()

    def delete_teacher(self, tid):
        if QMessageBox.question(self, "Confirm Delete",
                                "Delete this teacher?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            session = get_session()
            t = session.query(Teacher).get(tid)
            if t:
                session.delete(t)
                session.commit()
            session.close()
            self.refresh_table()


class TeacherDialog(QDialog):
    def __init__(self, teacher_id=None, parent=None):
        super().__init__(parent)
        self.teacher_id = teacher_id
        self.setWindowTitle("Add Teacher" if not teacher_id else "Edit Teacher")
        self.setMinimumWidth(420)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()
        if teacher_id:
            self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        form_layout = QVBoxLayout(inner)
        form_layout.setContentsMargins(28, 28, 28, 28)
        form_layout.setSpacing(14)

        def row(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(FORM_LABEL_STYLE)
            form_layout.addWidget(lbl)
            form_layout.addWidget(widget)
            form_layout.addSpacing(2)

        self.user_id_input = QLineEdit(); self.user_id_input.setStyleSheet(INPUT_STYLE); self.user_id_input.setFixedHeight(36)
        self.name_input    = QLineEdit(); self.name_input.setStyleSheet(INPUT_STYLE);    self.name_input.setFixedHeight(36)
        self.phone_input   = QLineEdit(); self.phone_input.setStyleSheet(INPUT_STYLE);   self.phone_input.setFixedHeight(36)
        self.subject_input = QLineEdit(); self.subject_input.setStyleSheet(INPUT_STYLE); self.subject_input.setFixedHeight(36)
        self.address_input = QLineEdit(); self.address_input.setStyleSheet(INPUT_STYLE); self.address_input.setFixedHeight(36)

        row("User ID  *",  self.user_id_input)
        row("Full Name  *", self.name_input)
        row("Phone",        self.phone_input)
        row("Subject",      self.subject_input)
        row("Address",      self.address_input)

        root.addWidget(inner)

        footer = QFrame()
        footer.setStyleSheet("QFrame { background: #f5f5f5; border-top: 1px solid #e8e8e8; }")
        btn_layout = QHBoxLayout(footer)
        btn_layout.setContentsMargins(28, 16, 28, 16)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel"); cancel_btn.setStyleSheet(BTN_SECONDARY); cancel_btn.clicked.connect(self.reject)
        save_btn   = QPushButton("Save Teacher"); save_btn.setStyleSheet(BTN_PRIMARY); save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(save_btn)
        root.addWidget(footer)

    def _load_data(self):
        session = get_session()
        t = session.query(Teacher).get(self.teacher_id)
        if t:
            uid, name, phone, subj, addr = t.user_id, t.name, t.phone or "", t.subject or "", t.address or ""
        session.close()
        if t:
            self.user_id_input.setText(uid)
            self.name_input.setText(name)
            self.phone_input.setText(phone)
            self.subject_input.setText(subj)
            self.address_input.setText(addr)

    def _save(self):
        uid  = self.user_id_input.text().strip()
        name = self.name_input.text().strip()
        if not uid or not name:
            QMessageBox.warning(self, "Validation Error", "User ID and Full Name are required.")
            return
        session = get_session()
        t = session.query(Teacher).get(self.teacher_id) if self.teacher_id else Teacher()
        if not self.teacher_id:
            session.add(t)
        t.user_id = uid;  t.name    = name
        t.phone   = self.phone_input.text().strip()
        t.subject = self.subject_input.text().strip()
        t.address = self.address_input.text().strip()
        session.commit()
        session.close()
        self.accept()