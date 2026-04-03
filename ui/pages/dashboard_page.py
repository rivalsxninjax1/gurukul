from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QFrame, QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt
from database.connection import get_session
from models.student import Student
from models.teacher import Teacher
from models.attendance import Attendance
from models.class_group import Class, Group
from datetime import date
from ui.styles import (
    CARD_STYLE, PAGE_TITLE_STYLE, SECTION_LABEL_STYLE
)


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #f5f5f5; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: #f5f5f5;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # ── Title
        title = QLabel("Dashboard")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(title)

        # ── Fetch all data eagerly in one session
        session = get_session()
        total_students   = session.query(Student).count()
        total_teachers   = session.query(Teacher).count()
        total_classes    = session.query(Class).count()
        total_groups     = session.query(Group).count()
        today_present    = session.query(Attendance).filter_by(
            date=date.today(), status="Present").count()
        today_incomplete = session.query(Attendance).filter_by(
            date=date.today(), status="Incomplete").count()

        classes_data = []
        for cls in session.query(Class).all():
            groups_data = []
            for g in cls.groups:
                groups_data.append({
                    "name":          g.name,
                    "student_count": len(g.students),
                })
            classes_data.append({
                "name":   cls.name,
                "groups": groups_data,
            })
        session.close()

        # ── Overview section label
        ovr_lbl = QLabel("OVERVIEW")
        ovr_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        layout.addWidget(ovr_lbl)

        # ── Stat cards row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        stat_data = [
            ("Total Students",  str(total_students),   "registered"),
            ("Total Teachers",  str(total_teachers),   "registered"),
            ("Classes",         str(total_classes),    "configured"),
            ("Groups",          str(total_groups),     "across all classes"),
            ("Present Today",   str(today_present),    "students"),
            ("Incomplete",      str(today_incomplete), "missing exit"),
        ]
        for label, value, sub in stat_data:
            stats_row.addWidget(self._stat_card(label, value, sub))
        layout.addLayout(stats_row)

        # ── Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background: #e0e0e0; border: none;")
        layout.addWidget(div)

        # ── Classes & groups section
        cls_lbl = QLabel("CLASSES & GROUPS")
        cls_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        layout.addWidget(cls_lbl)

        if classes_data:
            grid = QGridLayout()
            grid.setSpacing(12)
            for i, cls in enumerate(classes_data):
                grid.addWidget(self._class_card(cls), i // 3, i % 3)
            layout.addLayout(grid)
        else:
            empty = QLabel("No classes configured yet.  Go to  Classes & Groups  to add some.")
            empty.setStyleSheet(
                "color: #aaaaaa; font-size: 13px; padding: 24px;"
                "border: 1.5px dashed #dddddd; border-radius: 8px;"
                "background: #ffffff;"
            )
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    # ── Stat card ─────────────────────────────────────────────────────────────

    def _stat_card(self, label, value, sub):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)
        card.setMinimumHeight(104)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(3)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #1a1a1a;"
            "background: transparent; border: none;"
        )

        title_lbl = QLabel(label)
        title_lbl.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #444444;"
            "background: transparent; border: none;"
        )

        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(
            "font-size: 11px; color: #999999;"
            "background: transparent; border: none;"
        )

        inner.addWidget(val_lbl)
        inner.addWidget(title_lbl)
        inner.addWidget(sub_lbl)
        return card

    # ── Class card ────────────────────────────────────────────────────────────

    def _class_card(self, cls):
        card = QFrame()
        card.setStyleSheet(CARD_STYLE)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        total_students = sum(g["student_count"] for g in cls["groups"])

        header_row = QHBoxLayout()
        name_lbl = QLabel(cls["name"])
        name_lbl.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #1a1a1a;"
            "background: transparent; border: none;"
        )
        cnt_lbl = QLabel(f"{total_students} student{'s' if total_students != 1 else ''}")
        cnt_lbl.setStyleSheet(
            "font-size: 11px; color: #444444; background: #eeeeee;"
            "border-radius: 10px; padding: 2px 9px; border: none;"
        )
        header_row.addWidget(name_lbl)
        header_row.addStretch()
        header_row.addWidget(cnt_lbl)
        layout.addLayout(header_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #eeeeee; border: none;")
        layout.addWidget(sep)

        if cls["groups"]:
            for g in cls["groups"]:
                pill_row = QHBoxLayout()
                pill_row.setSpacing(0)

                g_name = QLabel(g["name"])
                g_name.setStyleSheet(
                    "font-size: 12px; color: #333333;"
                    "background: #f5f5f5; border: 1px solid #e0e0e0;"
                    "border-radius: 4px; padding: 4px 10px;"
                )

                g_count = QLabel(f"  {g['student_count']} student{'s' if g['student_count'] != 1 else ''}")
                g_count.setStyleSheet(
                    "font-size: 12px; color: #777777;"
                    "background: transparent; border: none;"
                )

                pill_row.addWidget(g_name)
                pill_row.addWidget(g_count)
                pill_row.addStretch()
                layout.addLayout(pill_row)
        else:
            no_grp = QLabel("No groups added yet")
            no_grp.setStyleSheet(
                "font-size: 12px; color: #bbbbbb; font-style: italic;"
                "background: transparent; border: none;"
            )
            layout.addWidget(no_grp)

        return card