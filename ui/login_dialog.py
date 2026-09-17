from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from ui.theme import COLORS, apply_card_shadow
import qtawesome as qta


class LoginDialog(QDialog):

    def __init__(self, api_service, parent=None, is_lock_screen=False):
        super().__init__(parent)
        self.api_service = api_service
        self.is_lock_screen = is_lock_screen
        self.user_data = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('تسجيل الدخول')
        self.setFixedSize(420, 520)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        if self.is_lock_screen:
            self.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )

        # Modern gradient background
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F0FDF4, stop:0.5 #ECFDF5, stop:1 #DBEAFE);
            }
        """)

        # Card container
        container = QFrame()
        apply_card_shadow(container, "#00000030", 50, 18)
        container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 28px;
                border: none;
            }
        """)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.addWidget(container)

        lay = QVBoxLayout(container)
        lay.setSpacing(16)
        lay.setContentsMargins(36, 36, 36, 36)

        # Title
        title = QLabel('نظام الإمداد والتموين')
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #10B981; padding: 12px 0;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        # Subtitle
        subtitle = QLabel('Military Supply Management')
        subtitle.setStyleSheet("color: #6B7280; font-size: 11px; font-weight: 500; letter-spacing: 1px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(subtitle)

        lay.addSpacing(20)

        # Username
        user_lbl = QLabel('اسم المستخدم')
        user_lbl.setStyleSheet("color: #111827; font-weight: 600; font-size: 13px;")
        lay.addWidget(user_lbl)

        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText('أدخل اسم المستخدم')
        self.txt_user.setMinimumHeight(48)
        self.txt_user.setStyleSheet("""
            QLineEdit {
                background-color: #F9FAFB;
                border: 2px solid #E5E7EB;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 15px;
                font-family: 'Cairo', sans-serif;
                color: #111827;
            }
            QLineEdit:focus {
                border: 2px solid #10B981;
                background-color: #FFFFFF;
            }
            QLineEdit::placeholder {
                color: #9CA3AF;
            }
        """)
        lay.addWidget(self.txt_user)

        # Password
        lay.addWidget(QLabel('كلمة المرور'))
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText('أدخل كلمة المرور')
        self.txt_pass.setMinimumHeight(48)
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setStyleSheet("""
            QLineEdit {
                background-color: #F9FAFB;
                border: 2px solid #E5E7EB;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 15px;
                font-family: 'Cairo', sans-serif;
                color: #111827;
            }
            QLineEdit:focus {
                border: 2px solid #10B981;
                background-color: #FFFFFF;
            }
        """)
        lay.addWidget(self.txt_pass)

        # Password toggle
        self.btn_toggle = QPushButton()
        self.btn_toggle.setIcon(qta.icon('fa5s.eye', color='#6B7280'))
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setStyleSheet('background: transparent; border: none; padding: 0;')
        self.btn_toggle.clicked.connect(self._toggle_password)
        pwd_lay = QHBoxLayout()
        pwd_lay.addWidget(self.txt_pass)
        pwd_lay.addWidget(self.btn_toggle)
        lay.addLayout(pwd_lay)

        lay.addSpacing(20)

        # Login button
        device_status = getattr(self.api_service, 'device_status', 'APPROVED')
        self.btn_login = QPushButton('دخول')
        self.btn_login.clicked.connect(self._do_login)
        self.btn_login.setEnabled(device_status not in ('PENDING', 'BLOCKED'))
        lay.addWidget(self.btn_login)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #06B6D4);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 28px;
                font-size: 15px;
                font-weight: 600;
                min-height: 44px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0891B2);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #0E7490);
            }
            QPushButton:disabled {
                background: #E5E7EB;
                color: #9CA3AF;
            }
        """)

        # Exit button
        self.btn_exit = QPushButton('إلغاء')
        self.btn_exit.clicked.connect(self.reject)
        lay.addWidget(self.btn_exit)
        self.btn_exit.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6B7280;
                border: 2px solid #E5E7EB;
                border-radius: 12px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 600;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
                border-color: #BDC3C7;
                color: #111827;
            }
        """)

        from ui.loading_overlay import LoadingOverlay
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()

    def _toggle_password(self):
        if self.txt_pass.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_pass.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle.setIcon(qta.icon('fa5s.eye-slash', color='gray'))
        else:
            self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle.setIcon(qta.icon('fa5s.eye', color='gray'))

    def _do_login(self):
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, 'خطأ', 'يرجى تعبئة كافة الحقول')
            return

        self.btn_login.setEnabled(False)
        try:
            self.loading_overlay.show_with_message('جاري التحقق...')
        except Exception:
            pass

        import PyQt6.QtWidgets as QtWidgets
        QtWidgets.QApplication.processEvents()

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._process_login(user, pwd))

    def _process_login(self, user, pwd):
        try:
            ok, res = self.api_service.login(user, pwd)
        except Exception as e:
            self.btn_login.setEnabled(True)
            try:
                self.loading_overlay.hide()
            except Exception:
                pass
            QMessageBox.critical(self, 'خطأ', f'فشل الاتصال: {e}')
            return

        if ok and isinstance(res, dict) and res.get('id'):
            self.user_data = res
            try:
                self.loading_overlay.hide()
            except Exception:
                pass
            self.accept()
        else:
            try:
                self.loading_overlay.hide()
            except Exception:
                pass
            self.btn_login.setEnabled(True)
            err = res.get('detail', 'فشل تسجيل الدخول') if isinstance(res, dict) else 'خطأ في الاتصال'
            QMessageBox.critical(self, 'خطأ', str(err))
