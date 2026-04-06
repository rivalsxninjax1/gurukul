from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QFileDialog, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt
from services.settings_service import get_all_settings, set_setting
from services.backup_service import backup_database, restore_database
from ui.styles import (
    BTN_PRIMARY, BTN_SECONDARY, BTN_DANGER,
    INPUT_STYLE, PAGE_TITLE_STYLE, PANEL_TITLE_STYLE,
    SECTION_LABEL_STYLE, CARD_STYLE, FORM_LABEL_STYLE
)


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #f5f5f5;")
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #f5f5f5; border: none; }")

        content = QWidget(); content.setStyleSheet("background: #f5f5f5;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Settings")
        title.setStyleSheet(PAGE_TITLE_STYLE)
        layout.addWidget(title)

        # ── Centre Info card
        layout.addWidget(self._section_card("CENTRE INFORMATION", [
            ("Centre Name",    "centre_name",    "e.g. ABC Tuition Centre"),
            ("Phone Number",   "centre_phone",   "e.g. +977-XXXXXXXXXX"),
            ("Address",        "centre_address", "e.g. Biratnagar, Nepal"),
        ]))

        # ── Attendance card
        layout.addWidget(self._section_card("ATTENDANCE", [
            ("Attendance Threshold (%)",
             "attendance_threshold", "Default: 75"),
        ]))

        # ── Fees card
        layout.addWidget(self._section_card("FEES", [
            ("Default Monthly Fee (Rs.)",
             "default_fee", "Default: 2000"),
        ]))

        # Save button
        save_btn = QPushButton("Save All Settings")
        save_btn.setStyleSheet(BTN_PRIMARY)
        save_btn.setFixedHeight(40)
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        # ── Backup card
        backup_card = QFrame(); backup_card.setStyleSheet(CARD_STYLE)
        bl = QVBoxLayout(backup_card); bl.setContentsMargins(20, 18, 20, 18); bl.setSpacing(12)

        bk_title = QLabel("BACKUP & RESTORE")
        bk_title.setStyleSheet(SECTION_LABEL_STYLE)
        bl.addWidget(bk_title)

        bk_desc = QLabel(
            "Back up your database to keep your data safe. "
            "Restore a previous backup if needed."
        )
        bk_desc.setStyleSheet("font-size: 12px; color: #666666; background: transparent;")
        bk_desc.setWordWrap(True)
        bl.addWidget(bk_desc)

        btn_row = QHBoxLayout()
        backup_btn = QPushButton("Backup Database")
        backup_btn.setStyleSheet(BTN_SECONDARY)
        backup_btn.clicked.connect(self._backup)

        restore_btn = QPushButton("Restore from Backup")
        restore_btn.setStyleSheet(BTN_DANGER)
        restore_btn.clicked.connect(self._restore)

        btn_row.addWidget(backup_btn)
        btn_row.addWidget(restore_btn)
        btn_row.addStretch()
        bl.addLayout(btn_row)
        layout.addWidget(backup_card)

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _section_card(self, section_title, fields):
        """fields = list of (label, settings_key, placeholder)"""
        card = QFrame(); card.setStyleSheet(CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18); layout.setSpacing(14)

        sec_lbl = QLabel(section_title); sec_lbl.setStyleSheet(SECTION_LABEL_STYLE)
        layout.addWidget(sec_lbl)

        self._field_refs = getattr(self, "_field_refs", {})

        for label_text, key, placeholder in fields:
            lbl = QLabel(label_text); lbl.setStyleSheet(FORM_LABEL_STYLE)
            inp = QLineEdit(); inp.setPlaceholderText(placeholder)
            inp.setStyleSheet(INPUT_STYLE); inp.setFixedHeight(36)
            self._field_refs[key] = inp
            layout.addWidget(lbl)
            layout.addWidget(inp)

        return card

    def _load_settings(self):
        self._field_refs = getattr(self, "_field_refs", {})
        settings = get_all_settings()
        for key, inp in self._field_refs.items():
            inp.setText(settings.get(key, ""))

    def _save_settings(self):
        for key, inp in self._field_refs.items():
            set_setting(key, inp.text().strip())
        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    def _backup(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Backup Folder")
        if folder:
            dest = backup_database(folder)
            QMessageBox.information(self, "Backup Complete",
                                    f"Database backed up to:\n{dest}")

    def _restore(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", "", "Database (*.db)"
        )
        if path:
            reply = QMessageBox.question(
                self, "Confirm Restore",
                "This will REPLACE your current database.\n"
                "All unsaved changes will be lost.\n\nProceed?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if restore_database(path):
                    QMessageBox.information(self, "Restored",
                                            "Database restored. Please restart the app.")
                else:
                    QMessageBox.critical(self, "Failed", "Restore failed. Check logs.")