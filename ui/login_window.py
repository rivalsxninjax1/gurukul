from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from services.auth_service import verify_login
from services.session_service import set_current_user, clear_current_user
from ui.styles import BTN_PRIMARY, INPUT_STYLE

CENTRE_NAME = "Gurukul Tuition Centre"


class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setWindowTitle(f"{CENTRE_NAME} — Login")
        self.setMinimumSize(480, 540)
        self.setStyleSheet("background: #f0f0f0;")
        self._build_ui()
        clear_current_user()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addStretch(1)

        center = QHBoxLayout()
        center.addStretch(1)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setFixedWidth(400)
        card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        card.setStyleSheet("""
            QFrame#loginCard {
                background: #ffffff;
                border: 1px solid #d8d8d8;
                border-radius: 14px;
            }
        """)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 36, 40, 36)
        cl.setSpacing(0)

        # ── Logo ──────────────────────────────────────────────────────────────
        logo_frame = QFrame()
        logo_frame.setFixedSize(76, 76)
        logo_frame.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                border-radius: 38px;
                border: none;
            }
        """)
        logo_inner = QVBoxLayout(logo_frame)
        logo_inner.setContentsMargins(0, 0, 0, 0)
        logo_icon = QLabel("G")
        logo_icon.setStyleSheet(
            "font-size: 34px; font-weight: bold; color: #ffffff;"
            "background: transparent; border: none;"
        )
        logo_icon.setAlignment(Qt.AlignCenter)
        logo_inner.addWidget(logo_icon)

        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(logo_frame)
        logo_row.addStretch()
        cl.addLayout(logo_row)
        cl.addSpacing(16)

        # Title
        title = QLabel(CENTRE_NAME)
        title.setFont(QFont("Arial", 17, QFont.Bold))
        title.setStyleSheet(
            "color: #1a1a1a; background: transparent; border: none;"
        )
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        cl.addWidget(title)

        sub = QLabel("Management System")
        sub.setStyleSheet(
            "font-size: 12px; color: #888888; background: transparent; border: none;"
        )
        sub.setAlignment(Qt.AlignCenter)
        cl.addWidget(sub)
        cl.addSpacing(22)

        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background: #eeeeee; border: none; margin: 0;")
        cl.addWidget(div)
        cl.addSpacing(20)

        # Error label
        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("""
            QLabel {
                font-size: 12px; color: #8b0000;
                background: #fdeaea;
                border: 1px solid #f5b8b8;
                border-radius: 5px;
                padding: 7px 10px;
            }
        """)
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setAlignment(Qt.AlignCenter)
        self.error_lbl.hide()
        cl.addWidget(self.error_lbl)
        cl.addSpacing(4)

        # Username
        uid_lbl = QLabel("Username")
        uid_lbl.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #444444;"
            "background: transparent; border: none;"
        )
        cl.addWidget(uid_lbl)
        cl.addSpacing(5)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setStyleSheet(INPUT_STYLE)
        self.username_input.setFixedHeight(42)
        cl.addWidget(self.username_input)
        cl.addSpacing(14)

        # Password
        pw_lbl = QLabel("Password")
        pw_lbl.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #444444;"
            "background: transparent; border: none;"
        )
        cl.addWidget(pw_lbl)
        cl.addSpacing(5)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(INPUT_STYLE)
        self.password_input.setFixedHeight(42)
        self.password_input.returnPressed.connect(self._handle_login)
        cl.addWidget(self.password_input)
        cl.addSpacing(22)

        # Login button
        login_btn = QPushButton("Log In")
        login_btn.setFixedHeight(44)
        login_btn.setStyleSheet(BTN_PRIMARY)
        login_btn.clicked.connect(self._handle_login)
        cl.addWidget(login_btn)
        cl.addSpacing(12)

        hint = QLabel("Default: admin / admin123")
        hint.setStyleSheet(
            "font-size: 11px; color: #bbbbbb; background: transparent; border: none;"
        )
        hint.setAlignment(Qt.AlignCenter)
        cl.addWidget(hint)

        center.addWidget(card)
        center.addStretch(1)
        outer.addLayout(center)
        outer.addStretch(1)

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        self.error_lbl.hide()

        if not username:
            self._show_error("Please enter your username.")
            self.username_input.setFocus()
            return
        if not password:
            self._show_error("Please enter your password.")
            self.password_input.setFocus()
            return

        if verify_login(username, password):
            set_current_user(username)
            self.on_success()
            self.close()
        else:
            self._show_error("Invalid username or password.")
            self.password_input.clear()
            self.password_input.setFocus()

    def _show_error(self, msg: str):
        self.error_lbl.setText(msg)
        self.error_lbl.show()
