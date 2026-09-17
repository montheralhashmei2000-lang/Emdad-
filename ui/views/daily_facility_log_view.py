"""سجل المرافق اليومي - Daily Facility Log View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDateEdit,
    QMessageBox, QTabWidget, QFormLayout, QGroupBox, QAbstractItemView, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService
from ui.theme import make_header_label


class DailyFacilityLogView(QWidget):
    """سجل العمليات اليومية للمرافق - المطابخ والأفران."""

    def __init__(self, parent=None, api_service: ApiService | None = None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._units = []
        self._facilities = []
        self._init_ui()
        self._load_metadata()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label('سجل المرافق اليومي (عمليات المطبخ والأفران)'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._tab_form = QWidget()
        self._tab_list = QWidget()
        self.tabs.addTab(self._tab_form, 'تسجيل عملية جديدة')
        self.tabs.addTab(self._tab_list, 'سجل العمليات')
        self._build_form_tab()
        self._build_list_tab()

    def _build_form_tab(self):
        layout = QVBoxLayout(self._tab_form)
        layout.setSpacing(12)
        card = QGroupBox('بيانات العملية')
        form = QFormLayout(card)
        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.cb_unit = QComboBox()
        self.cb_unit.addItem('-- اختر الوحدة --', None)
        self.cb_unit.currentIndexChanged.connect(self._on_unit_changed)
        self.cb_facility = QComboBox()
        self.cb_facility.addItem('-- اختر المرفق --', None)
        self.cb_operation = QComboBox()
        self.cb_operation.addItems(['تشغيل', 'إيقاف', 'صيانة', 'فحص', 'استهلاك وقود', 'استهلاك كهرباء', 'تنظيف', 'إصلاح', 'أخرى'])
        self.le_reading_before = QDoubleSpinBox()
        self.le_reading_before.setMaximum(9999999)
        self.le_reading_before.setDecimals(2)
        self.le_reading_after = QDoubleSpinBox()
        self.le_reading_after.setMaximum(9999999)
        self.le_reading_after.setDecimals(2)
        self.le_quantity = QDoubleSpinBox()
        self.le_quantity.setMaximum(9999999)
        self.le_quantity.setDecimals(3)
        form.addRow('تاريخ العملية:', self.dt_date)
        form.addRow('الوحدة:', self.cb_unit)
        form.addRow('المرفق:', self.cb_facility)
        form.addRow('نوع العملية:', self.cb_operation)
        form.addRow('القراءة قبل:', self.le_reading_before)
        form.addRow('القراءة بعد:', self.le_reading_after)
        form.addRow('الكمية المستهلكة:', self.le_quantity)
        layout.addWidget(card)
        self.le_notes = QLineEdit()
        self.le_notes.setPlaceholderText('ملاحظات إضافية...')
        layout.addWidget(QLabel('ملاحظات:'))
        layout.addWidget(self.le_notes)
        action_bar = QHBoxLayout()
        btn_save = QPushButton('💾 حفظ')
        btn_save.setStyleSheet("background-color:#27AE60; color:white; font-weight:bold;")
        btn_save.clicked.connect(self._save)
        action_bar.addWidget(btn_save)
        btn_clear = QPushButton('🗑️ تفريغ')
        btn_clear.clicked.connect(self._clear_form)
        action_bar.addWidget(btn_clear)
        layout.addLayout(action_bar)

    def _build_list_tab(self):
        layout = QVBoxLayout(self._tab_list)
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel('الوحدة:'))
        self.cb_filter_unit = QComboBox()
        self.cb_filter_unit.addItem('الكل', None)
        self.cb_filter_unit.currentIndexChanged.connect(self._load_list)
        toolbar.addWidget(self.cb_filter_unit)
        toolbar.addWidget(QLabel('من:'))
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-30))
        toolbar.addWidget(self.dt_from)
        toolbar.addWidget(QLabel('إلى:'))
        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        toolbar.addWidget(self.dt_to)
        btn_refresh = QPushButton('🔄')
        btn_refresh.clicked.connect(self._load_list)
        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(8)
        self.tbl.setHorizontalHeaderLabels(['#', 'التاريخ', 'المرفق', 'العملية', 'القراءة قبل', 'القراءة بعد', 'الكمية', 'إجراءات'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl, 1)

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
        self._load_facilities()
        self._load_list()
        self._load_list()

    def _load_facilities(self):
        self._facilities = []
        self.cb_facility.clear()
        self.cb_facility.addItem('-- اختر المرفق --', None)
        try:
            ok, data = self.api_service._request('GET', '/api/facility-subscriptions?status=ACTIVE')
            if ok and data:
                self._facilities = data
                for f in data:
                    self.cb_facility.addItem(f.get('facility_name', '-'), f.get('id'))
        except Exception as e:
            print(f"Error loading facilities: {e}")

    def _on_unit_changed(self):
        self._load_facilities()

    def _load_list(self):
        unit_id = self.cb_filter_unit.currentData()
        date_from = self.dt_from.date().toString('yyyy-MM-dd')
        date_to = self.dt_to.date().toString('yyyy-MM-dd')
        params = {'date_from': date_from, 'date_to': date_to}
        if unit_id:
            params['unit_id'] = unit_id
        try:
            ok, data = self.api_service._request('GET', '/api/daily-facility-logs', params=params)
            if not ok:
                return
            self.tbl.setRowCount(len(data) if data else 0)
            for r, log in enumerate(data or []):
                self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
                self.tbl.setItem(r, 1, QTableWidgetItem(str(log.get('log_date', '-'))))
                self.tbl.setItem(r, 2, QTableWidgetItem(log.get('facility_name', '-')))
                self.tbl.setItem(r, 3, QTableWidgetItem(log.get('operation_type', '-')))
                self.tbl.setItem(r, 4, QTableWidgetItem(str(log.get('reading_before', '-'))))
                self.tbl.setItem(r, 5, QTableWidgetItem(str(log.get('reading_after', '-'))))
                self.tbl.setItem(r, 6, QTableWidgetItem(str(log.get('quantity', '-'))))
                btn_del = QPushButton('🗑️')
                btn_del.clicked.connect(lambda _, l=log: self._delete(l))
                self.tbl.setCellWidget(r, 7, btn_del)
        except Exception as e:
            print(f"Error loading list: {e}")

    def _save(self):
        facility_id = self.cb_facility.currentData()
        if not facility_id:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء اختيار المرفق.')
            return
        payload = {
            'log_date': self.dt_date.date().toString('yyyy-MM-dd'),
            'facility_subscription_id': facility_id,
            'operation_type': self.cb_operation.currentText(),
            'reading_before': self.le_reading_before.value(),
            'reading_after': self.le_reading_after.value(),
            'quantity': self.le_quantity.value(),
            'notes': self.le_notes.text().strip(),
        }
        try:
            ok, data = self.api_service._request('POST', '/api/daily-facility-logs', json=payload)
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم حفظ السجل بنجاح.')
                self._clear_form()
                self._load_list()
            else:
                QMessageBox.critical(self, 'خطأ', f'فشل الحفظ: {data}')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'حدث خطأ: {e}')

    def _delete(self, log):
        reply = QMessageBox.question(self, 'تأكيد', 'هل تريد حذف هذا السجل؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                ok, _ = self.api_service._request('DELETE', f'/api/daily-facility-logs/{log.get("id")}')
                if ok:
                    QMessageBox.information(self, 'نجاح', 'تم الحذف.')
                    self._load_list()
            except Exception:
                QMessageBox.critical(self, 'خطأ', 'فشل الحذف.')

    def _clear_form(self):
        self.le_reading_before.setValue(0)
        self.le_reading_after.setValue(0)
        self.le_quantity.setValue(0)
        self.le_notes.clear()
        self.cb_facility.setCurrentIndex(0)
        self.cb_operation.setCurrentIndex(0)

    def load_data(self):
        self._load_metadata()
        form.addRow('المرفق:', self.cb_facility)
        form.addRow('نوع العملية:', self.cb_operation)
        form.addRow('القراءة قبل:', self.le_reading_before)
        form.addRow('القراءة بعد:', self.le_reading_after)
        form.addRow('الكمية المستهلكة:', self.le_quantity)
        layout.addWidget(card)
        self.le_notes = QLineEdit()
        self.le_notes.setPlaceholderText('ملاحظات إضافية...')
        layout.addWidget(QLabel('ملاحظات:'))
        layout.addWidget(self.le_notes)
        action_bar = QHBoxLayout()
        btn_save = QPushButton('💾 حفظ')
        btn_save.setStyleSheet("background-color:#27AE60; color:white; font-weight:bold;")
        btn_save.clicked.connect(self._save)
        action_bar.addWidget(btn_save)
        btn_clear = QPushButton('🗑️ تفريغ')
        btn_clear.clicked.connect(self._clear_form)
        action_bar.addWidget(btn_clear)
        layout.addLayout(action_bar)