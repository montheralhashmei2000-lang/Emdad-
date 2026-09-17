"""إدارة اشتراكات المرافق - Facility Subscription View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDateEdit,
    QMessageBox, QTabWidget, QFormLayout, QGroupBox, QAbstractItemView, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService
from ui.theme import make_header_label


class FacilitySubscriptionView(QWidget):
    """إدارة اشتراكات المرافق - المطابخ والأفران."""

    def __init__(self, parent=None, api_service: ApiService | None = None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._units = []
        self._init_ui()
        self._load_metadata()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label('إدارة اشتراكات المرافق (المطابخ والأفران)'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._tab_list = QWidget()
        self._tab_form = QWidget()
        self.tabs.addTab(self._tab_list, 'قائمة الاشتراكات')
        self.tabs.addTab(self._tab_form, 'إضافة/تعديل اشتراك')
        self._build_list_tab()
        self._build_form_tab()

    def _build_list_tab(self):
        layout = QVBoxLayout(self._tab_list)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel('الوحدة:'))
        self.cb_filter_unit = QComboBox()
        self.cb_filter_unit.addItem('الكل', None)
        self.cb_filter_unit.currentIndexChanged.connect(self._load_list)
        toolbar.addWidget(self.cb_filter_unit)
        toolbar.addWidget(QLabel('النوع:'))
        self.cb_filter_type = QComboBox()
        self.cb_filter_type.addItems(['الكل', 'مطبخ', 'فرن', 'ثلاجة', 'مولّد', 'آلية'])
        self.cb_filter_type.currentIndexChanged.connect(self._load_list)
        toolbar.addWidget(self.cb_filter_type)
        btn_refresh = QPushButton('🔄 تحديث')
        btn_refresh.clicked.connect(self._load_list)
        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(8)
        self.tbl.setHorizontalHeaderLabels(['#', 'المرفق', 'النوع', 'الوحدة', 'السعة', 'الحالة', 'تاريخ الاشتراك', 'إجراءات'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl, 1)

    def _build_form_tab(self):
        layout = QVBoxLayout(self._tab_form)
        layout.setSpacing(12)
        card = QGroupBox('بيانات الاشتراك')
        form = QFormLayout(card)
        self.le_facility_name = QLineEdit()
        self.le_facility_name.setPlaceholderText('مثال: مطبخ رقم 1')
        self.cb_type = QComboBox()
        self.cb_type.addItems(['مطبخ', 'فرن', 'ثلاجة', 'مولّد', 'آلية', 'أخرى'])
        self.cb_unit = QComboBox()

    def _load_metadata(self):
        try:
            ok, units = self.api_service.get_units()
            if ok and units:
                self._units = units
                for u in units:
                    self.cb_unit.addItem(f"{u.get('code', '')} - {u.get('name', '')}", u.get('id'))
                    self.cb_filter_unit.addItem(u.get('name', ''), u.get('id'))
        except Exception as e:
            print(f"Error loading units: {e}")
        self._load_list()

    def _load_list(self):
        unit_id = self.cb_filter_unit.currentData()
        facility_type = self.cb_filter_type.currentText()
        params = {}
        if unit_id:
            params['unit_id'] = unit_id
        if facility_type != 'الكل':
            params['type'] = facility_type
        try:
            ok, data = self.api_service._request('GET', '/api/facility-subscriptions', params=params)
            if not ok:
                return
            self.tbl.setRowCount(len(data) if data else 0)
            for r, sub in enumerate(data or []):
                self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
                self.tbl.setItem(r, 1, QTableWidgetItem(sub.get('facility_name', '-')))
                self.tbl.setItem(r, 2, QTableWidgetItem(sub.get('facility_type', '-')))
                self.tbl.setItem(r, 3, QTableWidgetItem(next((u.get('name', '-') for u in self._units if u.get('id') == sub.get('unit_id')), '-')))
                self.tbl.setItem(r, 4, QTableWidgetItem(str(sub.get('capacity', '-'))))
                status_map = {'ACTIVE': 'نشط', 'INACTIVE': 'متوقف', 'MAINTENANCE': 'صيانة', 'CANCELLED': 'ملغي'}
                self.tbl.setItem(r, 5, QTableWidgetItem(status_map.get(sub.get('status', ''), sub.get('status', '-'))))
                self.tbl.setItem(r, 6, QTableWidgetItem(str(sub.get('start_date', '-'))))
                btn_edit = QPushButton('✏️')
                btn_edit.clicked.connect(lambda _, s=sub: self._edit(s))
                btn_del = QPushButton('🗑️')
                btn_del.clicked.connect(lambda _, s=sub: self._delete(s))
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(0, 0, 0, 0)
                action_layout.addWidget(btn_edit)
                action_layout.addWidget(btn_del)
                self.tbl.setCellWidget(r, 7, action_widget)
        except Exception as e:
            print(f"Error loading list: {e}")

    def _edit(self, sub):
        self._current_id = sub.get('id')
        self.le_facility_name.setText(sub.get('facility_name', ''))
        idx = self.cb_type.findText(sub.get('facility_type', ''))
        if idx >= 0:
            self.cb_type.setCurrentIndex(idx)
        unit_idx = self.cb_unit.findData(sub.get('unit_id'))
        if unit_idx >= 0:
            self.cb_unit.setCurrentIndex(unit_idx)
        self.le_capacity.setText(str(sub.get('capacity', '')))
        status_map = {'نشط': 'ACTIVE', 'متوقف': 'INACTIVE', 'صيانة': 'MAINTENANCE', 'ملغي': 'CANCELLED'}
        for k, v in status_map.items():
            if v == sub.get('status', ''):
                self.cb_status.setCurrentText(k)
                break
        self.dt_start.setDate(QDate.fromString(str(sub.get('start_date', '')), 'yyyy-MM-dd') if sub.get('start_date') else QDate.currentDate())
        self.dt_end.setDate(QDate.fromString(str(sub.get('end_date', '')), 'yyyy-MM-dd') if sub.get('end_date') else QDate.currentDate().addMonths(12))
        self.txt_notes.setText(sub.get('notes', ''))
        self.tabs.setCurrentWidget(self._tab_form)

    def _save(self):
        facility_name = self.le_facility_name.text().strip()
        unit_id = self.cb_unit.currentData()
        if not facility_name or not unit_id:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء تعبئة جميع الحقول الإلزامية.')
            return
        status_map = {'نشط': 'ACTIVE', 'متوقف': 'INACTIVE', 'صيانة': 'MAINTENANCE', 'ملغي': 'CANCELLED'}
        payload = {
            'facility_name': facility_name,
            'facility_type': self.cb_type.currentText(),
            'unit_id': unit_id,
            'capacity': self.le_capacity.text().strip(),
            'status': status_map.get(self.cb_status.currentText(), 'ACTIVE'),
            'start_date': self.dt_start.date().toString('yyyy-MM-dd'),
            'end_date': self.dt_end.date().toString('yyyy-MM-dd'),
            'notes': self.txt_notes.toPlainText().strip(),
        }
        method = 'PUT' if hasattr(self, '_current_id') else 'POST'
        url = f'/api/facility-subscriptions/{self._current_id}' if method == 'PUT' else '/api/facility-subscriptions'
        try:
            ok, data = self.api_service._request(method, url, json=payload)
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم حفظ الاشتراك بنجاح.')
                self._clear_form()
                self._load_list()
                self.tabs.setCurrentWidget(self._tab_list)
            else:
                QMessageBox.critical(self, 'خطأ', f'فشل الحفظ: {data}')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'حدث خطأ: {e}')

    def _delete(self, sub):
        reply = QMessageBox.question(self, 'تأكيد', f'هل أنت متأكد من حذف اشتراك "{sub.get("facility_name", "")}"؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                ok, _ = self.api_service._request('DELETE', f'/api/facility-subscriptions/{sub.get("id")}')
                if ok:
                    QMessageBox.information(self, 'نجاح', 'تم الحذف بنجاح.')
                    self._load_list()
                else:
                    QMessageBox.critical(self, 'خطأ', 'فشل الحذف.')
            except Exception as e:
                QMessageBox.critical(self, 'خطأ', f'حدث خطأ: {e}')

    def _clear_form(self):
        if hasattr(self, '_current_id'):
            delattr(self, '_current_id')
        self.le_facility_name.clear()
        self.le_capacity.clear()
        self.cb_unit.setCurrentIndex(0)
        self.cb_type.setCurrentIndex(0)
        self.cb_status.setCurrentIndex(0)
        self.dt_start.setDate(QDate.currentDate())
        self.dt_end.setDate(QDate.currentDate().addMonths(12))
        self.txt_notes.clear()

    def load_data(self):
        self._load_metadata()
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText('ملاحظات إضافية...')
        self.txt_notes.setMaximumHeight(80)
        layout.addWidget(QLabel('ملاحظات:'))
        layout.addWidget(self.txt_notes)
        action_bar = QHBoxLayout()
        btn_save = QPushButton('💾 حفظ')
        btn_save.setStyleSheet("background-color:#27AE60; color:white; font-weight:bold;")
        btn_save.clicked.connect(self._save)
        action_bar.addWidget(btn_save)
        btn_clear = QPushButton('🗑️ إلغاء')
        btn_clear.clicked.connect(self._clear_form)
        action_bar.addWidget(btn_clear)
        layout.addLayout(action_bar)