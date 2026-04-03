import sys
from PyQt5.QtWidgets import QApplication
from utils.logger import setup_logger
from database.init_db import initialize_database
from services.auth_service import create_default_admin
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

def main():
    setup_logger()
    initialize_database()
    create_default_admin()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    main_win = MainWindow()

    def on_login_success():
        main_win.show()

    login = LoginWindow(on_success=on_login_success)
    login.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()