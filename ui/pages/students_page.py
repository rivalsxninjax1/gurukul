from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QDialog,
    QComboBox, QMessageBox, QHeaderView, QFrame,
    QDoubleSpinBox, QSpinBox, QScrollArea, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from database.connection import get_session
from models.student import Student
from models.class_group import Class, Group
from sqlalchemy import or_
from services.subscription_service import (
    create_subscription, get_student_subscription_flags
)
from services.id_service import generate_student_id
from services.export_service import export_student_list_pdf
from services.settings_service import get_setting
from utils.bs_converter import bs_to_ad
from ui.bs_widgets import BSDateEdit
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY,
    TABLE_STYLE, INPUT_STYLE, INPUT_READONLY_STYLE, COMBO_STYLE,
    SPINBOX_STYLE, DIALOG_STYLE, FORM_LABEL_STYLE,
    PAGE_TITLE_STYLE, CARD_STYLE, SECTION_LABEL_STYLE,
    FILTER_LABEL_STYLE,
)
from ui.event_bus import bus
from ui.widgets import Toast, FilterField

FLAG_COLORS = {
    "active":          ("#27ae60", "#eafaf1"),
    "expiring_soon":   ("#e67e22", "#fef5e7"),
    "payment_pending": ("#d35400", "#fdf2e9"),
    "expired":         ("#c0392b", "#fdeaea"),
    "no_subscription": ("#888888", "#f5f5f5"),
}


class StudentsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._filter_flag  = "all"
        self._filter_class = None
        self._filter_group = None
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("Students")
        title.setStyleSheet(PAGE_TITLE_STYLE)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or ID…")
        self.search_input.setFixedWidth(200)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet(INPUT_STYLE)
        self.search_input.textChanged.connect(self.refresh_table)

        export_btn = QPushButton("Export PDF")
        export_btn.setStyleSheet(BTN_SECONDARY)
        export_btn.clicked.connect(self._export_pdf)

        add_btn = QPushButton("+ Add Student")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self.open_add_dialog)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.search_input)
        header.addSpacing(8)
        header.addWidget(export_btn)
        header.addSpacing(6)
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.toast = Toast()
        layout.addWidget(self.toast)

        # Filter bar
        filter_card = QFrame()
        filter_card.setStyleSheet(CARD_STYLE)
        fl = QHBoxLayout(filter_card)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(10)

        def flbl(text: str):
            l = QLabel(text)
            l.setStyleSheet(FILTER_LABEL_STYLE)
            return l

        session = get_session()
        classes = [(c.id, c.name) for c in session.query(Class).all()]
        session.close()

        self.class_filter = QComboBox()
        self.class_filter.setStyleSheet(COMBO_STYLE)
        self.class_filter.addItem("All Classes", None)
        for cid, cname in classes:
            self.class_filter.addItem(cname, cid)
        self.class_filter.currentIndexChanged.connect(self._on_class_filter)

        self.group_filter = QComboBox()
        self.group_filter.setStyleSheet(COMBO_STYLE)
        self.group_filter.addItem("All Groups", None)
        self.group_filter.currentIndexChanged.connect(self._on_group_filter)

        class_field = FilterField("Class", self.class_filter, width=170)
        group_field = FilterField("Group", self.group_filter, width=170)

        fl.addWidget(class_field)
        fl.addWidget(group_field)
        fl.addSpacing(16)
        fl.addWidget(flbl("Status:"))

        self._filter_btns = {}
        filters = [
            ("all",             "All",             "#333333", "#eeeeee"),
            ("active",          "Active",          "#27ae60", "#eafaf1"),
            ("expiring_soon",   "Expiring Soon",   "#e67e22", "#fef5e7"),
            ("payment_pending", "Payment Pending", "#d35400", "#fdf2e9"),
            ("expired",         "Expired",         "#c0392b", "#fdeaea"),
        ]
        for key, label, fg, bg in filters:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(key == "all")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg}; color: {fg};
                    border: 1.5px solid {fg}; border-radius: 4px;
                    padding: 3px 10px; font-size: 11px; font-weight: bold;
                    min-height: 26px;
                }}
                QPushButton:checked {{ background: {fg}; color: #ffffff; }}
            """)
            btn.clicked.connect(lambda _, k=key: self._set_filter(k))
            fl.addWidget(btn)
            self._filter_btns[key] = btn

        fl.addStretch()
        layout.addWidget(filter_card)

        # Table
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "User ID", "Name", "Phone",
            "Class", "Group", "Subscription", "Actions"
        ])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 190)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(TABLE_STYLE)
        self.table.verticalHeader().setVisible(False)
        self.table.setFrameShape(QFrame.NoFrame)
        cl.addWidget(self.table)
        layout.addWidget(card)

    def _on_class_filter(self):
        self._filter_class = self.class_filter.currentData()
        self.group_filter.blockSignals(True)
        self.group_filter.clear()
        self.group_filter.addItem("All Groups", None)
        if self._filter_class:
            session = get_session()
            groups = session.query(Group).filter_by(
                class_id=self._filter_class
            ).all()
            for g in groups:
                self.group_filter.addItem(g.name, g.id)
            session.close()
        self.group_filter.blockSignals(False)
        self._filter_group = None
        self.refresh_table()

    def _on_group_filter(self):
        self._filter_group = self.group_filter.currentData()
        self.refresh_table()

    def _set_filter(self, key):
        self._filter_flag = key
        for k, btn in self._filter_btns.items():
            btn.setChecked(k == key)
        self.refresh_table()

    def refresh_table(self):
        search = self.search_input.text().strip()
        session = get_session()
        query = session.query(Student)
        if self._filter_class:
            query = query.filter(Student.class_id == self._filter_class)
        if self._filter_group:
            query = query.filter(Student.group_id == self._filter_group)
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(Student.name.ilike(like), Student.user_id.ilike(like))
            )
        students = query.order_by(Student.name).all()
        rows = []
        for s in students:
            rows.append({
                "id":    str(s.id),
                "uid":   s.user_id,
                "name":  s.name,
                "phone": s.phone or "",
                "class": s.class_.name if s.class_ else "—",
                "group": s.group.name  if s.group  else "—",
                "sid":   s.id,
            })
        session.close()

        for r in rows:
            r["flag_data"] = get_student_subscription_flags(r["sid"])

        if self._filter_flag != "all":
            rows = [r for r in rows
                    if r["flag_data"]["flag"] == self._filter_flag]

        self.table.setRowCount(len(rows))
        for row, r in enumerate(rows):
            for col, val in enumerate([
                r["id"], r["uid"], r["name"],
                r["phone"], r["class"], r["group"]
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(Qt.black)
                self.table.setItem(row, col, item)

            fd = r["flag_data"]
            fg, bg = FLAG_COLORS.get(fd["flag"], ("#333333", "#eeeeee"))
            s_item = QTableWidgetItem(f"  {fd['label']}")
            s_item.setForeground(QColor(fg))
            s_item.setBackground(QColor(bg))
            self.table.setItem(row, 6, s_item)

            aw = QWidget()
            al = QHBoxLayout(aw)
            al.setContentsMargins(5, 4, 5, 4)
            al.setSpacing(5)

            profile_btn = QPushButton("Profile")
            profile_btn.setStyleSheet(BTN_SECONDARY)
            profile_btn.clicked.connect(
                lambda _, sid=r["sid"]: bus.open_student_profile.emit(sid)
            )
            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet(BTN_SECONDARY)
            edit_btn.clicked.connect(
                lambda _, sid=r["sid"]: self.open_edit_dialog(sid)
            )
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(
                lambda _, sid=r["sid"]: self.delete_student(sid)
            )
            al.addWidget(profile_btn)
            al.addWidget(edit_btn)
            al.addWidget(del_btn)
            self.table.setCellWidget(row, 7, aw)
            self.table.setRowHeight(row, 44)

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Students PDF",
            "students_list.pdf", "PDF Files (*.pdf)"
        )
        if path:
            centre_name = get_setting(
                "centre_name", "GURUKUL ACADEMY AND TRAINING CENTER"
            )
            centre_address = get_setting(
                "centre_address", "Biratnagar-1, Bhatta Chowk"
            )
            export_student_list_pdf(path, centre_name, centre_address)
            QMessageBox.information(
                self, "Exported", f"Student list saved:\n{path}"
            )

    def open_add_dialog(self):
        dlg = StudentDialog(parent=self)
        if dlg.exec_():
            self.refresh_table()
            self.toast.success("Student added successfully.")
            bus.student_saved.emit()
            bus.open_student_profile.emit(dlg.saved_student_id)

    def open_edit_dialog(self, student_id):
        dlg = StudentDialog(student_id=student_id, parent=self)
        if dlg.exec_():
            self.refresh_table()
            self.toast.success("Student updated.")
            bus.student_saved.emit()

    def delete_student(self, student_id):
        if QMessageBox.question(
            self, "Confirm Delete",
            "Delete this student and all their records? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            session = get_session()
            s = session.query(Student).get(student_id)
            if s:
                session.delete(s)
                session.commit()
            session.close()
            self.refresh_table()
            self.toast.success("Student deleted.")
            bus.student_saved.emit()


class StudentDialog(QDialog):
    def __init__(self, student_id=None, parent=None):
        super().__init__(parent)
        self.student_id       = student_id
        self.saved_student_id = None
        self.setWindowTitle(
            "Add Student" if not student_id else "Edit Student"
        )
        self.setMinimumWidth(500)
        self.setMinimumHeight(460)
        self.setStyleSheet(DIALOG_STYLE)
        self.setSizeGripEnabled(True)
        self._build_ui()
        if student_id:
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
            fl.addSpacing(2)

        # Auto-generated ID
        self._auto_id = generate_student_id() if not self.student_id else ""
        id_lbl = QLabel("User ID (auto-generated)")
        id_lbl.setStyleSheet(FORM_LABEL_STYLE)
        fl.addWidget(id_lbl)
        self.id_display = QLineEdit(self._auto_id)
        self.id_display.setReadOnly(True)
        self.id_display.setStyleSheet(INPUT_READONLY_STYLE)
        self.id_display.setFixedHeight(36)
        fl.addWidget(self.id_display)
        fl.addSpacing(2)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(INPUT_STYLE)
        self.name_input.setFixedHeight(36)
        self.name_input.setPlaceholderText("Full name")

        self.phone_input = QLineEdit()
        self.phone_input.setStyleSheet(INPUT_STYLE)
        self.phone_input.setFixedHeight(36)
        self.phone_input.setPlaceholderText("Phone number")

        self.guardian_input = QLineEdit()
        self.guardian_input.setStyleSheet(INPUT_STYLE)
        self.guardian_input.setFixedHeight(36)
        self.guardian_input.setPlaceholderText("Parent / Guardian name")

        self.whatsapp_input = QLineEdit()
        self.whatsapp_input.setStyleSheet(INPUT_STYLE)
        self.whatsapp_input.setFixedHeight(36)
        self.whatsapp_input.setPlaceholderText("e.g. 9800000000")

        self.address_input = QLineEdit()
        self.address_input.setStyleSheet(INPUT_STYLE)
        self.address_input.setFixedHeight(36)
        self.address_input.setPlaceholderText("Address")

        self.dob_input = BSDateEdit()
        self.dob_input.set_today()

        self.join_date_input = BSDateEdit()
        self.join_date_input.set_today()

        session = get_session()
        classes = [(c.id, c.name) for c in session.query(Class).all()]
        session.close()

        self.class_combo = QComboBox()
        self.class_combo.setStyleSheet(COMBO_STYLE)
        self.class_combo.setFixedHeight(36)
        self.class_combo.addItem("— Select Class —", None)
        for cid, cname in classes:
            self.class_combo.addItem(cname, cid)
        self.class_combo.currentIndexChanged.connect(self._load_groups)

        self.group_combo = QComboBox()
        self.group_combo.setStyleSheet(COMBO_STYLE)
        self.group_combo.setFixedHeight(36)
        self.group_combo.addItem("— Select Group —", None)

        field("Full Name  *",       self.name_input)
        field("Phone",              self.phone_input)
        field("Guardian Name",      self.guardian_input)
        field("WhatsApp Number",    self.whatsapp_input)
        field("Address",            self.address_input)
        field("Date of Birth (BS)", self.dob_input)
        field("Join Date (BS)",     self.join_date_input)
        field("Class",              self.class_combo)
        field("Group",              self.group_combo)

        if not self.student_id:
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("background: #eeeeee; border: none;")
            fl.addWidget(sep)

            sub_lbl = QLabel("INITIAL SUBSCRIPTION")
            sub_lbl.setStyleSheet(SECTION_LABEL_STYLE)
            fl.addWidget(sub_lbl)

            self.duration_spin = QSpinBox()
            self.duration_spin.setRange(1, 24)
            self.duration_spin.setValue(1)
            self.duration_spin.setSuffix("  month(s)")
            self.duration_spin.setStyleSheet(SPINBOX_STYLE)
            self.duration_spin.setFixedHeight(36)

            self.fee_spin = QDoubleSpinBox()
            self.fee_spin.setRange(0, 999999)
            self.fee_spin.setValue(2000)
            self.fee_spin.setPrefix("Rs. ")
            self.fee_spin.setDecimals(0)
            self.fee_spin.setStyleSheet(SPINBOX_STYLE)
            self.fee_spin.setFixedHeight(36)

            field("Duration",  self.duration_spin)
            field("Total Fee", self.fee_spin)

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
        label = "Save Student" if not self.student_id else "Update Student"
        save  = QPushButton(label)
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self._save)
        br.addWidget(cancel)
        br.addStretch()
        br.addWidget(save)
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
        uid, name      = s.user_id, s.name
        phone, addr    = s.phone or "", s.address or ""
        guardian       = s.guardian_name or ""
        whatsapp       = s.whatsapp_number or ""
        dob, jd        = s.dob, s.join_date
        cid, gid       = s.class_id, s.group_id
        session.close()

        self.id_display.setText(uid)
        self.name_input.setText(name)
        self.phone_input.setText(phone)
        self.guardian_input.setText(guardian)
        self.whatsapp_input.setText(whatsapp)
        self.address_input.setText(addr)

        if dob:
            self.dob_input.set_from_ad(dob)
        if jd:
            self.join_date_input.set_from_ad(jd)

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
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Full Name is required.")
            self.name_input.setFocus()
            return

        # Validate WhatsApp number
        wa = self.whatsapp_input.text().strip()
        if wa and not wa.isdigit():
            QMessageBox.warning(
                self, "Validation",
                "WhatsApp number must contain digits only."
            )
            self.whatsapp_input.setFocus()
            return

        dob_ad  = self.dob_input.get_ad_date()
        join_ad = self.join_date_input.get_ad_date()
        if not join_ad:
            QMessageBox.warning(
                self, "Validation",
                "Join Date (BS) is invalid. Please enter a valid BS date."
            )
            return

        session = get_session()
        if self.student_id:
            s = session.query(Student).get(self.student_id)
        else:
            uid = self._auto_id
            dup = session.query(Student).filter_by(user_id=uid).first()
            if dup:
                QMessageBox.warning(
                    self, "Duplicate",
                    f"User ID '{uid}' already exists."
                )
                session.close()
                return
            s = Student()
            s.user_id = uid
            session.add(s)

        s.name            = name
        s.phone           = self.phone_input.text().strip()
        s.guardian_name   = self.guardian_input.text().strip() or None
        s.whatsapp_number = wa or None
        s.address         = self.address_input.text().strip()
        s.class_id        = self.class_combo.currentData()
        s.group_id        = self.group_combo.currentData()
        s.dob             = dob_ad
        s.join_date       = join_ad

        session.commit()
        self.saved_student_id = s.id
        sid = s.id
        session.close()

        if not self.student_id:
            create_subscription(
                student_id      = sid,
                start_date      = join_ad,
                duration_months = self.duration_spin.value(),
                total_fee       = self.fee_spin.value(),
            )
        self.accept()
