"""صرف البضاعة - Issue View."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDateEdit,
    QMessageBox, QTabWidget, QFormLayout, QGroupBox, QAbstractItemView, QDoubleSpinBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService
from ui.theme import make_header_label


class IssueView(QWidget):
    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._units, self._warehouses, self._items, self._stocks = [], [], [], []
        self._init_ui()
        self._load_metadata()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(make_header_label('صرف البضاعة'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._tab_list = QWidget()
        self._tab_form = QWidget()
        self.tabs.addTab(self._tab_form, 'إذن صرف جديد')
        self.tabs.addTab(self._tab_list, 'سجل المصروفات')
        self._build_form_tab()
        self._build_list_tab()

    def _build_form_tab(self):
        layout = QVBoxLayout(self._tab_form)
        header = QGroupBox('بيانات إذن الصرف')
        form = QFormLayout(header)
        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.le_ref = QLineEdit()
        self.le_ref.setPlaceholderText('اتركه فارغاً للتخصيص التلقائي')
        self.cb_warehouse = QComboBox()
        self.cb_warehouse.addItem('-- اختر المخزن --', None)
        self.cb_warehouse.currentIndexChanged.connect(self._on_warehouse_changed)
        self.cb_unit = QComboBox()
        self.cb_unit.addItem('-- اختر الوحدة --', None)
        self.cb_purpose = QComboBox()
        self.cb_purpose.addItems(['توزيع مؤن', 'احتياطي', 'طوارئ', 'صيانة', 'إنتاج', 'أخرى'])
        form.addRow('التاريخ:', self.dt_date)
        form.addRow('الرقم:', self.le_ref)
        form.addRow('المخزن:', self.cb_warehouse)
        form.addRow('الوحدة:', self.cb_unit)
        form.addRow('الغرض:', self.cb_purpose)
        layout.addWidget(header)
        items_box = QGroupBox('أصناف الصرف')
        items_lay = QVBoxLayout(items_box)
        toolbar = QHBoxLayout()
        btn_add = QPushButton('➕ إضافة صنف')
        btn_add.clicked.connect(self._add_row)
        toolbar.addWidget(btn_add)
        toolbar.addStretch()
        items_lay.addLayout(toolbar)
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(7)
        self.tbl.setHorizontalHeaderLabels(['#', 'الصنف', 'المتاح', 'الكمية', 'الوحدة', 'ملاحظات', 'حذف'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setAlternatingRowColors(True)
        items_lay.addWidget(self.tbl)
        self.lbl_total = QLabel('عدد الأصناف: 0')
        self.lbl_total.setStyleSheet('font-weight:bold; color:#C62828;')
        items_lay.addWidget(self.lbl_total)
        layout.addWidget(items_box)
        self.txt_notes = QTextEdit()
        self.txt_notes.setMaximumHeight(50)
        layout.addWidget(self.txt_notes)
        btn_save = QPushButton('💾 صرف')
        btn_save.setStyleSheet('background-color:#C62828; color:white; font-weight:bold; padding:8px;')
        btn_save.clicked.connect(self._save)
        layout.addWidget(btn_save)

    def _build_list_tab(self):
        layout = QVBoxLayout(self._tab_list)
        self.tbl_list = QTableWidget()
        self.tbl_list.setColumnCount(6)
        layout.addWidget(self.tbl_list, 1)

    def _load_metadata(self):
        try:
            ok, data = self.api.get_units(limit=1000)
            if ok and data:
                self._units = data
                for u in data:
                    self.cb_unit.addItem(f"{u.get('code', '')} - {u.get('name', '')}", u.get('id'))
        except Exception as e:
            print(f"Error: {e}")
        try:
            ok, data = self.api.get_items(limit=1000)
            if ok and data:
                self._items = data
        except Exception as e:
            print(f"Error: {e}")
        try:
            ok, data = self.api.get_warehouses(limit=1000)
            if ok and data:
                self._warehouses = data
                for w in data:
                    self.cb_warehouse.addItem(f"{w.get('code', '')} - {w.get('name', '')}", w.get('id'))
        except Exception as e:
            print(f"Error: {e}")
        self._load_list()

    def _on_warehouse_changed(self):
        wh_id = self.cb_warehouse.currentData()
        if not wh_id:
            return
        try:
            ok, data = self.api._request('GET', f'/api/inventory?warehouse_id={wh_id}')
            if ok and data:
                self._stocks = data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error: {e}")

    def _add_row(self):
        row = self.tbl.rowCount()
        self.tbl.insertRow(row)
        self.tbl.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        cb = QComboBox()
        cb.addItem('-- اختر --', None)
        self.lbl_total.setText(f"عدد الأصناف: {self.tbl.rowCount()}")

    def _on_item_changed(self, row):
        cb = self.tbl.cellWidget(row, 1)
        if not cb or not cb.currentData():
            return
        wh_id = self.cb_warehouse.currentData()
        available = 0
        if wh_id and self._stocks:
            stock = next((s for s in self._stocks if s.get('item_id') == cb.currentData()), None)
            if stock:
                available = stock.get('quantity', 0)
        lbl = self.tbl.cellWidget(row, 2)
        if lbl:
            lbl.setText(str(available))
        item = next((i for i in self._items if i.get('id') == cb.currentData()), None)
        if item and item.get('units'):
            base = next((u for u in item['units'] if u.get('is_base_unit')), item['units'][0])
            self.tbl.item(row, 4).setText(base.get('unit_name', '-'))

    def _save(self):
        if not self.cb_warehouse.currentData():
            QMessageBox.warning(self, 'تنبيه', 'اختر المخزن')
            return
        if not self.cb_unit.currentData():
            QMessageBox.warning(self, 'تنبيه', 'اختر الوحدة')
            return
        if self.tbl.rowCount() == 0:
            QMessageBox.warning(self, 'تنبيه', 'أضف أصناف')
            return
        items = []
        for r in range(self.tbl.rowCount()):
            cb = self.tbl.cellWidget(r, 1)
            sb_qty = self.tbl.cellWidget(r, 3)
            if cb and sb_qty and cb.currentData() and sb_qty.value() > 0:
                item = next((i for i in self._items if i.get('id') == cb.currentData()), None)
                unit_id = None
                if item and item.get('units'):
                    base = next((u for u in item['units'] if u.get('is_base_unit')), item['units'][0])
                    unit_id = base.get('id')
                items.append({'item_id': cb.currentData(), 'quantity': sb_qty.value(), 'unit_id': unit_id})
        if not items:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد أصناف صالحة')
            return
        payload = {'issue_date': self.dt_date.date().toString('yyyy-MM-dd'),
                   'ref_number': self.le_ref.text().strip(),
                   'warehouse_id': self.cb_warehouse.currentData(),
                   'beneficiary_unit_id': self.cb_unit.currentData(),
                   'purpose': self.cb_purpose.currentText(),
                   'notes': self.txt_notes.toPlainText().strip(),
                   'items': items}
        try:
            ok, _ = self.api.issue_stock_bulk(payload)
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم الصرف بنجاح')
                self.tbl.setRowCount(0)
                self.txt_notes.clear()
                self._load_list()
            else:
                QMessageBox.critical(self, 'خطأ', 'فشل الحفظ')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', str(e))

    def _load_list(self):
        try:
            ok, data = self.api.get_movements(limit=100)
            if not ok:
                data = []
            self.tbl_list.setRowCount(len(data))
            for r, mov in enumerate(data):
                self.tbl_list.setItem(r, 0, QTableWidgetItem(str(r + 1)))
                self.tbl_list.setItem(r, 1, QTableWidgetItem(str(mov.get('date', '-'))))
                self.tbl_list.setItem(r, 2, QTableWidgetItem(mov.get('ref_number', '-')))
                self.tbl_list.setItem(r, 3, QTableWidgetItem(str(mov.get('unit_id', '-'))))
                self.tbl_list.setItem(r, 4, QTableWidgetItem(mov.get('purpose', '-')))
                self.tbl_list.setItem(r, 5, QTableWidgetItem(str(len(mov.get('items', [])))))
        except Exception as e:
            print(f"Error: {e}")

    def load_data(self):
        self._load_metadata()
        self._load_list()
