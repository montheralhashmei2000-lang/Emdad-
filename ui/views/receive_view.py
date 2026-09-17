"""استلام البضاعة - Receive View."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDateEdit,
    QMessageBox, QTabWidget, QFormLayout, QGroupBox, QAbstractItemView, QDoubleSpinBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService
from ui.theme import make_header_label


class ReceiveView(QWidget):
    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._suppliers, self._warehouses, self._items = [], [], []
        self._init_ui()
        self._load_metadata()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label('استلام البضاعة (من الموردين)'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._tab_form = QWidget()
        self._tab_list = QWidget()
        self.tabs.addTab(self._tab_form, 'إنشاء إذن استلام')
        self.tabs.addTab(self._tab_list, 'سجل الإذونات')
        self._build_form_tab()
        self._build_list_tab()

    def _build_form_tab(self):
        layout = QVBoxLayout(self._tab_form)
        header = QGroupBox('بيانات إذن الاستلام')
        form = QFormLayout(header)
        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.le_ref = QLineEdit()
        self.le_ref.setPlaceholderText('اتركه فارغاً للتخصيص التلقائي')
        self.cb_supplier = QComboBox()
        self.cb_supplier.addItem('-- اختر المورد --', None)
        self.cb_warehouse = QComboBox()
        self.cb_warehouse.addItem('-- اختر المخزن --', None)
        self.cb_doctype = QComboBox()
        self.cb_doctype.addItems(['توريد عادي', 'توريد طوارئ', 'مرتجع وارد', 'تحويل وارد', 'افتتاحي'])
        form.addRow('التاريخ:', self.dt_date)
        form.addRow('الرقم:', self.le_ref)
        form.addRow('النوع:', self.cb_doctype)
        form.addRow('المورّد:', self.cb_supplier)
        form.addRow('المخزن:', self.cb_warehouse)
        layout.addWidget(header)
        items_box = QGroupBox('الأصناف')
        items_lay = QVBoxLayout(items_box)
        toolbar = QHBoxLayout()
        btn_add = QPushButton('➕ إضافة')
        btn_add.clicked.connect(self._add_row)
        toolbar.addWidget(btn_add)
        toolbar.addStretch()
        items_lay.addLayout(toolbar)
        self.tbl_items = QTableWidget()
        self.tbl_items.setColumnCount(7)
        self.tbl_items.setHorizontalHeaderLabels(['#', 'الصنف', 'الكمية', 'الوحدة', 'السعر', 'الإجمالي', 'حذف'])
        self.tbl_items.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_items.setAlternatingRowColors(True)
        items_lay.addWidget(self.tbl_items)
        self.lbl_total = QLabel('الإجمالي: 0.00')
        self.lbl_total.setStyleSheet('font-weight:bold; color:#1B5E20;')
        items_lay.addWidget(self.lbl_total)
        layout.addWidget(items_box)
        self.txt_notes = QTextEdit()
        self.txt_notes.setMaximumHeight(50)
        layout.addWidget(QLabel('ملاحظات:'))
        layout.addWidget(self.txt_notes)
        btn_save = QPushButton('💾 حفظ وإضافة للمخزون')
        btn_save.setStyleSheet('background-color:#27AE60; color:white; font-weight:bold; padding:8px;')
        btn_save.clicked.connect(self._save)
        layout.addWidget(btn_save)

    def _load_metadata(self):
        try:
            ok, data = self.api.get_suppliers()
            if ok and data:
                self._suppliers = data
                for s in data:
                    self.cb_supplier.addItem(f"{s.get('code', '')} - {s.get('name', '')}", s.get('id'))
        except Exception as e:
            print(f"Error: {e}")
        try:
            ok, data = self.api.get_warehouses()
            if ok and data:
                self._warehouses = data
                for w in data:
                    self.cb_warehouse.addItem(f"{w.get('code', '')} - {w.get('name', '')}", w.get('id'))
        except Exception as e:
            print(f"Error: {e}")
        try:
            ok, data = self.api.get_items()
            if ok and data:
                self._items = data
        except Exception as e:
            print(f"Error: {e}")
        self._load_list()

    def _add_row(self):
        row = self.tbl_items.rowCount()
        self.tbl_items.insertRow(row)
        self.tbl_items.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        cb = QComboBox()
        cb.addItem('-- اختر --', None)
        for itm in self._items:
            cb.addItem(f"{itm.get('item_code', '')} - {itm.get('name', '')}", itm.get('id'))
        cb.currentIndexChanged.connect(lambda _, r=row: self._on_item(r))
        self.tbl_items.setCellWidget(row, 1, cb)
        sb_qty = QDoubleSpinBox()
        sb_qty.setMaximum(999999)
        sb_qty.valueChanged.connect(lambda _, r=row: self._recalc(r))
        self.tbl_items.setCellWidget(row, 2, sb_qty)
        self.tbl_items.setItem(row, 3, QTableWidgetItem('-'))
        sb_price = QDoubleSpinBox()
        sb_price.setMaximum(999999)
        sb_price.valueChanged.connect(lambda _, r=row: self._recalc(r))
        self.tbl_items.setCellWidget(row, 4, sb_price)
        self.tbl_items.setItem(row, 5, QTableWidgetItem('0'))
        btn_del = QPushButton('🗑️')
        btn_del.clicked.connect(lambda _, r=row: self.tbl_items.removeRow(r))
        self.tbl_items.setCellWidget(row, 6, btn_del)

    def _on_item(self, row):
        cb = self.tbl_items.cellWidget(row, 1)
        if not cb or not cb.currentData():
            return
        item = next((i for i in self._items if i.get('id') == cb.currentData()), None)
        if item and item.get('units'):
            base = next((u for u in item['units'] if u.get('is_base_unit')), item['units'][0])
            self.tbl_items.item(row, 3).setText(base.get('unit_name', '-'))

    def _recalc(self, row):
        sb_qty = self.tbl_items.cellWidget(row, 2)
        sb_price = self.tbl_items.cellWidget(row, 4)
        if sb_qty and sb_price:
            self.tbl_items.item(row, 5).setText(f"{sb_qty.value() * sb_price.value():.2f}")
        total = sum(float(self.tbl_items.item(r, 5).text() or 0) for r in range(self.tbl_items.rowCount()))
        self.lbl_total.setText(f"الإجمالي: {total:.2f}")

    def _save(self):
        if not self.cb_supplier.currentData():
            QMessageBox.warning(self, 'تنبيه', 'اختر المورّد')
            return
        if not self.cb_warehouse.currentData():
            QMessageBox.warning(self, 'تنبيه', 'اختر المخزن')
            return
        if self.tbl_items.rowCount() == 0:
            QMessageBox.warning(self, 'تنبيه', 'أضف أصناف')
            return
        items = []
        for r in range(self.tbl_items.rowCount()):
            cb = self.tbl_items.cellWidget(r, 1)
            sb_qty = self.tbl_items.cellWidget(r, 2)
            sb_price = self.tbl_items.cellWidget(r, 4)
            if cb and sb_qty and sb_price and cb.currentData() and sb_qty.value() > 0:
                item = next((i for i in self._items if i.get('id') == cb.currentData()), None)
                unit_id = None
                if item and item.get('units'):
                    base = next((u for u in item['units'] if u.get('is_base_unit')), item['units'][0])
                    unit_id = base.get('id')
                items.append({'item_id': cb.currentData(), 'quantity': sb_qty.value(),
                            'unit_id': unit_id, 'unit_price': sb_price.value()})
        if not items:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد أصناف صالحة')
            return
        payload = {'receive_date': self.dt_date.date().toString('yyyy-MM-dd'),
                   'ref_number': self.le_ref.text().strip(),
                   'document_type': self.cb_doctype.currentText(),
                   'supplier_id': self.cb_supplier.currentData(),
                   'warehouse_id': self.cb_warehouse.currentData(),
                   'status': 'APPROVED',
                   'notes': self.txt_notes.toPlainText().strip(),
                   'items': items}
        try:
            ok, _ = self.api.receive_stock_bulk(payload)
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم الحفظ بنجاح')
                self.tbl_items.setRowCount(0)
                self.txt_notes.clear()
                self._load_list()
            else:
                QMessageBox.critical(self, 'خطأ', 'فشل الحفظ')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', str(e))

    def _load_list(self):
        try:
            ok, data = self.api.get_movements_filtered(movement_type='RECEIVE')
            if not ok:
                data = []
            self.tbl_list.setRowCount(len(data))
            for r, mov in enumerate(data):
                self.tbl_list.setItem(r, 0, QTableWidgetItem(str(r + 1)))
                self.tbl_list.setItem(r, 1, QTableWidgetItem(str(mov.get('date', '-'))))
                self.tbl_list.setItem(r, 2, QTableWidgetItem(mov.get('ref_number', '-')))
                self.tbl_list.setItem(r, 3, QTableWidgetItem(str(mov.get('supplier_id', '-'))))
                self.tbl_list.setItem(r, 4, QTableWidgetItem(str(mov.get('warehouse_id', '-'))))
                self.tbl_list.setItem(r, 5, QTableWidgetItem(str(len(mov.get('items', [])))))
        except Exception as e:
            print(f"Error: {e}")

    def load_data(self):
        self._load_metadata()
        self._load_list()

    def _build_list_tab(self):
        layout = QVBoxLayout(self._tab_list)
        self.tbl_list = QTableWidget()
        self.tbl_list.setColumnCount(6)
        self.tbl_list.setHorizontalHeaderLabels(['#', 'التاريخ', 'الرقم', 'المورّد', 'المخزن', 'الأصناف'])
        self.tbl_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_list.setAlternatingRowColors(True)
        layout.addWidget(self.tbl_list, 1)