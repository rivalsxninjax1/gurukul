from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from services.auth_service import verify_login
from ui.styles import BTN_PRIMARY, INPUT_STYLE


class LoginWindow(QWidget):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.setWindowTitle("Tuition CMS — Login")
        self.setFixedSize(420, 380)
        self.setStyleSheet("background: #eeeeee;")
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(50, 50, 50, 50)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setStyleSheet("""
            QFrame#loginCard {
                background: #ffffff;
                border: 1px solid #d8d8d8;
                border-radius: 10px;
            }
        """)
        card.setObjectName("loginCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(0)

        title = QLabel("Tuition Centre")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #1a1a1a; background: transparent; border: none;")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Management System")
        subtitle.setStyleSheet("font-size: 12px; color: #888888; background: transparent; border: none;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(24)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #eeeeee; border: none;")
        layout.addWidget(divider)
        layout.addSpacing(20)

        uid_lbl = QLabel("Username")
        uid_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #444444; background: transparent; border: none;")
        layout.addWidget(uid_lbl)
        layout.addSpacing(5)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setStyleSheet(INPUT_STYLE)
        self.username_input.setFixedHeight(38)
        layout.addWidget(self.username_input)
        layout.addSpacing(14)

        pw_lbl = QLabel("Password")
        pw_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #444444; background: transparent; border: none;")
        layout.addWidget(pw_lbl)
        layout.addSpacing(5)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(INPUT_STYLE)
        self.password_input.setFixedHeight(38)
        self.password_input.returnPressed.connect(self._handle_login)
        layout.addWidget(self.password_input)
        layout.addSpacing(22)

        login_btn = QPushButton("Log In")
        login_btn.setFixedHeight(40)
        login_btn.setStyleSheet(BTN_PRIMARY)
        login_btn.clicked.connect(self._handle_login)
        layout.addWidget(login_btn)
        layout.addSpacing(12)

        hint = QLabel("Default: admin / admin123")
        hint.setStyleSheet("font-size: 11px; color: #aaaaaa; background: transparent; border: none;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        outer.addWidget(card)

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Missing Fields", "Please enter both username and password.")
            return
        if verify_login(username, password):
            self.on_success()
            self.close()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password.")
            self.password_input.clear()
            self.password_input.setFocus()