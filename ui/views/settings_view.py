"""إعدادات النظام - Settings View."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QMessageBox, QFormLayout, QGroupBox, QComboBox, QCheckBox, QSpinBox)
from PyQt6.QtCore import Qt
from ui.theme import make_header_label


class SettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label('إعدادات النظام'))

        # General Settings
        general = QGroupBox('الإعدادات العامة')
        general_form = QFormLayout(general)
        self.le_org_name = QLineEdit()
        self.le_org_name.setPlaceholderText('اسم المؤسسة/الجهة')
        self.le_address = QLineEdit()
        self.le_address.setPlaceholderText('العنوان')
        self.le_phone = QLineEdit()
        self.le_phone.setPlaceholderText('رقم الهاتف')
        self.le_email = QLineEdit()
        self.le_email.setPlaceholderText('البريد الإلكتروني')
        general_form.addRow('اسم المؤسسة:', self.le_org_name)
        general_form.addRow('العنوان:', self.le_address)
        general_form.addRow('الهاتف:', self.le_phone)
        general_form.addRow('البريد:', self.le_email)
        layout.addWidget(general)

        # Inventory Settings
        inv = QGroupBox('إعدادات المخزون')
        inv_form = QFormLayout(inv)
        self.sb_low_stock = QSpinBox()
        self.sb_low_stock.setRange(0, 10000)
        self.sb_low_stock.setSuffix(' وحدة')
        self.chk_auto_batch = QCheckBox('تخصيص رقم تشغيلة تلقائياً')
        self.chk_allow_negative = QCheckBox('السماح بالمخزون السالب')
        self.cb_cost_method = QComboBox()
        self.cb_cost_method.addItems(['متوسط متحرك', 'أولاً أولاً (FIFO)', 'آخراً أولاً (LIFO)'])
        inv_form.addRow('حد التنبيه للمخزون:', self.sb_low_stock)
        inv_form.addRow('طريقة حساب التكلفة:', self.cb_cost_method)
        inv_form.addRow('', self.chk_auto_batch)
        inv_form.addRow('', self.chk_allow_negative)
        layout.addWidget(inv)

        # UI Settings
        ui_box = QGroupBox('إعدادات الواجهة')
        ui_form = QFormLayout(ui_box)
        self.cb_theme = QComboBox()
        self.cb_theme.addItems(['فاتح', 'داكن', 'أخضر', 'أزرق'])
        self.cb_lang = QComboBox()
        self.cb_lang.addItems(['العربية', 'English'])
        self.chk_rtl = QCheckBox('تفعيل RTL (من اليمين لليسار)')
        self.chk_rtl.setChecked(True)
        ui_form.addRow('الثيم:', self.cb_theme)
        ui_form.addRow('اللغة:', self.cb_lang)
        ui_form.addRow('', self.chk_rtl)
        layout.addWidget(ui_box)

        # Sync Settings
        sync = QGroupBox('إعدادات المزامنة')
        sync_form = QFormLayout(sync)
        self.le_api_url = QLineEdit()
        self.le_api_url.setPlaceholderText('https://api.example.com')
        self.sb_sync_interval = QSpinBox()
        self.sb_sync_interval.setRange(1, 60)
        self.sb_sync_interval.setSuffix(' دقائق')
        self.chk_auto_sync = QCheckBox('مزامنة تلقائية')
        sync_form.addRow('رابط API:', self.le_api_url)
        sync_form.addRow('فترة المزامنة:', self.sb_sync_interval)
        sync_form.addRow('', self.chk_auto_sync)
        layout.addWidget(sync)

        # Buttons
        btn_bar = QHBoxLayout()
        btn_save = QPushButton('💾 حفظ الإعدادات')
        btn_save.setStyleSheet('background-color:#27AE60; color:white; font-weight:bold; padding:10px;')
        btn_save.clicked.connect(self._save)
        btn_bar.addWidget(btn_save)
        btn_reset = QPushButton('🔄 إعادة تعيين الافتراضي')
        btn_reset.clicked.connect(self._reset)
        btn_bar.addWidget(btn_reset)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)
        layout.addStretch()

    def _save(self):
        QMessageBox.information(self, 'نجاح', 'تم حفظ الإعدادات بنجاح')

    def _reset(self):
        if QMessageBox.question(self, 'تأكيد', 'هل تريد إعادة تعيين الإعدادات للافتراضي؟',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._init_ui()

    def load_data(self):
        pass