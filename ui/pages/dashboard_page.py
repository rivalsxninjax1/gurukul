from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout,
    QFrame, QGridLayout, QScrollArea, QPushButton
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from database.connection import get_session
from models.student import Student
from models.teacher import Teacher
from models.attendance import Attendance
from models.class_group import Class, Group
from services.subscription_service import get_subscription_dashboard_stats
from services.expense_service import (
    get_total_revenue, get_expense_dashboard_stats
)
from utils.bs_converter import today_bs
from utils.logo_helper import logo_pixmap, logo_exists
from datetime import date
from ui.styles import (
    BTN_SECONDARY, CARD_STYLE, PAGE_TITLE_STYLE, SECTION_LABEL_STYLE,
    STATUS_PRESENT, STATUS_PRESENT_BG,
    STATUS_ABSENT, STATUS_ABSENT_BG,
    STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG,
)

CENTRE_NAME    = "GURUKUL ACADEMY AND TRAINING CENTER"
CENTRE_ADDRESS = "Biratnagar-1, Bhatta Chowk"


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

        # ── Branding header ───────────────────────────────────────────────────
        brand_card = QFrame()
        brand_card.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                border-radius: 10px;
                border: none;
            }
        """)
        brand_cl = QHBoxLayout(brand_card)
        brand_cl.setContentsMargins(24, 18, 24, 18)
        brand_cl.setSpacing(16)

        # Logo — PNG if available, else "G" circle fallback
        self._logo_lbl = QLabel()
        self._logo_lbl.setFixedSize(54, 54)
        self._logo_lbl.setAlignment(Qt.AlignCenter)
        self._refresh_logo_widget(self._logo_lbl, 54, 54, fallback_text="G",
                                  dark_bg=True)
        brand_cl.addWidget(self._logo_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        centre_lbl = QLabel(CENTRE_NAME)
        centre_lbl.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #ffffff;"
            "background: transparent; border: none;"
        )
        centre_lbl.setWordWrap(True)
        addr_lbl = QLabel(CENTRE_ADDRESS)
        addr_lbl.setStyleSheet(
            "font-size: 11px; color: #888888;"
            "background: transparent; border: none;"
        )
        sub_lbl = QLabel("Management Dashboard")
        sub_lbl.setStyleSheet(
            "font-size: 11px; color: #666666;"
            "background: transparent; border: none;"
        )
        title_col.addWidget(centre_lbl)
        title_col.addWidget(addr_lbl)
        title_col.addWidget(sub_lbl)
        brand_cl.addLayout(title_col)
        brand_cl.addStretch()

        right_col = QVBoxLayout()
        right_col.setSpacing(6)
        right_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._date_lbl = QLabel(f"Today (BS): {today_bs()}")
        self._date_lbl.setStyleSheet(
            "font-size: 12px; color: #aaaaaa; background: transparent; border: none;"
        )
        self._date_lbl.setAlignment(Qt.AlignRight)

        refresh_btn = QPushButton("↻  Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #333333; color: #ffffff;
                border: 1px solid #555555; border-radius: 5px;
                padding: 6px 14px; font-size: 12px; font-weight: bold;
                min-height: 28px;
            }
            QPushButton:hover   { background: #555555; }
            QPushButton:pressed { background: #222222; }
        """)
        refresh_btn.clicked.connect(self.refresh)
        right_col.addWidget(self._date_lbl)
        right_col.addWidget(refresh_btn)
        brand_cl.addLayout(right_col)
        self._layout.addWidget(brand_card)

        # ── Overview section ──────────────────────────────────────────────────
        ovr_lbl = QLabel("OVERVIEW")
        ovr_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(ovr_lbl)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        overview_defs = [
            ("students",     "Total Students",  "registered",    "#333333", "#f5f5f5"),
            ("teachers",     "Total Teachers",  "registered",    "#333333", "#f5f5f5"),
            ("present",      "Present Today",   "students",      "#333333", "#f5f5f5"),
            ("active_subs",  "Active",          "subscriptions", STATUS_PRESENT,    STATUS_PRESENT_BG),
            ("expired_subs", "Expired",         "subscriptions", STATUS_ABSENT,     STATUS_ABSENT_BG),
            ("pending_subs", "Payment Pending", "students",      STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG),
        ]
        for key, label, sub, fg, bg in overview_defs:
            card, v, s = self._make_stat_card(label, "—", sub, fg, bg)
            self._stat_cards[key] = (v, s)
            stats_row.addWidget(card)
        self._layout.addLayout(stats_row)

        # ── Financials ────────────────────────────────────────────────────────
        fin_lbl = QLabel("FINANCIALS")
        fin_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        self._layout.addWidget(fin_lbl)

        fin_row = QHBoxLayout()
        fin_row.setSpacing(12)
        fin_defs = [
            ("revenue",     "Total Revenue",   "collected",           STATUS_PRESENT,    STATUS_PRESENT_BG),
            ("expenses",    "Total Expenses",  "recorded",            STATUS_ABSENT,     STATUS_ABSENT_BG),
            ("net",         "Net Balance",     "revenue - expenses",  "#1a3a6b",          "#e8f0fb"),
            ("pending_amt", "Pending Amount",  "outstanding",         STATUS_INCOMPLETE, STATUS_INCOMPLETE_BG),
        ]
        for key, label, sub, fg, bg in fin_defs:
            card, v, s = self._make_stat_card(label, "—", sub, fg, bg)
            self._stat_cards[key] = (v, s)
            fin_row.addWidget(card)
        self._layout.addLayout(fin_row)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background: #e0e0e0; border: none;")
        self._layout.addWidget(div)

        # ── Classes & groups ──────────────────────────────────────────────────
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

    # ── Logo helpers ──────────────────────────────────────────────────────────

    def _refresh_logo_widget(self, lbl: QLabel,
                              w: int, h: int,
                              fallback_text: str = "G",
                              dark_bg: bool = True):
        """
        Set logo PNG onto a QLabel, or show a styled fallback letter.
        """
        pix = logo_pixmap(w, h)
        if pix:
            lbl.setPixmap(pix)
            lbl.setStyleSheet(
                "background: transparent; border: none;"
            )
        else:
            # Fallback: styled circle with letter
            bg  = "#ffffff" if dark_bg else "#1a1a1a"
            fg  = "#1a1a1a" if dark_bg else "#ffffff"
            rad = min(w, h) // 2
            lbl.setText(fallback_text)
            lbl.setStyleSheet(f"""
                QLabel {{
                    background: {bg};
                    border-radius: {rad}px;
                    color: {fg};
                    font-size: {int(w * 0.45)}px;
                    font-weight: bold;
                    border: none;
                }}
            """)

    # ── Data refresh ─────────────────────────────────────────────────────────

    def refresh(self):
        self._date_lbl.setText(f"Today (BS): {today_bs()}")

        session = get_session()
        total_students = session.query(Student).count()
        total_teachers = session.query(Teacher).count()
        today_present  = session.query(Attendance).filter_by(
            date=date.today(), status="Present"
        ).count()
        classes_data = []
        for cls in session.query(Class).all():
            classes_data.append({
                "name": cls.name,
                "groups": [
                    {"name": g.name, "student_count": len(g.students)}
                    for g in cls.groups
                ],
            })
        session.close()

        sub_stats = get_subscription_dashboard_stats()
        revenue   = get_total_revenue()
        exp_stat  = get_expense_dashboard_stats()
        net       = revenue - exp_stat["total_all_time"]

        updates = {
            "students":    (str(total_students),                     "registered"),
            "teachers":    (str(total_teachers),                     "registered"),
            "present":     (str(today_present),                      "today"),
            "active_subs": (str(sub_stats["active"]),                "subscriptions"),
            "expired_subs":(str(sub_stats["expired"]),               "subscriptions"),
            "pending_subs":(str(sub_stats["pending"]),               "students"),
            "revenue":     (f"Rs.{revenue:,.0f}",                    "collected"),
            "expenses":    (f"Rs.{exp_stat['total_all_time']:,.0f}", "recorded"),
            "net":         (f"Rs.{net:,.0f}",                        "revenue - expenses"),
            "pending_amt": (f"Rs.{sub_stats['total_pending']:,.0f}", "outstanding"),
        }
        for key, (val, sub) in updates.items():
            v, s = self._stat_cards[key]
            v.setText(val)
            s.setText(sub)
            if key == "net":
                color = STATUS_PRESENT if net >= 0 else STATUS_ABSENT
                v.setStyleSheet(
                    f"font-size: 22px; font-weight: bold; color: {color};"
                    "background: transparent; border: none;"
                )

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

    # ── Card builders ─────────────────────────────────────────────────────────

    def _make_stat_card(self, label, value, sub,
                        fg="#333333", bg="#f5f5f5"):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }}
        """)
        card.setMinimumHeight(96)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(3)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {fg};"
            "background: transparent; border: none;"
        )
        title_lbl = QLabel(label)
        title_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {fg};"
            "background: transparent; border: none;"
        )
        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet(
            f"font-size: 11px; color: {fg};"
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