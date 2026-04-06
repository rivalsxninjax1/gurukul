from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QDialog,
    QMessageBox, QHeaderView, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt
from database.connection import get_session
from models.teacher import Teacher
from services.id_service import generate_teacher_id
from utils.bs_converter import bs_str
from ui.bs_widgets import BSDateEdit
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY,
    TABLE_STYLE, INPUT_STYLE, INPUT_READONLY_STYLE,
    DIALOG_STYLE, FORM_LABEL_STYLE, PAGE_TITLE_STYLE, CARD_STYLE,
)
from ui.event_bus import bus
from ui.widgets import Toast


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

        self.toast = Toast()
        layout.addWidget(self.toast)

        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Teacher ID", "Name", "Phone",
             "Subject", "Join Date (BS)", "Actions"]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 190)
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
        teachers = session.query(Teacher).all()
        rows = [{
            "id":      str(t.id),
            "uid":     t.user_id,
            "name":    t.name,
            "phone":   t.phone or "",
            "subject": t.subject or "",
            "joined":  bs_str(t.join_date) if t.join_date else "—",
            "tid":     t.id,
        } for t in teachers]
        session.close()

        self.table.setRowCount(len(rows))
        for row, r in enumerate(rows):
            for col, val in enumerate([
                r["id"], r["uid"], r["name"],
                r["phone"], r["subject"], r["joined"]
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.table.setItem(row, col, item)

            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(6, 4, 6, 4)
            al.setSpacing(6)

            profile_btn = QPushButton("Profile")
            profile_btn.setStyleSheet(BTN_SECONDARY)
            profile_btn.clicked.connect(
                lambda _, tid=r["tid"]: bus.open_teacher_profile.emit(tid)
            )
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(BTN_SECONDARY)
            edit_btn.clicked.connect(
                lambda _, tid=r["tid"]: self.open_edit_dialog(tid)
            )
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(
                lambda _, tid=r["tid"]: self.delete_teacher(tid)
            )
            al.addWidget(profile_btn)
            al.addWidget(edit_btn)
            al.addWidget(del_btn)
            self.table.setCellWidget(row, 6, aw)
            self.table.setRowHeight(row, 44)

    def open_add_dialog(self):
        if TeacherDialog(parent=self).exec_():
            self.refresh_table()
            self.toast.success("Teacher added.")

    def open_edit_dialog(self, tid):
        if TeacherDialog(teacher_id=tid, parent=self).exec_():
            self.refresh_table()
            self.toast.success("Teacher updated.")

    def delete_teacher(self, tid):
        if QMessageBox.question(
            self, "Confirm Delete",
            "Delete this teacher and all their records?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            session = get_session()
            t = session.query(Teacher).get(tid)
            if t:
                session.delete(t)
                session.commit()
            session.close()
            self.refresh_table()
            self.toast.success("Teacher deleted.")


class TeacherDialog(QDialog):
    def __init__(self, teacher_id=None, parent=None):
        super().__init__(parent)
        self.teacher_id = teacher_id
        self.setWindowTitle(
            "Add Teacher" if not teacher_id else "Edit Teacher"
        )
        self.setMinimumWidth(460)
        self.setMinimumHeight(360)
        self.setStyleSheet(DIALOG_STYLE)
        self.setSizeGripEnabled(True)
        self._build_ui()
        if teacher_id:
            self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: #ffffff; border: none; }"
        )
        inner = QWidget()
        inner.setStyleSheet("background: #ffffff;")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(28, 28, 28, 20)
        fl.setSpacing(14)

        def field(label_text, widget):
            lbl = QLabel(label_text)
            lbl.setStyleSheet(FORM_LABEL_STYLE)
            fl.addWidget(lbl)
            fl.addWidget(widget)
            fl.addSpacing(4)

        # Auto ID
        self._auto_id = generate_teacher_id() if not self.teacher_id else ""
        id_lbl = QLabel("Teacher ID (auto-generated)")
        id_lbl.setStyleSheet(FORM_LABEL_STYLE)
        fl.addWidget(id_lbl)
        self.id_display = QLineEdit(self._auto_id)
        self.id_display.setReadOnly(True)
        self.id_display.setStyleSheet(INPUT_READONLY_STYLE)
        self.id_display.setFixedHeight(36)
        fl.addWidget(self.id_display)
        fl.addSpacing(4)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(INPUT_STYLE)
        self.name_input.setFixedHeight(36)
        self.name_input.setPlaceholderText("Full name")

        self.phone_input = QLineEdit()
        self.phone_input.setStyleSheet(INPUT_STYLE)
        self.phone_input.setFixedHeight(36)
        self.phone_input.setPlaceholderText("Phone number")

        self.subject_input = QLineEdit()
        self.subject_input.setStyleSheet(INPUT_STYLE)
        self.subject_input.setFixedHeight(36)
        self.subject_input.setPlaceholderText("e.g. Mathematics")

        self.address_input = QLineEdit()
        self.address_input.setStyleSheet(INPUT_STYLE)
        self.address_input.setFixedHeight(36)
        self.address_input.setPlaceholderText("Address")

        # BS date picker
        self.join_date_input = BSDateEdit()
        self.join_date_input.set_today()

        field("Full Name  *",    self.name_input)
        field("Phone",           self.phone_input)
        field("Subject",         self.subject_input)
        field("Address",         self.address_input)
        field("Join Date (BS)",  self.join_date_input)

        scroll.setWidget(inner)
        root.addWidget(scroll)

        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: #f5f5f5; border-top: 1px solid #e8e8e8; }"
        )
        br = QHBoxLayout(footer)
        br.setContentsMargins(28, 14, 28, 14)
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        label = "Save Teacher" if not self.teacher_id else "Update Teacher"
        save  = QPushButton(label)
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self._save)
        br.addWidget(cancel)
        br.addStretch()
        br.addWidget(save)
        root.addWidget(footer)

    def _load_data(self):
        session = get_session()
        t = session.query(Teacher).get(self.teacher_id)
        if not t:
            session.close()
            return
        uid, name = t.user_id, t.name
        phone     = t.phone or ""
        subject   = t.subject or ""
        address   = t.address or ""
        jd        = t.join_date
        session.close()

        self.id_display.setText(uid)
        self.name_input.setText(name)
        self.phone_input.setText(phone)
        self.subject_input.setText(subject)
        self.address_input.setText(address)
        if jd:
            self.join_date_input.set_from_ad(jd)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Full Name is required.")
            self.name_input.setFocus()
            return

        join_ad = self.join_date_input.get_ad_date()
        if not join_ad:
            QMessageBox.warning(
                self, "Validation",
                "Join Date (BS) is invalid."
            )
            return

        session = get_session()
        if self.teacher_id:
            t = session.query(Teacher).get(self.teacher_id)
        else:
            t = Teacher()
            t.user_id = self._auto_id
            session.add(t)

        t.name      = name
        t.phone     = self.phone_input.text().strip()
        t.subject   = self.subject_input.text().strip()
        t.address   = self.address_input.text().strip()
        t.join_date = join_ad

        session.commit()
        session.close()
        self.accept()