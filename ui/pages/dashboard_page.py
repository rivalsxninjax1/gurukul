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
from services.subscription_service import get_subscription_dashboard_stats
from datetime import date
from ui.styles import (
    CARD_STYLE, PAGE_TITLE_STYLE, SECTION_LABEL_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
    STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG,
)


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._stat_cards = {}
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: #f5f5f5; border: none; }"
        )
        content = QWidget()
        content.setStyleSheet("background: #f5f5f5;")
        self._layout = QVBoxLayout(content)
        self._layout.setContentsMargins(30, 30, 30, 30)
        self._layout.setSpacing(20)

        title = QLabel("Dashboard")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        self._layout.addWidget(title)

        # Overview cards
        ovr = QLabel("OVERVIEW")
        ovr.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(ovr)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        defs = [
            ("students",       "Total Students",    "registered",       "#333333", "#f5f5f5"),
            ("teachers",       "Total Teachers",    "registered",       "#333333", "#f5f5f5"),
            ("present",        "Present Today",     "students",         "#333333", "#f5f5f5"),
            ("active_subs",    "Active",            "subscriptions",    STATUS_PRESENT, STATUS_PRESENT_BG),
            ("expired_subs",   "Expired",           "subscriptions",    STATUS_ABSENT,  STATUS_ABSENT_BG),
            ("pending_subs",   "Payment Pending",   "students",         STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG),
        ]
        for key, label, sub, fg, bg in defs:
            card, v, s = self._make_stat_card(label, "—", sub, fg, bg)
            self._stat_cards[key] = (v, s)
            stats_row.addWidget(card)
        self._layout.addLayout(stats_row)

        # Revenue row
        rev_lbl = QLabel("REVENUE")
        rev_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(rev_lbl)

        rev_row = QHBoxLayout()
        rev_row.setSpacing(12)
        rev_defs = [
            ("revenue",  "Total Collected", "from all payments",   STATUS_PRESENT, STATUS_PRESENT_BG),
            ("pending_amount", "Pending Amount", "outstanding balance", STATUS_ABSENT, STATUS_ABSENT_BG),
        ]
        for key, label, sub, fg, bg in rev_defs:
            card, v, s = self._make_stat_card(label, "—", sub, fg, bg)
            self._stat_cards[key] = (v, s)
            rev_row.addWidget(card)
        rev_row.addStretch()
        self._layout.addLayout(rev_row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background: #e0e0e0; border: none;")
        self._layout.addWidget(div)

        # Classes section
        cls_lbl = QLabel("CLASSES & GROUPS")
        cls_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(cls_lbl)

        self._classes_container = QWidget()
        self._classes_container.setStyleSheet("background: transparent;")
        self._classes_grid = QGridLayout(self._classes_container)
        self._classes_grid.setSpacing(12)
        self._layout.addWidget(self._classes_container)

        self._layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def refresh(self):
        session = get_session()
        total_students = session.query(Student).count()
        total_teachers = session.query(Teacher).count()
        today_present  = session.query(Attendance).filter_by(
            date=date.today(), status="Present"
        ).count()
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

        sub_stats = get_subscription_dashboard_stats()

        updates = {
            "students":      (str(total_students),  "registered"),
            "teachers":      (str(total_teachers),  "registered"),
            "present":       (str(today_present),   "today"),
            "active_subs":   (str(sub_stats["active"]),   "subscriptions"),
            "expired_subs":  (str(sub_stats["expired"]),  "subscriptions"),
            "pending_subs":  (str(sub_stats["pending"]),  "students"),
            "revenue":       (f"Rs.{sub_stats['total_revenue']:,.0f}", "collected"),
            "pending_amount":(f"Rs.{sub_stats['total_pending']:,.0f}", "outstanding"),
        }
        for key, (val, sub) in updates.items():
            v, s = self._stat_cards[key]
            v.setText(val)
            s.setText(sub)

        # Rebuild classes grid
        while self._classes_grid.count():
            item = self._classes_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if classes_data:
            for i, cls in enumerate(classes_data):
                self._classes_grid.addWidget(
                    self._class_card(cls), i // 3, i % 3
                )
        else:
            empty = QLabel(
                "No classes configured yet. "
                "Go to Classes & Groups to add some."
            )
            empty.setStyleSheet(
                "color: #aaaaaa; font-size: 13px; padding: 24px;"
                "border: 1.5px dashed #dddddd; border-radius: 8px;"
                "background: #ffffff;"
            )
            empty.setAlignment(Qt.AlignCenter)
            self._classes_grid.addWidget(empty, 0, 0)

    def _make_stat_card(self, label, value, sub, fg="#333333", bg="#f5f5f5"):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
        """)
        card.setMinimumHeight(100)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 14, 16, 14)
        inner.setSpacing(3)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"font-size: 26px; font-weight: bold; color: {fg};"
            "background: transparent; border: none;"
        )
        title_lbl = QLabel(label)
        title_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {fg};"
            "background: transparent; border: none;"
        )
        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(
            f"font-size: 11px; color: {fg}; opacity: 0.7;"
            "background: transparent; border: none;"
        )
        inner.addWidget(val_lbl)
        inner.addWidget(title_lbl)
        inner.addWidget(sub_lbl)
        return card, val_lbl, sub_lbl

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
        cnt_lbl = QLabel(
            f"{total_students} student{'s' if total_students != 1 else ''}"
        )
        cnt_lbl.setStyleSheet(
            "font-size: 11px; color: #444444; background: #eeeeee;"
            "border-radius: 10px; padding: 2px 9px; border: none;"
        )
        header_row.addWidget(name_lbl)
        header_row.addStretch()
        header_row.addWidget(cnt_lbl)
        layout.addLayout(header_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #eeeeee; border: none;")
        layout.addWidget(sep)

        if cls["groups"]:
            for g in cls["groups"]:
                row = QHBoxLayout()
                g_name = QLabel(g["name"])
                g_name.setStyleSheet(
                    "font-size: 12px; color: #333333;"
                    "background: #f5f5f5; border: 1px solid #e0e0e0;"
                    "border-radius: 4px; padding: 4px 10px;"
                )
                g_cnt = QLabel(
                    f"  {g['student_count']} "
                    f"student{'s' if g['student_count'] != 1 else ''}"
                )
                g_cnt.setStyleSheet(
                    "font-size: 12px; color: #777777;"
                    "background: transparent; border: none;"
                )
                row.addWidget(g_name)
                row.addWidget(g_cnt)
                row.addStretch()
                layout.addLayout(row)
        else:
            no_grp = QLabel("No groups added yet")
            no_grp.setStyleSheet(
                "font-size: 12px; color: #bbbbbb; font-style: italic;"
                "background: transparent; border: none;"
            )
            layout.addWidget(no_grp)

        return card