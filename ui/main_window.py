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
from ui.pages.settings_page        import SettingsPage
from ui.pages.student_profile_page import StudentProfilePage
from ui.pages.teacher_profile_page import TeacherProfilePage
from ui.event_bus import bus


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tuition Centre Management System")
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
        self.settings_page      = SettingsPage()
        self.student_profile    = StudentProfilePage()
        self.teacher_profile    = TeacherProfilePage()

        self.pages = [
            self.dashboard_page,     # 0
            self.students_page,      # 1
            self.teachers_page,      # 2
            self.classes_page,       # 3
            self.attendance_page,    # 4
            self.subscriptions_page, # 5
            self.reports_page,       # 6
            self.schedule_page,      # 7
            self.exams_page,         # 8
            self.settings_page,      # 9
            self.student_profile,    # 10 — no nav button
            self.teacher_profile,    # 11 — no nav button
        ]
        for page in self.pages:
            self.stack.addWidget(page)

        root.addWidget(self.stack)
        self._switch_page(0)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(215)
        sidebar.setStyleSheet("background: #1e1e1e;")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo_w = QWidget()
        logo_w.setStyleSheet("background: #141414;")
        ll = QVBoxLayout(logo_w)
        ll.setContentsMargins(18, 20, 18, 20)
        ll.setSpacing(4)
        t = QLabel("TuitionCMS")
        t.setStyleSheet(
            "color: #ffffff; font-size: 16px; font-weight: bold;"
            "background: transparent;"
        )
        s = QLabel("Management System")
        s.setStyleSheet(
            "color: #666666; font-size: 10px; background: transparent;"
        )
        ll.addWidget(t)
        ll.addWidget(s)
        layout.addWidget(logo_w)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #333333;")
        layout.addWidget(div)
        layout.addSpacing(8)

        nav_items = [
            ("Dashboard",        "⊞", 0),
            ("Students",         "◉", 1),
            ("Teachers",         "◈", 2),
            ("Classes & Groups", "▦", 3),
            ("Attendance",       "☰", 4),
            ("Subscriptions",    "◎", 5),
            ("Reports",          "▤", 6),
            ("Schedule",         "◫", 7),
            ("Exams",            "✎", 8),
            ("Settings",         "⚙", 9),
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
        ver = QLabel("v2.1.0  •  Offline")
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
        bus.student_saved.connect(self.dashboard_page.refresh)
        bus.student_saved.connect(
            self.subscriptions_page._load_students
        )
        bus.open_student_profile.connect(self._open_student_profile)
        bus.open_teacher_profile.connect(self._open_teacher_profile)

    def _open_student_profile(self, student_id):
        if student_id < 0:
            self._switch_page(1)
            return
        self.student_profile.load_student(student_id)
        self._switch_page(10, highlight_nav=False)

    def _open_teacher_profile(self, teacher_id):
        if teacher_id < 0:
            self._switch_page(2)
            return
        self.teacher_profile.load_teacher(teacher_id)
        self._switch_page(11, highlight_nav=False)