"""سجل التدقيق - Audit Log View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDateEdit,
    QMessageBox, QFormLayout, QAbstractItemView, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService
from ui.theme import make_header_label


class AuditLogView(QWidget):
    """سجل التدقيق - عرض جميع العمليات والتغييرات في النظام."""

    def __init__(self, parent=None, api_service: ApiService | None = None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()
        self._load_logs()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label('سجل التدقيق (سجل العمليات)'))
        filter_card = QGroupBox('تصفية السجلات')
        filter_layout = QFormLayout(filter_card)
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-7))
        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        self.cb_action = QComboBox()
        self.cb_action.addItems(['الكل', 'إنشاء', 'تعديل', 'حذف', 'اعتماد', 'رفض', 'تسجيل دخول', 'تسجيل خروج'])
        self.le_user = QLineEdit()
        self.le_user.setPlaceholderText('اسم المستخدم (اختياري)')
        self.le_entity = QLineEdit()
        self.le_entity.setPlaceholderText('اسم الجدول/الكيان (اختياري)')
        filter_layout.addRow('من تاريخ:', self.dt_from)
        filter_layout.addRow('إلى تاريخ:', self.dt_to)
        filter_layout.addRow('نوع العملية:', self.cb_action)
        filter_layout.addRow('المستخدم:', self.le_user)
        filter_layout.addRow('الكيان:', self.le_entity)
        layout.addWidget(filter_card)
        btn_bar = QHBoxLayout()
        btn_search = QPushButton('🔍 بحث')
        btn_search.clicked.connect(self._load_logs)
        btn_bar.addWidget(btn_search)
        btn_export = QPushButton('📥 تصدير Excel')
        btn_export.clicked.connect(self._export)
        btn_bar.addWidget(btn_export)
        btn_export_pdf = QPushButton('📄 تصدير PDF')
        btn_export_pdf.clicked.connect(self._export_pdf)
        btn_bar.addWidget(btn_export_pdf)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(7)
        self.tbl.setHorizontalHeaderLabels(['#', 'التاريخ والوقت', 'المستخدم', 'نوع العملية', 'الكيان', 'رقم السجل', 'التفاصيل'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(True)
        layout.addWidget(self.tbl, 1)
        self.lbl_summary = QLabel()
        self.lbl_summary.setStyleSheet("background-color:#E8F5E9; padding:8px; border-radius:4px; font-weight:bold;")
        layout.addWidget(self.lbl_summary)

    def _load_logs(self):
        action_map = {'الكل': None, 'إنشاء': 'CREATE', 'تعديل': 'UPDATE', 'حذف': 'DELETE',
            'اعتماد': 'APPROVE', 'رفض': 'REJECT', 'تسجيل دخول': 'LOGIN', 'تسجيل خروج': 'LOGOUT'}
        params = {'date_from': self.dt_from.date().toString('yyyy-MM-dd'), 'date_to': self.dt_to.date().toString('yyyy-MM-dd')}
        action = action_map.get(self.cb_action.currentText())
        if action:
            params['action'] = action
        user = self.le_user.text().strip()
        if user:
            params['user'] = user
        entity = self.le_entity.text().strip()
        if entity:
            params['entity'] = entity
        try:
            ok, data = self.api_service._request('GET', '/api/audit-logs', params=params)
            if not ok:
                data = []
            logs = data if isinstance(data, list) else []
            self.tbl.setRowCount(len(logs))
            action_text = {'CREATE': 'إنشاء', 'UPDATE': 'تعديل', 'DELETE': 'حذف', 'APPROVE': 'اعتماد', 'REJECT': 'رفض', 'LOGIN': 'دخول', 'LOGOUT': 'خروج'}
            for r, log in enumerate(logs):
                self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
                self.tbl.setItem(r, 1, QTableWidgetItem(str(log.get('timestamp', '-'))))
                self.tbl.setItem(r, 2, QTableWidgetItem(log.get('user_name', log.get('user_id', '-'))))
                self.tbl.setItem(r, 3, QTableWidgetItem(action_text.get(log.get('action', ''), log.get('action', '-'))))
                self.tbl.setItem(r, 4, QTableWidgetItem(log.get('entity_name', log.get('table_name', '-'))))
                self.tbl.setItem(r, 5, QTableWidgetItem(str(log.get('record_id', '-'))))
                btn_details = QPushButton('👁️')
                btn_details.clicked.connect(lambda _, l=log: self._show_details(l))
                self.tbl.setCellWidget(r, 6, btn_details)
            self.lbl_summary.setText(f'عدد السجلات: {len(logs)}')
        except Exception as e:
            self.lbl_summary.setText(f'خطأ: {e}')
            print(f"Error loading audit logs: {e}")

    def _show_details(self, log):
        details = f"""المستخدم: {log.get('user_name', '-')}
العملية: {log.get('action', '-')}
الكيان: {log.get('entity_name', '-')}
رقم السجل: {log.get('record_id', '-')}
التاريخ: {log.get('timestamp', '-')}
IP: {log.get('ip_address', '-')}
التفاصيل:\n{log.get('details', '-')}"""
        QMessageBox.information(self, 'تفاصيل السجل', details)

    def _export(self):
        QMessageBox.information(self, 'تصدير', 'جاري تصدير السجلات إلى ملف Excel...')

    def _export_pdf(self):
        QMessageBox.information(self, 'تصدير', 'جاري تصدير السجلات إلى ملف PDF...')

    def load_data(self):
        self._load_logs()
        btn_bar.addWidget(btn_export)
        btn_export_pdf = QPushButton('📄 تصدير PDF')
        btn_export_pdf.clicked.connect(self._export_pdf)
        btn_bar.addWidget(btn_export_pdf)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(7)
        self.tbl.setHorizontalHeaderLabels(['#', 'التاريخ والوقت', 'المستخدم', 'نوع العملية', 'الكيان', 'رقم السجل', 'التفاصيل'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setShowGrid(True)
        layout.addWidget(self.tbl, 1)
        self.lbl_summary = QLabel()
        self.lbl_summary.setStyleSheet("background-color:#E8F5E9; padding:8px; border-radius:4px; font-weight:bold;")
        layout.addWidget(self.lbl_summary)