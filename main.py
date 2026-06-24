import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QObject, QEvent
from utils.logger import setup_logger
from database.init_db import initialize_database
from services.auth_service import create_default_admin
from services.subscription_service import auto_renew_expired_students
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


class _MsgBoxFilter(QObject):
    """
    Event filter that auto-styles every QMessageBox the moment it is
    shown — covers static calls (QMessageBox.question / .warning /
    .information / .critical) which bypass apply_msgbox_style().
    Only touches QMessageBox instances, nothing else in the app.
    """
    def eventFilter(self, obj, event):
        if isinstance(obj, QMessageBox) and event.type() == QEvent.Polish:
            from PyQt5.QtGui import QPalette, QColor
            from PyQt5.QtWidgets import QLabel, QPushButton

            # White dialog background, dark text
            p = obj.palette()
            p.setColor(QPalette.Window,     QColor("#ffffff"))
            p.setColor(QPalette.WindowText, QColor("#1a1a1a"))
            p.setColor(QPalette.Text,       QColor("#1a1a1a"))
            obj.setPalette(p)

            # Force dark text on every label
            for lbl in obj.findChildren(QLabel):
                lp = lbl.palette()
                lp.setColor(QPalette.WindowText, QColor("#1a1a1a"))
                lp.setColor(QPalette.Text,       QColor("#1a1a1a"))
                lbl.setPalette(lp)
                lbl.setStyleSheet(
                    "color: #1a1a1a; background: transparent; font-size: 13px;"
                )

            # Style buttons: dark bg, white text, rounded
            for btn in obj.findChildren(QPushButton):
                btn.setStyleSheet("""
                    QPushButton {
                        background: #1a1a1a; color: #ffffff;
                        border: none; border-radius: 5px;
                        padding: 6px 20px; font-size: 13px;
                        min-width: 80px; min-height: 28px;
                    }
                    QPushButton:hover   { background: #3a3a3a; }
                    QPushButton:pressed { background: #000000; }
                """)

        return super().eventFilter(obj, event)


def main():
    setup_logger()
    initialize_database()
    create_default_admin()
    auto_renew_expired_students()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Install the event filter — styles every QMessageBox on show,
    # without touching any other widget in the app.
    _filter = _MsgBoxFilter()
    app.installEventFilter(_filter)

    main_win = MainWindow()

    def on_login_success():
        main_win.show()

    login = LoginWindow(on_success=on_login_success)
    login.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()