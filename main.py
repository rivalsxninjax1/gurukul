import sys
from PyQt5.QtWidgets import QApplication
from utils.logger import setup_logger
from database.init_db import initialize_database
from services.auth_service import create_default_admin
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.styles import MSGBOX_STYLE

def main():
    setup_logger()
    initialize_database()
    create_default_admin()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Apply QMessageBox style globally so every dialog — including those
    # created via the static QMessageBox.question/warning/information/critical
    # convenience methods — shows dark text on a white background.
    app.setStyleSheet(MSGBOX_STYLE)

    main_win = MainWindow()

    def on_login_success():
        main_win.show()

    login = LoginWindow(on_success=on_login_success)
    login.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()