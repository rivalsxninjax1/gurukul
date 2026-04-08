from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt

from ui.pages.dashboard_page       import DashboardPage
from ui.pages.students_page        import StudentsPage
from ui.pages.teachers_page        import TeachersPage
from ui.pages.classes_page         import ClassesPage
from ui.pages.attendance_page      import AttendancePage
from ui.pages.subscriptions_page   import SubscriptionsPage
from ui.pages.reports_page         import ReportsPage
from ui.pages.schedule_page        import SchedulePage
from ui.pages.exams_page           import ExamsPage
from ui.pages.expenses_page        import ExpensesPage
from ui.pages.settings_page        import SettingsPage
from ui.pages.student_profile_page import StudentProfilePage
from ui.pages.teacher_profile_page import TeacherProfilePage
from ui.event_bus import bus

CENTRE_NAME = "Gurukul Tuition Centre"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(CENTRE_NAME)
        self.setMinimumSize(1200, 740)
        self._build_ui()
        self._connect_bus()

    def _build_ui(self):
        central = QWidget()
        central.setStyleSheet("background: #f5f5f5;")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: #f5f5f5;")

        self.dashboard_page     = DashboardPage()
        self.students_page      = StudentsPage()
        self.teachers_page      = TeachersPage()
        self.classes_page       = ClassesPage()
        self.attendance_page    = AttendancePage()
        self.subscriptions_page = SubscriptionsPage()
        self.reports_page       = ReportsPage()
        self.schedule_page      = SchedulePage()
        self.exams_page         = ExamsPage()
        self.expenses_page      = ExpensesPage()
        self.settings_page      = SettingsPage()
        self.student_profile    = StudentProfilePage()
        self.teacher_profile    = TeacherProfilePage()

        self.pages = [
            self.dashboard_page,      # 0
            self.students_page,       # 1
            self.teachers_page,       # 2
            self.classes_page,        # 3
            self.attendance_page,     # 4
            self.subscriptions_page,  # 5
            self.reports_page,        # 6
            self.schedule_page,       # 7
            self.exams_page,          # 8
            self.expenses_page,       # 9
            self.settings_page,       # 10
            self.student_profile,     # 11 — no nav
            self.teacher_profile,     # 12 — no nav
        ]
        for page in self.pages:
            self.stack.addWidget(page)

        root.addWidget(self.stack)
        self._switch_page(0)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(222)
        sidebar.setStyleSheet("background: #1e1e1e;")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Branding header
        logo_w = QWidget()
        logo_w.setStyleSheet("background: #141414;")
        ll = QVBoxLayout(logo_w)
        ll.setContentsMargins(14, 14, 14, 14)
        ll.setSpacing(6)

        # Logo row
        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)

        # PNG logo or fallback
        from utils.logo_helper import logo_pixmap
        logo_lbl = QLabel()
        logo_lbl.setFixedSize(40, 40)
        logo_lbl.setAlignment(Qt.AlignCenter)
        pix = logo_pixmap(40, 40)
        if pix:
            logo_lbl.setPixmap(pix)
            logo_lbl.setStyleSheet("background: transparent; border: none;")
        else:
            logo_lbl.setText("G")
            logo_lbl.setStyleSheet("""
                QLabel {
                    background: #ffffff; border-radius: 20px;
                    color: #1a1a1a; font-size: 20px;
                    font-weight: bold; border: none;
                }
            """)
        logo_row.addWidget(logo_lbl)

        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        t1 = QLabel("Gurukul Academy")
        t1.setStyleSheet(
            "color: #ffffff; font-size: 12px; font-weight: bold;"
            "background: transparent;"
        )
        t2 = QLabel("and Training Center")
        t2.setStyleSheet(
            "color: #aaaaaa; font-size: 10px; background: transparent;"
        )
        name_col.addWidget(t1)
        name_col.addWidget(t2)
        logo_row.addLayout(name_col)
        logo_row.addStretch()
        ll.addLayout(logo_row)

        addr = QLabel("Biratnagar-1, Bhatta Chowk")
        addr.setStyleSheet(
            "color: #555555; font-size: 9px; background: transparent;"
        )
        ll.addWidget(addr)
        layout.addWidget(logo_w)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #333333;")
        layout.addWidget(div)
        layout.addSpacing(8)

        nav_items = [
            ("Dashboard",        "⊞",  0),
            ("Students",         "◉",  1),
            ("Teachers",         "◈",  2),
            ("Classes & Groups", "▦",  3),
            ("Attendance",       "☰",  4),
            ("Subscriptions",    "◎",  5),
            ("Reports",          "▤",  6),
            ("Schedule",         "◫",  7),
            ("Exams",            "✎",  8),
            ("Expenses",         "₹",  9),
            ("Settings",         "⚙", 10),
        ]

        self.nav_buttons = []
        for label, icon, idx in nav_items:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setFixedHeight(44)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #999999;
                    text-align: left; padding-left: 14px;
                    font-size: 13px; border: none; border-radius: 0;
                }
                QPushButton:hover  { background: #2a2a2a; color: #ffffff; }
                QPushButton:checked {
                    background: #2e2e2e; color: #ffffff;
                    border-left: 3px solid #ffffff; padding-left: 11px;
                }
            """)
            btn.clicked.connect(lambda _, i=idx: self._switch_page(i))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)

        layout.addStretch()
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet("background: #333333;")
        layout.addWidget(div2)
        ver = QLabel("v2.3.0  •  Offline")
        ver.setStyleSheet(
            "color: #444444; font-size: 10px; padding: 10px 18px;"
            "background: transparent;"
        )
        layout.addWidget(ver)
        return sidebar
    
    
    def _switch_page(self, index, highlight_nav=True):
        self.stack.setCurrentIndex(index)
        if highlight_nav and index < len(self.nav_buttons):
            for i, btn in enumerate(self.nav_buttons):
                btn.setChecked(i == index)

    def _connect_bus(self):
        bus.attendance_imported.connect(self.dashboard_page.refresh)
        bus.payment_added.connect(self.dashboard_page.refresh)
        bus.payment_added.connect(self.expenses_page.refresh)
        bus.student_saved.connect(self.dashboard_page.refresh)
        bus.student_saved.connect(self.subscriptions_page._load_students)
        bus.open_student_profile.connect(self._open_student_profile)
        bus.open_teacher_profile.connect(self._open_teacher_profile)

    def _open_student_profile(self, student_id):
        if student_id < 0:
            self._switch_page(1)
            return
        self.student_profile.load_student(student_id)
        self._switch_page(11, highlight_nav=False)

    def _open_teacher_profile(self, teacher_id):
        if teacher_id < 0:
            self._switch_page(2)
            return
        self.teacher_profile.load_teacher(teacher_id)
        self._switch_page(12, highlight_nav=False)