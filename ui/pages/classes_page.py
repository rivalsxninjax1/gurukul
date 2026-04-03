from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QLineEdit, QMessageBox, QHeaderView, QSplitter, QFrame,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from database.connection import get_session
from models.class_group import Class, Group


# ─── Shared style helpers ───────────────────────────────────────────────────

BTN_PRIMARY = """
    QPushButton {
        background: #1a1a1a; color: #ffffff;
        padding: 7px 16px; border-radius: 5px;
        font-size: 13px; font-weight: bold; border: none;
    }
    QPushButton:hover   { background: #3a3a3a; }
    QPushButton:pressed { background: #000000; }
"""

BTN_DANGER = """
    QPushButton {
        background: #c0392b; color: #ffffff;
        padding: 5px 12px; border-radius: 5px;
        font-size: 12px; border: none;
    }
    QPushButton:hover   { background: #e74c3c; }
    QPushButton:pressed { background: #a93226; }
"""

BTN_SECONDARY = """
    QPushButton {
        background: #4a4a4a; color: #ffffff;
        padding: 5px 12px; border-radius: 5px;
        font-size: 12px; border: none;
    }
    QPushButton:hover   { background: #666666; }
    QPushButton:pressed { background: #333333; }
"""

TABLE_STYLE = """
    QTableWidget {
        border: 1px solid #d0d0d0;
        gridline-color: #e8e8e8;
        background: #ffffff;
        alternate-background-color: #f9f9f9;
        font-size: 13px;
        color: #1a1a1a;
    }
    QHeaderView::section {
        background: #2c2c2c;
        color: #ffffff;
        padding: 9px 8px;
        font-size: 13px;
        font-weight: bold;
        border: none;
    }
    QTableWidget::item:selected {
        background: #e8e8e8;
        color: #1a1a1a;
    }
"""

PANEL_STYLE = """
    QFrame {
        background: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 8px;
    }
"""

LIST_STYLE = """
    QListWidget {
        border: 1px solid #d0d0d0;
        border-radius: 6px;
        background: #ffffff;
        font-size: 13px;
        color: #1a1a1a;
        padding: 4px;
    }
    QListWidget::item {
        padding: 8px 10px;
        border-radius: 4px;
        margin: 2px 0;
    }
    QListWidget::item:selected {
        background: #2c2c2c;
        color: #ffffff;
    }
    QListWidget::item:hover:!selected {
        background: #f0f0f0;
    }
"""

SECTION_LABEL_STYLE = "font-size: 11px; color: #888888; font-weight: bold; letter-spacing: 1px;"
PAGE_TITLE_STYLE    = "font-size: 20px; font-weight: bold; color: #1a1a1a;"
PANEL_TITLE_STYLE   = "font-size: 15px; font-weight: bold; color: #1a1a1a;"
COUNT_BADGE_STYLE   = """
    QLabel {
        background: #2c2c2c; color: #ffffff;
        border-radius: 10px; padding: 1px 8px;
        font-size: 11px; font-weight: bold;
    }
"""


class ClassesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_class_id = None
        self._build_ui()
        self.refresh_classes()

    # ── Main layout ──────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 30, 30, 30)
        root.setSpacing(20)

        # ── Page header
        header = QHBoxLayout()
        title = QLabel("Classes & Groups")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        header.addWidget(title)
        header.addStretch()
        root.addLayout(header)

        # ── Two-panel splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(12)
        splitter.setStyleSheet("QSplitter::handle { background: #e0e0e0; }")

        splitter.addWidget(self._build_classes_panel())
        splitter.addWidget(self._build_groups_panel())
        splitter.setSizes([420, 520])

        root.addWidget(splitter)

    # ── Left panel: classes ──────────────────────────────────────────────────

    def _build_classes_panel(self):
        frame = QFrame()
        frame.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header row
        hdr = QHBoxLayout()
        lbl = QLabel("Classes")
        lbl.setStyleSheet(PANEL_TITLE_STYLE)
        self.class_count_badge = QLabel("0")
        self.class_count_badge.setStyleSheet(COUNT_BADGE_STYLE)

        add_btn = QPushButton("+ Add Class")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_class)

        hdr.addWidget(lbl)
        hdr.addWidget(self.class_count_badge)
        hdr.addStretch()
        hdr.addWidget(add_btn)
        layout.addLayout(hdr)

        hint = QLabel("Select a class to manage its groups →")
        hint.setStyleSheet("font-size: 12px; color: #999999;")
        layout.addWidget(hint)

        # Table
        self.class_table = QTableWidget()
        self.class_table.setColumnCount(4)
        self.class_table.setHorizontalHeaderLabels(["ID", "Class Name", "Groups", "Actions"])
        self.class_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.class_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.class_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.class_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.class_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.class_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.class_table.setAlternatingRowColors(True)
        self.class_table.setStyleSheet(TABLE_STYLE)
        self.class_table.verticalHeader().setVisible(False)
        self.class_table.itemSelectionChanged.connect(self._on_class_selected)
        layout.addWidget(self.class_table)

        return frame

    # ── Right panel: groups ──────────────────────────────────────────────────

    def _build_groups_panel(self):
        frame = QFrame()
        frame.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header row
        hdr = QHBoxLayout()
        self.group_panel_title = QLabel("Groups")
        self.group_panel_title.setStyleSheet(PANEL_TITLE_STYLE)
        self.group_count_badge = QLabel("0")
        self.group_count_badge.setStyleSheet(COUNT_BADGE_STYLE)

        self.add_group_btn = QPushButton("+ Add Group")
        self.add_group_btn.setStyleSheet(BTN_PRIMARY)
        self.add_group_btn.setEnabled(False)
        self.add_group_btn.clicked.connect(self._add_group)

        hdr.addWidget(self.group_panel_title)
        hdr.addWidget(self.group_count_badge)
        hdr.addStretch()
        hdr.addWidget(self.add_group_btn)
        layout.addLayout(hdr)

        self.group_hint = QLabel("← Select a class first")
        self.group_hint.setStyleSheet("font-size: 12px; color: #999999;")
        layout.addWidget(self.group_hint)

        # Group list
        self.group_list = QListWidget()
        self.group_list.setStyleSheet(LIST_STYLE)
        self.group_list.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.group_list)

        # Delete selected group button
        del_row = QHBoxLayout()
        del_row.addStretch()
        self.del_group_btn = QPushButton("Delete Selected Group")
        self.del_group_btn.setStyleSheet(BTN_DANGER)
        self.del_group_btn.setEnabled(False)
        self.del_group_btn.clicked.connect(self._delete_group)
        del_row.addWidget(self.del_group_btn)
        layout.addLayout(del_row)

        # Students in selected group (bonus info panel)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #e0e0e0; border: none; max-height: 1px;")
        layout.addWidget(sep)

        students_lbl = QLabel("STUDENTS IN SELECTED GROUP")
        students_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        layout.addWidget(students_lbl)

        self.students_list = QListWidget()
        self.students_list.setStyleSheet(LIST_STYLE)
        self.students_list.setMaximumHeight(160)
        self.students_list.setSelectionMode(QAbstractItemView.NoSelection)
        layout.addWidget(self.students_list)

        self.group_list.itemSelectionChanged.connect(self._on_group_selected)

        return frame

    # ── Data loaders ─────────────────────────────────────────────────────────

    def refresh_classes(self):
        session = get_session()
        classes = session.query(Class).all()

        self.class_table.setRowCount(len(classes))
        self.class_count_badge.setText(str(len(classes)))

        for row, c in enumerate(classes):
            group_count = len(c.groups)

            id_item = QTableWidgetItem(str(c.id))
            id_item.setTextAlignment(Qt.AlignCenter)
            name_item = QTableWidgetItem(c.name)

            cnt_item = QTableWidgetItem(str(group_count))
            cnt_item.setTextAlignment(Qt.AlignCenter)
            if group_count == 0:
                cnt_item.setForeground(QColor("#999999"))

            self.class_table.setItem(row, 0, id_item)
            self.class_table.setItem(row, 1, name_item)
            self.class_table.setItem(row, 2, cnt_item)

            # Action buttons cell
            action_w = QWidget()
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(4, 3, 4, 3)
            action_l.setSpacing(6)

            edit_btn = QPushButton("Rename")
            edit_btn.setStyleSheet(BTN_SECONDARY)
            edit_btn.clicked.connect(lambda _, cid=c.id, cname=c.name: self._rename_class(cid, cname))

            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(lambda _, cid=c.id: self._delete_class(cid))

            action_l.addWidget(edit_btn)
            action_l.addWidget(del_btn)
            self.class_table.setCellWidget(row, 3, action_w)
            self.class_table.setRowHeight(row, 44)

        session.close()

        # Reset group panel if selected class is gone
        if self.selected_class_id is not None:
            self._refresh_groups_for(self.selected_class_id)

    def _refresh_groups_for(self, class_id):
        session = get_session()
        cls = session.query(Class).get(class_id)

        self.group_list.clear()
        self.students_list.clear()

        if not cls:
            self.selected_class_id = None
            self.add_group_btn.setEnabled(False)
            self.del_group_btn.setEnabled(False)
            self.group_panel_title.setText("Groups")
            self.group_count_badge.setText("0")
            self.group_hint.setText("← Select a class first")
            session.close()
            return

        self.group_panel_title.setText(f"Groups  —  {cls.name}")
        self.group_count_badge.setText(str(len(cls.groups)))
        self.group_hint.setText(
            f"{len(cls.groups)} group(s) in {cls.name}" if cls.groups
            else f"No groups yet in {cls.name}. Click '+ Add Group'."
        )
        self.add_group_btn.setEnabled(True)

        for g in cls.groups:
            student_count = len(g.students)
            item = QListWidgetItem(f"  {g.name}   ({student_count} student{'s' if student_count != 1 else ''})")
            item.setData(Qt.UserRole, g.id)
            self.group_list.addItem(item)

        session.close()

    # ── Slot: class row selected ─────────────────────────────────────────────

    def _on_class_selected(self):
        rows = self.class_table.selectedItems()
        if not rows:
            return
        class_id = int(self.class_table.item(self.class_table.currentRow(), 0).text())
        self.selected_class_id = class_id
        self._refresh_groups_for(class_id)

    # ── Slot: group item selected ────────────────────────────────────────────

    def _on_group_selected(self):
        item = self.group_list.currentItem()
        self.students_list.clear()
        if not item:
            self.del_group_btn.setEnabled(False)
            return
        self.del_group_btn.setEnabled(True)
        group_id = item.data(Qt.UserRole)

        session = get_session()
        group = session.query(Group).get(group_id)
        if group:
            if group.students:
                for s in group.students:
                    si = QListWidgetItem(f"  {s.name}  ({s.user_id})")
                    self.students_list.addItem(si)
            else:
                placeholder = QListWidgetItem("  No students assigned yet")
                placeholder.setForeground(QColor("#aaaaaa"))
                self.students_list.addItem(placeholder)
        session.close()

    # ── Actions: class ───────────────────────────────────────────────────────

    def _add_class(self):
        dlg = NameInputDialog("Add New Class", "Class name:", parent=self)
        if dlg.exec_():
            name = dlg.get_value()
            if not name:
                return
            session = get_session()
            existing = session.query(Class).filter_by(name=name).first()
            if existing:
                QMessageBox.warning(self, "Duplicate", f'A class named "{name}" already exists.')
                session.close()
                return
            session.add(Class(name=name))
            session.commit()
            session.close()
            self.refresh_classes()

    def _rename_class(self, class_id, current_name):
        dlg = NameInputDialog("Rename Class", "New class name:", default=current_name, parent=self)
        if dlg.exec_():
            name = dlg.get_value()
            if not name or name == current_name:
                return
            session = get_session()
            existing = session.query(Class).filter_by(name=name).first()
            if existing:
                QMessageBox.warning(self, "Duplicate", f'A class named "{name}" already exists.')
                session.close()
                return
            cls = session.query(Class).get(class_id)
            if cls:
                cls.name = name
                session.commit()
            session.close()
            self.refresh_classes()

    def _delete_class(self, class_id):
        session = get_session()
        cls = session.query(Class).get(class_id)
        student_count = len(cls.students) if cls else 0
        group_count   = len(cls.groups)   if cls else 0
        session.close()

        msg = f'Delete class "{cls.name}"?'
        if student_count or group_count:
            msg += f'\n\nThis will also delete {group_count} group(s) and unlink {student_count} student(s).'

        reply = QMessageBox.question(self, "Confirm Delete", msg,
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        session = get_session()
        cls = session.query(Class).get(class_id)
        if cls:
            # Unlink students before delete
            for s in cls.students:
                s.class_id = None
                s.group_id = None
            session.delete(cls)
            session.commit()
        session.close()

        if self.selected_class_id == class_id:
            self.selected_class_id = None
            self.group_list.clear()
            self.students_list.clear()
            self.add_group_btn.setEnabled(False)
            self.del_group_btn.setEnabled(False)
            self.group_panel_title.setText("Groups")
            self.group_count_badge.setText("0")
            self.group_hint.setText("← Select a class first")

        self.refresh_classes()

    # ── Actions: group ───────────────────────────────────────────────────────

    def _add_group(self):
        if not self.selected_class_id:
            return
        session = get_session()
        cls = session.query(Class).get(self.selected_class_id)
        class_name = cls.name if cls else ""
        session.close()

        dlg = NameInputDialog(
            f"Add Group to {class_name}", "Group name (e.g. Morning / Evening):", parent=self
        )
        if dlg.exec_():
            name = dlg.get_value()
            if not name:
                return
            session = get_session()
            existing = session.query(Group).filter_by(
                class_id=self.selected_class_id, name=name
            ).first()
            if existing:
                QMessageBox.warning(self, "Duplicate",
                                    f'Group "{name}" already exists in {class_name}.')
                session.close()
                return
            session.add(Group(name=name, class_id=self.selected_class_id))
            session.commit()
            session.close()
            self.refresh_classes()

    def _delete_group(self):
        item = self.group_list.currentItem()
        if not item:
            return
        group_id   = item.data(Qt.UserRole)
        group_name = item.text().strip().split("  ")[0]

        session = get_session()
        group = session.query(Group).get(group_id)
        student_count = len(group.students) if group else 0
        session.close()

        msg = f'Delete group "{group_name}"?'
        if student_count:
            msg += f'\n\n{student_count} student(s) will be unlinked from this group.'

        reply = QMessageBox.question(self, "Confirm Delete", msg,
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        session = get_session()
        group = session.query(Group).get(group_id)
        if group:
            for s in group.students:
                s.group_id = None
            session.delete(group)
            session.commit()
        session.close()

        self.refresh_classes()
        self.del_group_btn.setEnabled(False)
        self.students_list.clear()


# ─── Reusable name input dialog ──────────────────────────────────────────────

class NameInputDialog(QDialog):
    def __init__(self, title, prompt, default="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedWidth(380)
        self.setStyleSheet("background: #ffffff;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        lbl = QLabel(prompt)
        lbl.setStyleSheet("font-size: 13px; color: #333333;")
        layout.addWidget(lbl)

        self.input = QLineEdit(default)
        self.input.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #cccccc; border-radius: 5px;
                padding: 8px 10px; font-size: 13px; color: #1a1a1a;
                background: #fafafa;
            }
            QLineEdit:focus { border-color: #555555; background: #ffffff; }
        """)
        self.input.setPlaceholderText("Enter name…")
        self.input.returnPressed.connect(self.accept)
        layout.addWidget(self.input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(BTN_SECONDARY)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Save")
        ok_btn.setStyleSheet(BTN_PRIMARY)
        ok_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

    def get_value(self):
        return self.input.text().strip()