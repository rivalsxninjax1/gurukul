from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit,
    QMessageBox, QHeaderView, QFrame, QSplitter, QListWidget,
    QListWidgetItem, QAbstractItemView, QDoubleSpinBox,
    QScrollArea, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from database.connection import get_session
from models.student import Student
from models.exam import Exam, ExamSubject, StudentResult
from services.exam_service import (
    get_all_exams, create_exam, delete_exam,
    get_subjects_for_exam, add_subject, delete_subject,
    save_result, get_results_for_student,
)
from ui.styles import (
    BTN_PRIMARY, BTN_DANGER, BTN_SECONDARY,
    TABLE_STYLE, INPUT_STYLE, COMBO_STYLE, SPINBOX_STYLE,
    DIALOG_STYLE, FORM_LABEL_STYLE, PAGE_TITLE_STYLE,
    PANEL_TITLE_STYLE, CARD_STYLE, SECTION_LABEL_STYLE,
    LIST_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
    apply_msgbox_style,
)
from ui.event_bus import bus
from ui.widgets import Toast


class ExamsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._selected_exam_id = None
        self._build_ui()
        self._load_exams()
        # Real-time: refresh student list when a new student is saved
        bus.student_saved.connect(self._populate_students)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(16)

        title = QLabel("Examinations")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        root.addWidget(title)

        self.toast = Toast()
        root.addWidget(self.toast)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(10)
        splitter.setStyleSheet("QSplitter::handle { background: #e0e0e0; }")
        splitter.addWidget(self._build_exam_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([300, 700])
        root.addWidget(splitter)

    def _build_exam_panel(self):
        frame = QFrame()
        frame.setStyleSheet(CARD_STYLE)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("Exams")
        lbl.setStyleSheet(PANEL_TITLE_STYLE)
        add_btn = QPushButton("+ New Exam")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_exam)
        hdr.addWidget(lbl)
        hdr.addStretch()
        hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        self.exam_list = QListWidget()
        self.exam_list.setStyleSheet(LIST_STYLE)
        self.exam_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.exam_list.itemSelectionChanged.connect(self._on_exam_selected)
        layout.addWidget(self.exam_list)

        del_btn = QPushButton("Delete Selected Exam")
        del_btn.setStyleSheet(BTN_DANGER)
        del_btn.clicked.connect(self._delete_exam)
        layout.addWidget(del_btn)
        return frame

    def _build_right_panel(self):
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Subjects card
        sub_frame = QFrame()
        sub_frame.setStyleSheet(CARD_STYLE)
        sub_cl = QVBoxLayout(sub_frame)
        sub_cl.setContentsMargins(0, 0, 0, 0)
        sub_cl.setSpacing(0)

        sub_hdr_w = QWidget()
        sub_hdr_w.setStyleSheet(
            "background: #ffffff; border-bottom: 1px solid #eeeeee;"
        )
        sub_hdr_l = QHBoxLayout(sub_hdr_w)
        sub_hdr_l.setContentsMargins(16, 10, 16, 10)
        sub_lbl = QLabel("Subjects for Selected Exam")
        sub_lbl.setStyleSheet(PANEL_TITLE_STYLE)
        add_sub_btn = QPushButton("+ Add Subject")
        add_sub_btn.setStyleSheet(BTN_SECONDARY)
        add_sub_btn.clicked.connect(self._add_subject)
        sub_hdr_l.addWidget(sub_lbl)
        sub_hdr_l.addStretch()
        sub_hdr_l.addWidget(add_sub_btn)
        sub_cl.addWidget(sub_hdr_w)

        self.subject_table = QTableWidget()
        self.subject_table.setColumnCount(4)
        self.subject_table.setHorizontalHeaderLabels(
            ["Subject", "Full Marks", "Pass Marks", "Actions"]
        )
        sh = self.subject_table.horizontalHeader()
        sh.setSectionResizeMode(0, QHeaderView.Stretch)
        sh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        sh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        sh.setSectionResizeMode(3, QHeaderView.Fixed)
        self.subject_table.setColumnWidth(3, 90)
        self.subject_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.subject_table.setAlternatingRowColors(True)
        self.subject_table.setStyleSheet(TABLE_STYLE)
        self.subject_table.verticalHeader().setVisible(False)
        self.subject_table.setFrameShape(QFrame.NoFrame)
        self.subject_table.setMaximumHeight(220)
        sub_cl.addWidget(self.subject_table)
        layout.addWidget(sub_frame)

        # Marks entry card
        marks_frame = QFrame()
        marks_frame.setStyleSheet(CARD_STYLE)
        marks_cl = QVBoxLayout(marks_frame)
        marks_cl.setContentsMargins(0, 0, 0, 0)
        marks_cl.setSpacing(0)

        marks_hdr_w = QWidget()
        marks_hdr_w.setStyleSheet(
            "background: #ffffff; border-bottom: 1px solid #eeeeee;"
        )
        marks_hdr_l = QHBoxLayout(marks_hdr_w)
        marks_hdr_l.setContentsMargins(16, 10, 16, 10)
        marks_lbl = QLabel("Enter Marks")
        marks_lbl.setStyleSheet(PANEL_TITLE_STYLE)

        student_lbl = QLabel("Student:")
        student_lbl.setStyleSheet(
            "font-size: 12px; color: #555555; background: transparent;"
        )
        self.student_combo = QComboBox()
        self.student_combo.setStyleSheet(COMBO_STYLE)
        self.student_combo.setFixedHeight(34)
        self.student_combo.setFixedWidth(220)
        self._populate_students()
        self.student_combo.currentIndexChanged.connect(self._load_marks_table)

        save_marks_btn = QPushButton("Save All Marks")
        save_marks_btn.setStyleSheet(BTN_PRIMARY)
        save_marks_btn.clicked.connect(self._save_marks)

        marks_hdr_l.addWidget(marks_lbl)
        marks_hdr_l.addSpacing(12)
        marks_hdr_l.addWidget(student_lbl)
        marks_hdr_l.addWidget(self.student_combo)
        marks_hdr_l.addStretch()
        marks_hdr_l.addWidget(save_marks_btn)
        marks_cl.addWidget(marks_hdr_w)

        self.marks_table = QTableWidget()
        self.marks_table.setColumnCount(5)
        self.marks_table.setHorizontalHeaderLabels(
            ["Subject", "Full Marks", "Pass Marks", "Marks Obtained", "Pass/Fail"]
        )
        mh = self.marks_table.horizontalHeader()
        mh.setSectionResizeMode(0, QHeaderView.Stretch)
        mh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        mh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        mh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        mh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.marks_table.setAlternatingRowColors(True)
        self.marks_table.setStyleSheet(TABLE_STYLE)
        self.marks_table.verticalHeader().setVisible(False)
        self.marks_table.setFrameShape(QFrame.NoFrame)
        marks_cl.addWidget(self.marks_table)
        layout.addWidget(marks_frame)
        return frame

    # ── Data loading ──────────────────────────────────────────────────────────

    def _populate_students(self):
        """Reload student dropdown — called on init and on bus.student_saved."""
        prev_id = self.student_combo.currentData() \
                  if self.student_combo.count() > 0 else None
        session = get_session()
        students = session.query(Student).order_by(Student.name).all()
        self.student_combo.blockSignals(True)
        self.student_combo.clear()
        self.student_combo.addItem("— Select Student —", None)
        restore_idx = 0
        for i, s in enumerate(students, 1):
            self.student_combo.addItem(f"{s.name}  ({s.user_id})", s.id)
            if s.id == prev_id:
                restore_idx = i
        self.student_combo.setCurrentIndex(restore_idx)
        self.student_combo.blockSignals(False)
        session.close()
        # Reload marks table for newly selected student
        self._load_marks_table()

    def _load_exams(self):
        exams = get_all_exams()
        self.exam_list.clear()
        for e in exams:
            item = QListWidgetItem(
                f"  {e['name']}  ({e['subject_count']} subject(s))"
            )
            item.setData(Qt.UserRole, e["id"])
            self.exam_list.addItem(item)

    def _on_exam_selected(self):
        item = self.exam_list.currentItem()
        if not item:
            return
        self._selected_exam_id = item.data(Qt.UserRole)
        self._load_subjects()
        self._load_marks_table()

    def _load_subjects(self):
        if not self._selected_exam_id:
            return
        subjects = get_subjects_for_exam(self._selected_exam_id)
        self.subject_table.setRowCount(len(subjects))
        for r, sub in enumerate(subjects):
            self.subject_table.setItem(r, 0, QTableWidgetItem(sub["subject_name"]))
            self.subject_table.setItem(r, 1, QTableWidgetItem(str(sub["full_marks"])))
            self.subject_table.setItem(r, 2, QTableWidgetItem(str(sub["pass_marks"])))
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(
                lambda _, sid=sub["id"]: self._delete_subject(sid)
            )
            self.subject_table.setCellWidget(r, 3, del_btn)
            for col in range(3):
                item = self.subject_table.item(r, col)
                if item:
                    item.setForeground(Qt.black)
            self.subject_table.setRowHeight(r, 40)

    def _load_marks_table(self):
        if not self._selected_exam_id:
            return
        student_id = self.student_combo.currentData()
        subjects   = get_subjects_for_exam(self._selected_exam_id)
        self.marks_table.setRowCount(len(subjects))
        self._marks_widgets = {}

        session = get_session()
        for r, sub in enumerate(subjects):
            existing = None
            if student_id:
                existing = session.query(StudentResult).filter_by(
                    student_id=student_id,
                    exam_id=self._selected_exam_id,
                    subject_id=sub["id"]
                ).first()

            self.marks_table.setItem(r, 0, QTableWidgetItem(sub["subject_name"]))
            self.marks_table.setItem(r, 1, QTableWidgetItem(str(sub["full_marks"])))
            self.marks_table.setItem(r, 2, QTableWidgetItem(str(sub["pass_marks"])))

            spin = QDoubleSpinBox()
            spin.setRange(0, sub["full_marks"])
            spin.setDecimals(1)
            spin.setStyleSheet(SPINBOX_STYLE)
            if existing:
                spin.setValue(existing.marks)

            # Capture row index for pass/fail update
            def make_handler(row, pass_marks):
                def handler(val):
                    self._update_pass_fail(row, val, pass_marks)
                return handler

            spin.valueChanged.connect(
                make_handler(r, sub["pass_marks"])
            )
            self.marks_table.setCellWidget(r, 3, spin)
            self._marks_widgets[sub["id"]] = spin

            pf_item = QTableWidgetItem("—")
            pf_item.setForeground(Qt.black)
            if existing:
                if existing.marks >= sub["pass_marks"]:
                    pf_item.setText("Pass")
                    pf_item.setForeground(QColor(STATUS_PRESENT))
                    pf_item.setBackground(QColor(STATUS_PRESENT_BG))
                else:
                    pf_item.setText("Fail")
                    pf_item.setForeground(QColor(STATUS_ABSENT))
                    pf_item.setBackground(QColor(STATUS_ABSENT_BG))
            self.marks_table.setItem(r, 4, pf_item)

            for col in range(3):
                item = self.marks_table.item(r, col)
                if item:
                    item.setForeground(Qt.black)
            self.marks_table.setRowHeight(r, 44)

        session.close()

    def _update_pass_fail(self, row, marks, pass_marks):
        item = self.marks_table.item(row, 4)
        if not item:
            item = QTableWidgetItem()
            self.marks_table.setItem(row, 4, item)
        if marks >= pass_marks:
            item.setText("Pass")
            item.setForeground(QColor(STATUS_PRESENT))
            item.setBackground(QColor(STATUS_PRESENT_BG))
        else:
            item.setText("Fail")
            item.setForeground(QColor(STATUS_ABSENT))
            item.setBackground(QColor(STATUS_ABSENT_BG))

    # ── Actions ───────────────────────────────────────────────────────────────

    def _add_exam(self):
        dlg = NameDialog("New Exam", "Exam name (e.g. Mid Term, Final):",
                         parent=self)
        if dlg.exec_():
            name = dlg.get_value()
            if name:
                create_exam(name)
                self._load_exams()
                self.toast.success(f'Exam "{name}" created.')

    def _delete_exam(self):
        item = self.exam_list.currentItem()
        if not item:
            QMessageBox.information(self, "Select Exam",
                                    "Please select an exam to delete.")
            return
        name    = item.text().strip()
        exam_id = item.data(Qt.UserRole)
        mb = QMessageBox(self)
        mb.setWindowTitle("Confirm Delete")
        mb.setText(f'Delete exam "{name}" and all its data?')
        mb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        apply_msgbox_style(mb)
        if mb.exec_() == QMessageBox.Yes:
            delete_exam(exam_id)
            self._selected_exam_id = None
            self.subject_table.setRowCount(0)
            self.marks_table.setRowCount(0)
            self._load_exams()
            self.toast.success("Exam deleted.")

    def _add_subject(self):
        if not self._selected_exam_id:
            QMessageBox.information(self, "Select Exam",
                                    "Please select an exam first.")
            return
        dlg = SubjectDialog(parent=self)
        if dlg.exec_():
            vals = dlg.get_values()
            if vals["name"]:
                add_subject(
                    self._selected_exam_id,
                    vals["name"], vals["full"], vals["pass"],
                )
                self._load_subjects()
                self._load_marks_table()
                self.toast.success(f'Subject "{vals["name"]}" added.')

    def _delete_subject(self, subject_id):
        mb = QMessageBox(self)
        mb.setWindowTitle("Confirm Delete")
        mb.setText("Delete this subject and all its marks?")
        mb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        apply_msgbox_style(mb)
        if mb.exec_() == QMessageBox.Yes:
            delete_subject(subject_id)
            self._load_subjects()
            self._load_marks_table()
            self.toast.success("Subject deleted.")

    def _save_marks(self):
        student_id = self.student_combo.currentData()
        if not student_id:
            QMessageBox.information(self, "Select Student",
                                    "Please select a student.")
            return
        if not self._selected_exam_id:
            QMessageBox.information(self, "Select Exam",
                                    "Please select an exam.")
            return
        for subject_id, spin in self._marks_widgets.items():
            save_result(student_id, self._selected_exam_id,
                        subject_id, spin.value())
        self.toast.success("Marks saved successfully.")
        self._load_marks_table()


