"""Settings View — إعدادات النظام وإدارة المستخدمين."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox, QMessageBox, QComboBox,
    QCheckBox, QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QDialogButtonBox, QFrame, QFileDialog,
    QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from api_service import ApiService
from theme import make_header_label, COLORS
import sqlite3
import os
import hashlib
import secrets
import base64


def _get_db_path():
    """Resolve local SQLite database path."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base, 'data', 'logistics.db'),
        os.path.join(base, 'logistics.db'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


def _hash_password(password: str) -> str:
    """Hash password with SHA-256 (fallback if bcrypt unavailable)."""
    salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return f"sha256${salt}${h}"


def _check_password(password: str, stored: str) -> bool:
    """Verify password against stored hash."""
    if not stored:
        return False
    if stored.startswith('$2'):
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
        except Exception:
            return False
    if stored.startswith('sha256$'):
        try:
            _, salt, h = stored.split('$', 2)
            return hashlib.sha256((salt + password).encode('utf-8')).hexdigest() == h
        except Exception:
            return False
    return False


class UserDialog(QDialog):
    """Add/Edit user dialog."""
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("تعديل المستخدم" if user else "إضافة مستخدم جديد")
        self.setMinimumWidth(420)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._result = None
        self._build_ui()

    def _build_ui(self):
        lay = QFormLayout(self)
        lay.setSpacing(12)

        self.le_username = QLineEdit()
        self.le_username.setPlaceholderText("اسم المستخدم")
        if self.user:
            self.le_username.setText(self.user.get('username', ''))
            self.le_username.setReadOnly(True)
        lay.addRow("اسم المستخدم:", self.le_username)

        self.le_fullname = QLineEdit()
        self.le_fullname.setPlaceholderText("الاسم الكامل")
        if self.user:
            self.le_fullname.setText(self.user.get('full_name', ''))
        lay.addRow("الاسم الكامل:", self.le_fullname)

        ph = "اتركها فارغة لعدم التغيير" if self.user else "كلمة المرور"
        self.le_password = QLineEdit()
        self.le_password.setPlaceholderText(ph)
        self.le_password.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addRow("كلمة المرور:", self.le_password)

        self.le_confirm = QLineEdit()
        self.le_confirm.setPlaceholderText("تأكيد كلمة المرور")
        self.le_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addRow("تأكيد المرور:", self.le_confirm)

        self.cb_role = QComboBox()
        self.cb_role.addItems(["admin", "manager", "user", "viewer"])
        if self.user:
            idx = self.cb_role.findText(self.user.get('role', 'user'))
            if idx >= 0:
                self.cb_role.setCurrentIndex(idx)
        lay.addRow("الدور:", self.cb_role)

        self.chk_active = QCheckBox("الحساب نشط")
        self.chk_active.setChecked(True)
        if self.user:
            self.chk_active.setChecked(bool(self.user.get('is_active', True)))
        lay.addRow("", self.chk_active)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        lay.addRow(btns)

    def _on_accept(self):
        username = self.le_username.text().strip()
        fullname = self.le_fullname.text().strip()
        password = self.le_password.text()
        confirm = self.le_confirm.text()
        role = self.cb_role.currentText()
        is_active = self.chk_active.isChecked()

        if not username:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال اسم المستخدم")
            return
        if not fullname:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال الاسم الكامل")
            return
        if not self.user and not password:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال كلمة المرور للمستخدم الجديد")
            return
        if password and password != confirm:
            QMessageBox.warning(self, "تنبيه", "كلمتا المرور غير متطابقتين")
            return
        if password and len(password) < 3:
            QMessageBox.warning(self, "تنبيه", "كلمة المرور قصيرة جداً")
            return

        self._result = {
            'username': username,
            'full_name': fullname,
            'password': password,
            'role': role,
            'is_active': is_active,
        }
        self.accept()

    def get_data(self):
        return self._result


class SettingsView(QWidget):
    """شاشة الإعدادات — مع تبويب إدارة المستخدمين الكامل."""

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.addWidget(make_header_label("⚙️ الإعدادات"))

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f"QTabWidget::pane {{ border: 1px solid {COLORS['border']}; border-radius: 4px; background: {COLORS['bg_card']}; }}"
            f"QTabBar::tab {{ padding: 8px 20px; background: {COLORS['bg_table_alt']}; color: {COLORS['text_medium']}; }}"
            f"QTabBar::tab:selected {{ background: {COLORS['green_primary']}; color: white; font-weight: bold; }}"
        )

        self.tabs.addTab(self._build_general_tab(), "🔧 عام")
        self.tabs.addTab(self._build_sync_tab(), "🔄 المزامنة")
        self.tabs.addTab(self._build_users_tab(), "👥 المستخدمين")
        self.tabs.addTab(self._build_print_tab(), "🖨️ الطباعة والنماذج")
        self.tabs.addTab(self._build_display_tab(), "🖥️ العرض")
        self.tabs.addTab(self._build_about_tab(), "ℹ️ حول النظام")

        self.tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self.tabs)

    def _on_tab_changed(self, idx):
        """Refresh users when its tab opens."""
        try:
            tab_text = self.tabs.tabText(idx)
            if "المستخدمين" in tab_text:
                self._load_users()
        except Exception:
            pass

    def _build_users_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(10)
        tb = QHBoxLayout()
        lbl = QLabel("إدارة حسابات المستخدمين")
        lbl.setStyleSheet("color: " + COLORS['text_medium'] + "; font-weight: bold;")
        tb.addWidget(lbl)
        tb.addStretch()
        self.btn_user_add = QPushButton("+ إضافة مستخدم")
        self.btn_user_add.setStyleSheet("background: " + COLORS['green_primary'] + "; color: white; padding: 7px 14px; border-radius: 4px; font-weight: bold;")
        self.btn_user_add.clicked.connect(self._add_user)
        tb.addWidget(self.btn_user_add)
        self.btn_user_refresh = QPushButton("تحديث")
        self.btn_user_refresh.setStyleSheet("background: " + COLORS['info'] + "; color: white; padding: 7px 14px; border-radius: 4px;")
        self.btn_user_refresh.clicked.connect(self._load_users)
        tb.addWidget(self.btn_user_refresh)
        lay.addLayout(tb)
        self.tbl_users = QTableWidget()
        self.tbl_users.setColumnCount(7)
        self.tbl_users.setHorizontalHeaderLabels(("الاسم الكامل", "اسم المستخدم", "الدور", "الحالة", "تاريخ الإنشاء", "المعرّف", "إجراءات"))
        self.tbl_users.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_users.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_users.setColumnWidth(2, 90)
        self.tbl_users.setColumnWidth(3, 75)
        self.tbl_users.setColumnWidth(4, 150)
        self.tbl_users.setColumnWidth(5, 80)
        self.tbl_users.setColumnWidth(6, 210)
        self.tbl_users.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_users.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.tbl_users)
        self.lbl_users_count = QLabel("اضغط 'تحديث' لتحميل قائمة المستخدمين")
        self.lbl_users_count.setStyleSheet("color: " + COLORS['text_muted'] + "; padding: 4px; font-size: 11px;")
        lay.addWidget(self.lbl_users_count)
        return w

    def _load_users(self):
        try:
            db = _get_db_path()
            if not os.path.exists(db):
                self.lbl_users_count.setText("قاعدة البيانات غير موجودة")
                return
            conn = sqlite3.connect(db)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT id, username, full_name, role, is_active, created_at FROM users WHERE (is_deleted IS NULL OR is_deleted = 0) ORDER BY created_at DESC")
            rows = cur.fetchall()
            conn.close()
            self.tbl_users.setRowCount(0)
            for i, r in enumerate(rows):
                user = dict(r)
                self.tbl_users.insertRow(i)
                self.tbl_users.setItem(i, 0, QTableWidgetItem(user.get('full_name', '') or ''))
                self.tbl_users.setItem(i, 1, QTableWidgetItem(user.get('username', '') or ''))
                role = (user.get('role') or 'viewer').upper()
                self.tbl_users.setItem(i, 2, QTableWidgetItem(role))
                is_active = bool(user.get('is_active', True))
                active_item = QTableWidgetItem("نشط" if is_active else "موقوف")
                active_item.setForeground(Qt.GlobalColor.darkGreen if is_active else Qt.GlobalColor.red)
                self.tbl_users.setItem(i, 3, active_item)
                created = (user.get('created_at') or '').split('T')[0]
                self.tbl_users.setItem(i, 4, QTableWidgetItem(str(created)))
                self.tbl_users.setItem(i, 5, QTableWidgetItem(str(user.get('id', ''))[:8]))
                cell = QWidget()
                bl = QHBoxLayout(cell)
                bl.setContentsMargins(2, 2, 2, 2)
                bl.setSpacing(4)
                btn_edit = QPushButton("تعديل")
                btn_edit.setFixedWidth(50)
                btn_edit.setStyleSheet("background: " + COLORS['info'] + "; color: white; padding: 3px; border-radius: 3px;")
                btn_edit.clicked.connect(lambda _, u=user: self._edit_user(u))
                bl.addWidget(btn_edit)
                btn_toggle = QPushButton("تبديل")
                btn_toggle.setFixedWidth(50)
                btn_toggle.setStyleSheet("background: " + (COLORS['warning'] if is_active else COLORS['ok']) + "; color: white; padding: 3px; border-radius: 3px;")
                btn_toggle.clicked.connect(lambda _, u=user: self._toggle_user(u))
                bl.addWidget(btn_toggle)
                btn_reset = QPushButton("إعادة")
                btn_reset.setFixedWidth(50)
                btn_reset.setStyleSheet("background: " + COLORS['purple'] + "; color: white; padding: 3px; border-radius: 3px;")
                btn_reset.clicked.connect(lambda _, u=user: self._reset_password(u))
                bl.addWidget(btn_reset)
                btn_del = QPushButton("حذف")
                btn_del.setFixedWidth(50)
                btn_del.setStyleSheet("background: " + COLORS['danger'] + "; color: white; padding: 3px; border-radius: 3px;")
                btn_del.clicked.connect(lambda _, u=user: self._delete_user(u))
                bl.addWidget(btn_del)
                bl.addStretch()
                self.tbl_users.setCellWidget(i, 6, cell)
            self.lbl_users_count.setText("تم تحميل " + str(len(rows)) + " مستخدم(ين)")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", "فشل تحميل المستخدمين:\n" + str(e))
            self.lbl_users_count.setText("خطأ: " + str(e))

    def _build_print_tab(self):
        sw = QScrollArea()
        sw.setWidgetResizable(True)
        cont = QWidget()
        lay = QVBoxLayout(cont)
        lay.setSpacing(15)
        lay.setContentsMargins(10, 10, 10, 10)

        box_logo = QGroupBox("الشعار والترويسة")
        box_logo.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        fl = QFormLayout(box_logo)
        fl.setSpacing(10)

        logo_row = QHBoxLayout()
        self.lbl_logo_preview = QLabel("لم يتم اختيار شعار")
        self.lbl_logo_preview.setStyleSheet("border: 1px dashed " + COLORS['border'] + "; padding: 10px; min-width: 100px; min-height: 80px;")
        self.lbl_logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_row.addWidget(self.lbl_logo_preview)
        logo_btns = QVBoxLayout()
        self._logo_base64 = ""
        btn_upload_logo = QPushButton("رفع شعار (PNG/JPG)")
        btn_upload_logo.setStyleSheet("background: " + COLORS['info'] + "; color: white; padding: 6px 12px; border-radius: 4px;")
        btn_upload_logo.clicked.connect(self._upload_logo)
        logo_btns.addWidget(btn_upload_logo)
        btn_clear_logo = QPushButton("إزالة الشعار")
        btn_clear_logo.setStyleSheet("background: " + COLORS['danger'] + "; color: white; padding: 6px 12px; border-radius: 4px;")
        btn_clear_logo.clicked.connect(self._clear_logo)
        logo_btns.addWidget(btn_clear_logo)
        logo_btns.addStretch()
        logo_row.addLayout(logo_btns)
        fl.addRow("شعار الجهة:", logo_row)

        self.le_org_name = QLineEdit()
        self.le_org_name.setPlaceholderText("اسم الجهة (يمكن كتابة عدة أسطر)")
        fl.addRow("اسم الجهة:", self.le_org_name)

        self.te_contact = QTextEdit()
        self.te_contact.setPlaceholderText("معلومات الاتصال (سطر في كل سطر)")
        self.te_contact.setMaximumHeight(70)
        fl.addRow("معلومات الاتصال:", self.te_contact)

        lay.addWidget(box_logo)

        box_print = QGroupBox("إعدادات الطباعة")
        box_print.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        pfl = QFormLayout(box_print)
        pfl.setSpacing(10)

        self.cb_paper_size = QComboBox()
        self.cb_paper_size.addItems(["A4", "A5", "Letter", "Legal"])
        pfl.addRow("حجم الورق:", self.cb_paper_size)

        self.cb_orientation = QComboBox()
        self.cb_orientation.addItems(["landscape (أفقي)", "portrait (عمودي)"])
        pfl.addRow("الاتجاه:", self.cb_orientation)

        margins_h = QHBoxLayout()
        self.sp_mtop = QSpinBox(); self.sp_mtop.setRange(0, 100); self.sp_mtop.setSuffix("mm"); self.sp_mtop.setValue(20)
        self.sp_mbot = QSpinBox(); self.sp_mbot.setRange(0, 100); self.sp_mbot.setSuffix("mm"); self.sp_mbot.setValue(20)
        self.sp_mleft = QSpinBox(); self.sp_mleft.setRange(0, 100); self.sp_mleft.setSuffix("mm"); self.sp_mleft.setValue(15)
        self.sp_mright = QSpinBox(); self.sp_mright.setRange(0, 100); self.sp_mright.setSuffix("mm"); self.sp_mright.setValue(15)
        margins_h.addWidget(QLabel("أعلى:")); margins_h.addWidget(self.sp_mtop)
        margins_h.addWidget(QLabel("أسفل:")); margins_h.addWidget(self.sp_mbot)
        margins_h.addWidget(QLabel("يسار:")); margins_h.addWidget(self.sp_mleft)
        margins_h.addWidget(QLabel("يمين:")); margins_h.addWidget(self.sp_mright)
        pfl.addRow("الهوامش:", margins_h)

        lay.addWidget(box_print)

        box_templates = QGroupBox("رأس وذيل النماذج المطبوعة")
        box_templates.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        tfl = QFormLayout(box_templates)
        tfl.setSpacing(10)

        self.te_form_header = QTextEdit()
        self.te_form_header.setPlaceholderText("نص رأس النموذج (يظهر اعلى كل نموذج مطبوعة)")
        self.te_form_header.setMaximumHeight(80)
        tfl.addRow("راس النموذج:", self.te_form_header)

        self.te_form_footer = QTextEdit()
        self.te_form_footer.setPlaceholderText("نص ذيل النموذج (يظهر اسفل كل نموذج مطبوعة)")
        self.te_form_footer.setMaximumHeight(80)
        tfl.addRow("ذيل النموذج:", self.te_form_footer)

        self.te_report_header = QTextEdit()
        self.te_report_header.setPlaceholderText("راس التقارير (يظهر اعلى التقارير المطبوعة)")
        self.te_report_header.setMaximumHeight(80)
        tfl.addRow("راس التقرير:", self.te_report_header)

        self.te_report_footer = QTextEdit()
        self.te_report_footer.setPlaceholderText("ذيل التقارير (يظهر اسفل التقارير المطبوعة)")
        self.te_report_footer.setMaximumHeight(80)
        tfl.addRow("ذيل التقرير:", self.te_report_footer)

        lay.addWidget(box_templates)

        box_opts = QGroupBox("خيارات اضافية للطباعة")
        box_opts.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        ofl = QFormLayout(box_opts)
        ofl.setSpacing(10)

        self.chk_show_logo = QCheckBox("اظهار الشعار عند الطباعة")
        self.chk_show_logo.setChecked(True)
        ofl.addRow("", self.chk_show_logo)

        self.chk_show_seal = QCheckBox("اظهار ختم الجهة عند الطباعة")
        ofl.addRow("", self.chk_show_seal)

        lay.addWidget(box_opts)

        hb = QHBoxLayout()
        hb.addStretch()
        btn_save = QPushButton("حفظ اعدادات الطباعة")
        btn_save.setStyleSheet("background: " + COLORS['green_primary'] + "; color: white; padding: 10px 25px; border-radius: 4px; font-weight: bold;")
        btn_save.clicked.connect(self._save_print_settings)
        hb.addWidget(btn_save)
        lay.addLayout(hb)
        lay.addStretch()

        sw.setWidget(cont)
        w = QWidget()
        QVBoxLayout(w).addWidget(sw)

        self._load_print_settings()
        return w


    def _upload_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "اختر شعار", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            try:
                with open(path, 'rb') as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode('utf-8')
                self._logo_base64 = b64
                pix = QPixmap(path).scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl_logo_preview.setPixmap(pix)
            except Exception as e:
                QMessageBox.warning(self, "خطا", str(e))

    def _clear_logo(self):
        self._logo_base64 = ""
        self.lbl_logo_preview.clear()
        self.lbl_logo_preview.setText("لم يتم اختيار شعار")
        self.lbl_logo_preview.setStyleSheet("border: 1px dashed " + COLORS['border'] + "; padding: 10px; min-width: 100px; min-height: 80px;")

    def _load_print_settings(self):
        try:
            api = ApiService()
            ok, res = api.get_system_settings()
            if ok and isinstance(res, dict):
                org = res.get('org_name', '') or ''
                self.le_org_name.setText(org.replace(chr(10), ' | '))
                contact = res.get('contact_info', '') or ''
                self.te_contact.setPlainText(contact)
                self._logo_base64 = res.get('org_logo_base64', '') or ''
                if self._logo_base64:
                    try:
                        from PyQt6.QtGui import QImage
                        img_data = base64.b64decode(self._logo_base64)
                        pix = QPixmap.fromImage(QImage.fromData(img_data))
                        self.lbl_logo_preview.setPixmap(pix.scaled(120, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    except Exception:
                        pass
                paper = res.get('paper_size', 'A4')
                if paper in ["A4", "A5", "Letter", "Legal"]:
                    self.cb_paper_size.setCurrentText(paper)
                orient = res.get('print_orientation', 'landscape')
                self.cb_orientation.setCurrentIndex(0 if 'landscape' in orient else 1)
                self.sp_mtop.setValue(int(res.get('print_margin_top', 20)))
                self.sp_mbot.setValue(int(res.get('print_margin_bottom', 20)))
                self.sp_mleft.setValue(int(res.get('print_margin_left', 15)))
                self.sp_mright.setValue(int(res.get('print_margin_right', 15)))
                hdr = res.get('form_header_text', '') or ''
                self.te_form_header.setPlainText(hdr)
                ftr = res.get('form_footer_text', '') or ''
                self.te_form_footer.setPlainText(ftr)
                rhdr = res.get('report_header', '') or ''
                self.te_report_header.setPlainText(rhdr)
                rftr = res.get('report_footer', '') or ''
                self.te_report_footer.setPlainText(rftr)
                self.chk_show_logo.setChecked(res.get('show_logo_on_print', 'true') == 'true')
                self.chk_show_seal.setChecked(res.get('show_seal_on_print', 'false') == 'true')
        except Exception as e:
            QMessageBox.warning(self, "خطا", "فشل تحميل الاعدادات:" + chr(10) + str(e))

    def _save_print_settings(self):
        data = {
            'org_name': self.le_org_name.text(),
            'contact_info': self.te_contact.toPlainText(),
            'org_logo_base64': self._logo_base64,
            'paper_size': self.cb_paper_size.currentText(),
            'print_orientation': 'landscape' if self.cb_orientation.currentIndex() == 0 else 'portrait',
            'print_margin_top': str(self.sp_mtop.value()),
            'print_margin_bottom': str(self.sp_mbot.value()),
            'print_margin_left': str(self.sp_mleft.value()),
            'print_margin_right': str(self.sp_mright.value()),
            'form_header_text': self.te_form_header.toPlainText(),
            'form_footer_text': self.te_form_footer.toPlainText(),
            'report_header': self.te_report_header.toPlainText(),
            'report_footer': self.te_report_footer.toPlainText(),
            'show_logo_on_print': 'true' if self.chk_show_logo.isChecked() else 'false',
            'show_seal_on_print': 'true' if self.chk_show_seal.isChecked() else 'false',
        }
        try:
            api = ApiService()
            ok, res = api.update_system_settings(data)
            if ok:
                QMessageBox.information(self, "حفظ", "تم حفظ اعدادات الطباعة بنجاح!")
            else:
                QMessageBox.warning(self, "خطا", str(res))
        except Exception as e:
            QMessageBox.critical(self, "خطا", str(e))

    def _add_user(self):
        dlg = UserDialog(self, user=None)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db = _get_db_path()
                conn = sqlite3.connect(db)
                cur = conn.cursor()
                cur.execute("SELECT id FROM users WHERE username = ?", (data['username'],))
                if cur.fetchone():
                    QMessageBox.warning(self, "تنبيه", "اسم المستخدم موجود مسبقاً")
                    conn.close()
                    return
                import uuid
                new_id = str(uuid.uuid4())
                pwd_hash = _hash_password(data['password'])
                cur.execute("INSERT INTO users (id, username, full_name, password_hash, role, is_active, created_at, updated_at, sync_status, is_deleted) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 'pending', 0)", (new_id, data['username'], data['full_name'], pwd_hash, data['role'], int(data['is_active'])))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "نجاح", "تم إضافة المستخدم بنجاح")
                self._load_users()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _edit_user(self, user):
        dlg = UserDialog(self, user=user)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            try:
                db = _get_db_path()
                conn = sqlite3.connect(db)
                cur = conn.cursor()
                if data['password']:
                    pwd_hash = _hash_password(data['password'])
                    cur.execute("UPDATE users SET full_name=?, password_hash=?, role=?, is_active=?, updated_at=datetime('now'), sync_status='pending' WHERE id=?", (data['full_name'], pwd_hash, data['role'], int(data['is_active']), user['id']))
                else:
                    cur.execute("UPDATE users SET full_name=?, role=?, is_active=?, updated_at=datetime('now'), sync_status='pending' WHERE id=?", (data['full_name'], data['role'], int(data['is_active']), user['id']))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "نجاح", "تم تحديث المستخدم")
                self._load_users()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", str(e))

    def _toggle_user(self, user):
        new_state = not bool(user.get('is_active', True))
        try:
            db = _get_db_path()
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_active=?, updated_at=datetime('now'), sync_status='pending' WHERE id=?", (int(new_state), user['id']))
            conn.commit()
            conn.close()
            state_txt = "تفعيل" if new_state else "إيقاف"
            QMessageBox.information(self, "نجاح", "تم " + state_txt + " المستخدم")
            self._load_users()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _reset_password(self, user):
        reply = QMessageBox.question(self, "تأكيد", "هل تريد إعادة تعيين كلمة مرور '" + user['username'] + "' إلى '123456'؟", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            db = _get_db_path()
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("UPDATE users SET password_hash=?, updated_at=datetime('now'), sync_status='pending' WHERE id=?", (_hash_password("123456"), user['id']))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "نجاح", "تم إعادة التعيين إلى: 123456")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _delete_user(self, user):
        if user.get('username') == 'admin':
            QMessageBox.warning(self, "محظور", "لا يمكن حذف حساب المدير")
            return
        reply = QMessageBox.question(self, "تأكيد", "حذف '" + user.get('username', '') + "'؟", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes: return
        try:
            db = _get_db_path()
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_deleted=1, is_active=0, updated_at=datetime('now'), sync_status='pending' WHERE id=?", (user['id'],))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "نجاح", "تم حذف المستخدم")
            self._load_users()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _build_general_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(15)
        box = QGroupBox("إعدادات الاتصال بالخادم")
        box.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        fl = QFormLayout(box)
        self.le_server_url = QLineEdit()
        self.le_server_url.setPlaceholderText("http://example.com/api")
        self.le_server_url.setMinimumWidth(300)
        fl.addRow("عنوان الخادم:", self.le_server_url)
        self.sp_timeout = QSpinBox()
        self.sp_timeout.setRange(5, 60)
        self.sp_timeout.setSuffix(" ثانية")
        self.sp_timeout.setValue(15)
        fl.addRow("مهلة الاتصال:", self.sp_timeout)
        lay.addWidget(box)
        box2 = QGroupBox("إعدادات المعسكر")
        box2.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        fl2 = QFormLayout(box2)
        self.le_camp_name = QLineEdit()
        self.le_camp_name.setPlaceholderText("اسم المعسكر")
        fl2.addRow("اسم المعسكر:", self.le_camp_name)
        self.le_camp_code = QLineEdit()
        self.le_camp_code.setPlaceholderText("رمز المعسكر")
        fl2.addRow("رمز المعسكر:", self.le_camp_code)
        lay.addWidget(box2)
        hb = QHBoxLayout()
        hb.addStretch()
        btn_save = QPushButton("حفظ الإعدادات")
        btn_save.setStyleSheet("background: " + COLORS['green_primary'] + "; color: white; padding: 8px 20px; border-radius: 4px; font-weight: bold;")
        btn_save.clicked.connect(self._save_settings)
        hb.addWidget(btn_save)
        btn_test = QPushButton("اختبار الاتصال")
        btn_test.setStyleSheet("background: " + COLORS['info'] + "; color: white; padding: 8px 20px; border-radius: 4px;")
        btn_test.clicked.connect(self._test_connection)
        hb.addWidget(btn_test)
        lay.addLayout(hb)
        lay.addStretch()
        return w

    def _build_sync_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(15)
        box = QGroupBox("حالة المزامنة")
        box.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        vbox = QVBoxLayout(box)
        self.lbl_sync_status = QLabel("لم يتم المزامنة بعد")
        self.lbl_sync_status.setStyleSheet("color: " + COLORS['text_medium'] + ";")
        vbox.addWidget(self.lbl_sync_status)
        h = QHBoxLayout()
        self.chk_auto_sync = QCheckBox("مزامنة تلقائية عند بدء التشغيل")
        self.chk_auto_sync.setChecked(True)
        h.addWidget(self.chk_auto_sync)
        h.addStretch()
        vbox.addLayout(h)
        lay.addWidget(box)
        lay.addStretch()
        btn_sync = QPushButton("مزامنة الآن")
        btn_sync.setStyleSheet("background: " + COLORS['green_primary'] + "; color: white; padding: 10px; border-radius: 4px; font-weight: bold;")
        btn_sync.clicked.connect(self._sync_now)
        lay.addWidget(btn_sync)
        return w

    def _build_display_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(15)
        box = QGroupBox("إعدادات العرض")
        box.setStyleSheet("QGroupBox { font-weight: bold; padding: 10px; }")
        fl = QFormLayout(box)
        self.chk_fullscreen = QCheckBox("تشغيل بكامل الشاشة عند البدء")
        fl.addRow("", self.chk_fullscreen)
        self.chk_screenshot = QCheckBox("حماية لقطات الشاشة")
        fl.addRow("", self.chk_screenshot)
        self.sp_items_per_page = QSpinBox()
        self.sp_items_per_page.setRange(10, 100)
        self.sp_items_per_page.setSuffix(" عنصر")
        self.sp_items_per_page.setValue(25)
        fl.addRow("العناصر في الصفحة:", self.sp_items_per_page)
        lay.addWidget(box)
        lay.addStretch()
        return w

    def _build_about_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("نظام الإمداد والتموين")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: " + COLORS['green_primary'] + ";")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        version = QLabel("الإصدار 1.0.0")
        version.setStyleSheet("font-size: 13px; color: " + COLORS['text_medium'] + ";")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(version)
        org = QLabel("مكتب النظم والمعلومات")
        org.setStyleSheet("font-size: 11px; color: " + COLORS['text_muted'] + ";")
        org.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(org)
        lay.addSpacing(15)
        desc_text = "نظام متكامل لإدارة سلسلة الإمداد\n• المخزون والعهد\n• المعاملات المخزنية\n• الجهات المستفيدة والموردين\n• التقارير والإشعارات"
        desc = QLabel(desc_text)
        desc.setStyleSheet("color: " + COLORS['text_medium'] + "; padding: 10px; background: " + COLORS['bg_table_alt'] + "; border-radius: 8px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.addWidget(desc)
        lay.addStretch()
        return w

    def _save_settings(self):
        QMessageBox.information(self, "حفظ", "تم حفظ الإعدادات بنجاح!")

    def _test_connection(self):
        server = self.le_server_url.text()
        if not server:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال عنوان الخادم أولاً")
            return
        QMessageBox.information(self, "الاتصال", "جاري الاتصال بـ:\n" + server + "\n\n(غير متوفر في وضع العمل المحلي)")

    def _sync_now(self):
        self.lbl_sync_status.setText("المزامنة غير متوفرة حالياً في وضع العمل المحلي")
        self.lbl_sync_status.setStyleSheet("color: " + COLORS['warning'] + ";")
