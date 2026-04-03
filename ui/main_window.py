from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.pages.dashboard_page  import DashboardPage
from ui.pages.students_page   import StudentsPage
from ui.pages.teachers_page   import TeachersPage
from ui.pages.classes_page    import ClassesPage
from ui.pages.attendance_page import AttendancePage
from ui.pages.billing_page    import BillingPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tuition Centre Management System")
        self.setMinimumSize(1150, 720)
        self._build_ui()

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

        self.pages = [
            DashboardPage(),
            StudentsPage(),
            TeachersPage(),
            ClassesPage(),
            AttendancePage(),
            BillingPage(),
        ]
        for page in self.pages:
            self.stack.addWidget(page)

        root.addWidget(self.stack)
        self._switch_page(0)

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(210)
        sidebar.setStyleSheet("background: #1e1e1e;")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo area
        logo_frame = QWidget()
        logo_frame.setStyleSheet("background: #141414;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(18, 20, 18, 20)
        logo_layout.setSpacing(3)

        logo_title = QLabel("TuitionCMS")
        logo_title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold; background: transparent;")

        logo_sub = QLabel("Management System")
        logo_sub.setStyleSheet("color: #777777; font-size: 10px; background: transparent;")

        logo_layout.addWidget(logo_title)
        logo_layout.addWidget(logo_sub)
        layout.addWidget(logo_frame)

        # Thin divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #333333;")
        layout.addWidget(div)

        layout.addSpacing(8)

        nav_section = QLabel("MENU")
        nav_section.setStyleSheet(
            "color: #555555; font-size: 10px; font-weight: bold;"
            "padding: 0px 18px; background: transparent; letter-spacing: 1px;"
        )
        layout.addWidget(nav_section)
        layout.addSpacing(6)

        nav_items = [
            ("Dashboard",        "⊞", 0),
            ("Students",         "◉", 1),
            ("Teachers",         "◈", 2),
            ("Classes & Groups", "▦", 3),
            ("Attendance",       "☰", 4),
            ("Billing",          "◎", 5),
        ]

        self.nav_buttons = []
        for label, icon, idx in nav_items:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setFixedHeight(46)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #999999;
                    text-align: left;
                    padding-left: 14px;
                    font-size: 13px;
                    border: none;
                    border-radius: 0px;
                }
                QPushButton:hover {
                    background: #2a2a2a;
                    color: #ffffff;
                }
                QPushButton:checked {
                    background: #2e2e2e;
                    color: #ffffff;
                    border-left: 3px solid #ffffff;
                    padding-left: 11px;
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

        ver = QLabel("v1.0.0  •  Offline")
        ver.setStyleSheet("color: #444444; font-size: 10px; padding: 10px 18px; background: transparent;")
        layout.addWidget(ver)

        return sidebar

    def _switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)