# ── Dialogs ───────────────────────────────────────────────────────────────────

class NameDialog(QDialog):
    def __init__(self, title, prompt, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(360)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui(prompt)

    def _build_ui(self, prompt):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(24, 24, 24, 16)
        fl.setSpacing(10)

        lbl = QLabel(prompt)
        lbl.setStyleSheet(FORM_LABEL_STYLE)
        fl.addWidget(lbl)

        self.input = QLineEdit()
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
        br.setContentsMargins(24, 12, 24, 12)
        br.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self.accept)
        br.addWidget(cancel)
        br.addSpacing(8)
        br.addWidget(save)
        root.addWidget(footer)

    def get_value(self):
        return self.input.text().strip()


class SubjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Subject")
        self.setFixedWidth(380)
        self.setStyleSheet(DIALOG_STYLE)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        inner = QFrame()
        inner.setStyleSheet("QFrame { background: #ffffff; border: none; }")
        fl = QVBoxLayout(inner)
        fl.setContentsMargins(24, 24, 24, 16)
        fl.setSpacing(14)

        def field(lbl_text, widget):
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(FORM_LABEL_STYLE)
            fl.addWidget(lbl)
            fl.addWidget(widget)
            fl.addSpacing(2)

        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(INPUT_STYLE)
        self.name_input.setFixedHeight(36)
        self.name_input.setPlaceholderText("e.g. Mathematics")

        self.full_spin = QDoubleSpinBox()
        self.full_spin.setRange(1, 1000)
        self.full_spin.setValue(100)
        self.full_spin.setDecimals(0)
        self.full_spin.setStyleSheet(SPINBOX_STYLE)
        self.full_spin.setFixedHeight(36)

        self.pass_spin = QDoubleSpinBox()
        self.pass_spin.setRange(1, 1000)
        self.pass_spin.setValue(40)
        self.pass_spin.setDecimals(0)
        self.pass_spin.setStyleSheet(SPINBOX_STYLE)
        self.pass_spin.setFixedHeight(36)

        field("Subject Name  *", self.name_input)
        field("Full Marks",      self.full_spin)
        field("Pass Marks",      self.pass_spin)
        root.addWidget(inner)

        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: #f5f5f5; border-top: 1px solid #e8e8e8; }"
        )
        br = QHBoxLayout(footer)
        br.setContentsMargins(24, 12, 24, 12)
        br.addStretch()
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(BTN_SECONDARY)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Add Subject")
        save.setStyleSheet(BTN_PRIMARY)
        save.clicked.connect(self._save)
        br.addWidget(cancel)
        br.addSpacing(8)
        br.addWidget(save)
        root.addWidget(footer)

    def _save(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation",
                                "Subject name is required.")
            return
        self.accept()

    def get_values(self):
        return {
            "name": self.name_input.text().strip(),
            "full": self.full_spin.value(),
            "pass": self.pass_spin.value(),
        }