# NOTE: هذا الملف أُعيد بناؤه يدوياً من ملف login_dialog.pyc
# الملف الأصلي مُصرَّف بصيغة Python 3.14 (RC) التي لا تدعمها أدوات فك التشفير
# الحالية. تم استخراج كل الأسماء والنصوص والقيم الثابتة بدقة كاملة عبر قارئ
# marshal مخصص، وأُعيد بناء المنطق بالاعتماد عليها وعلى نمط الملفات السابقة
# من نفس المشروع. النقطة الأقل يقيناً (معلَّمة "تقريبي"): تفصيل بسيط في بناء
# ستايل زر "خروج" في _init_ui.

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

from theme import COLORS, make_header_label
import qtawesome as qta


class LoginDialog(QDialog):

    def __init__(self, api_service, parent=None, is_lock_screen=False):
        super().__init__(parent)
        self.api_service = api_service
        self.is_lock_screen = is_lock_screen
        self.user_data = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('تسجيل الدخول - نظام الإمداد والتموين')
        self.setFixedSize(400, 300)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        if self.is_lock_screen:
            self.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )

        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.addWidget(make_header_label('نظام الإمداد والتموين'))

        if self.is_lock_screen:
            lbl_lock = QLabel('تم قفل الشاشة لحماية بياناتك بسبب الخمول.')
            lbl_lock.setStyleSheet('color: ' + COLORS['danger'] + '; font-weight: bold;')
            lay.addWidget(lbl_lock)

        lay.addWidget(QLabel('رمز المستخدم:'))
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText('اسم المستخدم (Username)')
        lay.addWidget(self.txt_user)

        lay.addWidget(QLabel('كلمة المرور:'))
        pwd_lay = QHBoxLayout()
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText('كلمة المرور')
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        pwd_lay.addWidget(self.txt_pass)

        self.btn_toggle_pwd = QPushButton()
        self.btn_toggle_pwd.setIcon(qta.icon('fa5s.eye', color='gray'))
        self.btn_toggle_pwd.setStyleSheet('background: transparent; border: none;')
        self.btn_toggle_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_pwd.clicked.connect(self._toggle_password)
        pwd_lay.addWidget(self.btn_toggle_pwd)

        lay.addLayout(pwd_lay)

        ok, res = self.api_service.check_device(None)
        device_status = res.get('status', 'UNKNOWN') if isinstance(res, dict) else 'UNKNOWN'

        self.lbl_device_msg = QLabel()
        self.lbl_device_msg.setWordWrap(True)
        self.lbl_device_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if device_status == 'PENDING':
            self.lbl_device_msg.setText(
                '⚠️ جهازك ما زال قيد الانتظار.\n'
                'يرجى التواصل مع الإدارة وتزويدهم برمز جهازك للموافقة عليه:\n'
                + str(res.get('hardware_id', ''))
            )
        elif device_status == 'BLOCKED':
            self.lbl_device_msg.setText('❌ هذا الجهاز محظور من دخول النظام.')

        lay.addWidget(self.lbl_device_msg)

        btns = QHBoxLayout()
        self.btn_login = QPushButton('دخول')
        self.btn_login.setIcon(qta.icon('fa5s.sign-in-alt', color='white'))
        self.btn_login.setStyleSheet(
            'background-color: ' + COLORS['green_primary']
            + '; color: white; font-weight: bold; padding: 10px;'
        )
        self.btn_login.clicked.connect(self._do_login)
        self.btn_login.setEnabled(device_status not in ('PENDING', 'BLOCKED'))
        btns.addWidget(self.btn_login)

        self.btn_exit = QPushButton('خروج')
        self.btn_exit.setStyleSheet('background-color: #6c757d; color: white; padding: 10px;')
        self.btn_exit.clicked.connect(self.reject)
        btns.addWidget(self.btn_exit)

        lay.addLayout(btns)

        from loading_overlay import LoadingOverlay
        self.loading_overlay = LoadingOverlay(self, text='جاري المصادقة...')
        self.loading_overlay.hide()

    def _toggle_password(self):
        if self.txt_pass.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_pass.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_pwd.setIcon(qta.icon('fa5s.eye-slash', color='gray'))
        else:
            self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_pwd.setIcon(qta.icon('fa5s.eye', color='gray'))

    def _do_login(self):
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text().strip()

        if not user or not pwd:
            QMessageBox.warning(self, 'خطأ', 'يرجى تعبئة كافة الحقول')
            return

        self.btn_login.setEnabled(False)
        self.loading_overlay.show_overlay('جاري التحميل وتهيئة النظام ⏳...')

        import PyQt6.QtWidgets as QtWidgets
        QtWidgets.QApplication.processEvents()

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._process_login(user, pwd))

    def _process_login(self, user, pwd):
        ok, res = self.api_service.login(user, pwd)

        if ok and isinstance(res, dict) and res.get('id'):
            self.user_data = res
            self.loading_overlay.hide_overlay()
            self.accept()
        else:
            self.loading_overlay.hide_overlay()
            self.btn_login.setEnabled(True)

            err = res.get('detail', 'فشل تسجيل الدخول') if isinstance(res, dict) else 'خطأ في الاتصال'
            QMessageBox.critical(self, 'خطأ', str(err))
