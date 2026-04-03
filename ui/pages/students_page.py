from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QDialog,
    QFormLayout, QDateEdit, QComboBox, QMessageBox, QHeaderView, QFrame
)
from PyQt5.QtCore import Qt, QDate
from database.connection import get_session
from models.student import Student
from models.class_group import Class, Group
from datetime import date
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY,
    TABLE_STYLE, INPUT_STYLE, COMBO_STYLE, DATE_STYLE,
    DIALOG_STYLE, FORM_LABEL_STYLE, PAGE_TITLE_STYLE,
    HINT_LABEL_STYLE, CARD_STYLE
)


class StudentsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        # ── Header
        header = QHBoxLayout()
        title = QLabel("Students")
        title.setStyleSheet(PAGE_TITLE_STYLE)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or user ID…")
        self.search_input.setFixedWidth(260)
        self.search_input.setStyleSheet(INPUT_STYLE)
        self.search_input.textChanged.connect(self.refresh_table)

        add_btn = QPushButton("+ Add Student")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self.open_add_dialog)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_input)
        header.addSpacing(10)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # ── Table inside white card
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "User ID", "Name", "Phone", "Class", "Group", "Actions"]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 160)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.verticalHeader().setVisible(False)
        self.table.setFrameShape(QFrame.NoFrame)

        card_layout.addWidget(self.table)
        layout.addWidget(card)

    def refresh_table(self):
        search = self.search_input.text().strip().lower()
        session = get_session()
        students = session.query(Student).all()

        # Eagerly extract before close
        rows = []
        for s in students:
            rows.append({
                "id":      str(s.id),
                "uid":     s.user_id,
                "name":    s.name,
                "phone":   s.phone or "",
                "class":   s.class_.name if s.class_ else "—",
                "group":   s.group.name  if s.group  else "—",
                "sid":     s.id,
            })
        session.close()

        if search:
            rows = [r for r in rows if
                    search in r["name"].lower() or search in r["uid"].lower()]

        self.table.setRowCount(len(rows))
        for row, r in enumerate(rows):
            for col, val in enumerate([
                r["id"], r["uid"], r["name"],
                r["phone"], r["class"], r["group"]
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(6, 4, 6, 4)
            al.setSpacing(6)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(BTN_SECONDARY)
            edit_btn.clicked.connect(lambda _, sid=r["sid"]: self.open_edit_dialog(sid))

            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(lambda _, sid=r["sid"]: self.delete_student(sid))

            al.addWidget(edit_btn)
            al.addWidget(del_btn)
            al.addStretch()
            self.table.setCellWidget(row, 6, aw)
            self.table.setRowHeight(row, 44)

    def open_add_dialog(self):
        if StudentDialog(parent=self).exec_():
            self.refresh_table()

    def open_edit_dialog(self, student_id):
        if StudentDialog(student_id=student_id, parent=self).exec_():
            self.refresh_table()

    def delete_student(self, student_id):
        if QMessageBox.question(self, "Confirm Delete",
                                "Are you sure you want to delete this student?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            session = get_session()
            s = session.query(Student).get(student_id)
            if s:
                session.delete(s)
                session.commit()
            session.close()
            self.refresh_table()


class StudentDialog(QDialog):
    def __init__(self, student_id=None, parent=None):
        super().__init__(parent)
        self.student_id = student_id
        self.setWindowTitle("Add Student" if not student_id else "Edit Student")
        self.setMinimumWidth(440)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()
        if student_id:
            self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # White inner card
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

        self.user_id_input = QLineEdit()
        self.user_id_input.setStyleSheet(INPUT_STYLE)
        self.user_id_input.setFixedHeight(36)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(INPUT_STYLE)
        self.name_input.setFixedHeight(36)

        self.phone_input = QLineEdit()
        self.phone_input.setStyleSheet(INPUT_STYLE)
        self.phone_input.setFixedHeight(36)

        self.address_input = QLineEdit()
        self.address_input.setStyleSheet(INPUT_STYLE)
        self.address_input.setFixedHeight(36)

        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDate(QDate.currentDate())
        self.dob_input.setStyleSheet(DATE_STYLE)
        self.dob_input.setFixedHeight(36)

        self.join_date_input = QDateEdit()
        self.join_date_input.setCalendarPopup(True)
        self.join_date_input.setDate(QDate.currentDate())
        self.join_date_input.setStyleSheet(DATE_STYLE)
        self.join_date_input.setFixedHeight(36)

        session = get_session()
        classes = session.query(Class).all()
        class_list = [(c.id, c.name) for c in classes]
        session.close()

        self.class_combo = QComboBox()
        self.class_combo.setStyleSheet(COMBO_STYLE)
        self.class_combo.setFixedHeight(36)
        self.class_combo.addItem("— Select Class —", None)
        for cid, cname in class_list:
            self.class_combo.addItem(cname, cid)
        self.class_combo.currentIndexChanged.connect(self._load_groups)

        self.group_combo = QComboBox()
        self.group_combo.setStyleSheet(COMBO_STYLE)
        self.group_combo.setFixedHeight(36)
        self.group_combo.addItem("— Select Group —", None)

        row("User ID  *", self.user_id_input)
        row("Full Name  *", self.name_input)
        row("Phone", self.phone_input)
        row("Address", self.address_input)
        row("Date of Birth", self.dob_input)
        row("Join Date", self.join_date_input)
        row("Class", self.class_combo)
        row("Group", self.group_combo)

        root.addWidget(inner)

        # Button footer
        footer = QFrame()
        footer.setStyleSheet("QFrame { background: #f5f5f5; border-top: 1px solid #e8e8e8; }")
        btn_layout = QHBoxLayout(footer)
        btn_layout.setContentsMargins(28, 16, 28, 16)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Student")
        save_btn.setStyleSheet(BTN_PRIMARY)
        save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(save_btn)
        root.addWidget(footer)

    def _load_groups(self):
        class_id = self.class_combo.currentData()
        self.group_combo.clear()
        self.group_combo.addItem("— Select Group —", None)
        if class_id:
            session = get_session()
            groups = session.query(Group).filter_by(class_id=class_id).all()
            for g in groups:
                self.group_combo.addItem(g.name, g.id)
            session.close()

    def _load_data(self):
        session = get_session()
        s = session.query(Student).get(self.student_id)
        if not s:
            session.close()
            return
        uid, name, phone, addr = s.user_id, s.name, s.phone or "", s.address or ""
        dob, jd = s.dob, s.join_date
        cid, gid = s.class_id, s.group_id
        session.close()

        self.user_id_input.setText(uid)
        self.name_input.setText(name)
        self.phone_input.setText(phone)
        self.address_input.setText(addr)
        if dob:
            self.dob_input.setDate(QDate(dob.year, dob.month, dob.day))
        if jd:
            self.join_date_input.setDate(QDate(jd.year, jd.month, jd.day))
        if cid:
            idx = self.class_combo.findData(cid)
            if idx >= 0:
                self.class_combo.setCurrentIndex(idx)
                self._load_groups()
        if gid:
            idx = self.group_combo.findData(gid)
            if idx >= 0:
                self.group_combo.setCurrentIndex(idx)

    def _save(self):
        uid  = self.user_id_input.text().strip()
        name = self.name_input.text().strip()
        if not uid or not name:
            QMessageBox.warning(self, "Validation Error", "User ID and Full Name are required.")
            return
        session = get_session()
        s = session.query(Student).get(self.student_id) if self.student_id else Student()
        if not self.student_id:
            session.add(s)
        s.user_id   = uid
        s.name      = name
        s.phone     = self.phone_input.text().strip()
        s.address   = self.address_input.text().strip()
        s.class_id  = self.class_combo.currentData()
        s.group_id  = self.group_combo.currentData()
        d = self.dob_input.date()
        j = self.join_date_input.date()
        s.dob       = date(d.year(), d.month(), d.day())
        s.join_date = date(j.year(), j.month(), j.day())
        session.commit()
        session.close()
        self.accept()