"""المرتجعات - Returns View."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDateEdit,
    QMessageBox, QTabWidget, QFormLayout, QGroupBox, QAbstractItemView, QDoubleSpinBox, QTextEdit)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService
from ui.theme import make_header_label


class ReturnsView(QWidget):
    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._warehouses, self._suppliers, self._items, self._units = [], [], [], []
        self._init_ui()
        self._load_metadata()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label('المرتجعات'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._tab_in = QWidget()
        self._tab_out = QWidget()
        self._tab_list = QWidget()
        self.tabs.addTab(self._tab_in, 'مرتجع وارد')
        self.tabs.addTab(self._tab_out, 'مرتجع صادر')
        self.tabs.addTab(self._tab_list, 'سجل المرتجعات')
        self._build_in_tab()
        self._build_out_tab()
        self._build_list_tab()

    def _build_in_tab(self):
        layout = QVBoxLayout(self._tab_in)
        card = QGroupBox('بيانات المرتجع الوارد (من وحدة إلى المخزن)')
        form = QFormLayout(card)
        self.dt_in = QDateEdit()
        self.dt_in.setCalendarPopup(True)
        self.dt_in.setDate(QDate.currentDate())
        self.le_ref_in = QLineEdit()
        self.le_ref_in.setPlaceholderText('الرقم المرجعي')
        self.cb_unit_in = QComboBox()
        self.cb_unit_in.addItem('-- اختر الوحدة --', None)
        self.cb_wh_in = QComboBox()
        self.cb_wh_in.addItem('-- اختر المخزن --', None)
        self.cb_reason_in = QComboBox()
        self.cb_reason_in.addItems(['لم يتم استخدامه', 'تالف', 'منتهي الصلاحية', 'خطأ في التوريد', 'زيادة', 'أخرى'])
        form.addRow('التاريخ:', self.dt_in)
        form.addRow('الرقم:', self.le_ref_in)
        form.addRow('الوحدة:', self.cb_unit_in)
        form.addRow('المخزن:', self.cb_wh_in)
        form.addRow('السبب:', self.cb_reason_in)
        layout.addWidget(card)
        self.tbl_in = self._make_items_table()
        layout.addWidget(self.tbl_in)
        btn_add = QPushButton('➕ إضافة صنف')
        btn_add.clicked.connect(lambda: self._add_table_row(self.tbl_in))
        layout.addWidget(btn_add)
        self.txt_in = QTextEdit()
        self.txt_in.setMaximumHeight(50)
        layout.addWidget(QLabel('ملاحظات:'))
        layout.addWidget(self.txt_in)
        btn_save = QPushButton('💾 حفظ المرتجع الوارد')
        btn_save.setStyleSheet('background-color:#27AE60; color:white; font-weight:bold; padding:8px;')
        btn_save.clicked.connect(lambda: self._save('in'))
        layout.addWidget(btn_save)

    def _build_out_tab(self):
        layout = QVBoxLayout(self._tab_out)
        card = QGroupBox('بيانات المرتجع الصادر (من المخزن إلى المورّد)')
        form = QFormLayout(card)
        self.dt_out = QDateEdit()
        self.dt_out.setCalendarPopup(True)
        self.dt_out.setDate(QDate.currentDate())
        self.le_ref_out = QLineEdit()
        self.le_ref_out.setPlaceholderText('الرقم المرجعي')
        self.cb_wh_out = QComboBox()
        self.cb_wh_out.addItem('-- اختر المخزن --', None)
        self.cb_sup_out = QComboBox()
        self.cb_sup_out.addItem('-- اختر المورّد --', None)
        self.cb_reason_out = QComboBox()
        self.cb_reason_out.addItems(['تالف', 'منتهي الصلاحية', 'لا يطابق المواصفات', 'خطأ في الاستلام', 'زيادة', 'أخرى'])
        form.addRow('التاريخ:', self.dt_out)
        form.addRow('الرقم:', self.le_ref_out)
        form.addRow('المخزن:', self.cb_wh_out)
        form.addRow('المورّد:', self.cb_sup_out)
        form.addRow('السبب:', self.cb_reason_out)
        layout.addWidget(card)
        self.tbl_out = self._make_items_table()
        layout.addWidget(self.tbl_out)
        btn_add = QPushButton('➕ إضافة صنف')
        self.txt_out = QTextEdit()
        self.txt_out.setMaximumHeight(50)
        layout.addWidget(QLabel("ملاحظات:"))
        layout.addWidget(self.txt_out)
        btn_save = QPushButton("💾 حفظ المرتجع الصادر")
        btn_save.setStyleSheet("background-color:#C62828; color:white; font-weight:bold; padding:8px;")
        btn_save.clicked.connect(lambda: self._save("out"))
        layout.addWidget(btn_save)
    def _build_list_tab(self):
        layout = QVBoxLayout(self._tab_list)
        self.tbl_list = QTableWidget()
        self.tbl_list.setColumnCount(7)
        self.tbl_list.setHorizontalHeaderLabels(['#', 'التاريخ', 'النوع', 'الرقم', 'الجهة', 'الأصناف', 'ملاحظات'])
        self.tbl_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_list.setAlternatingRowColors(True)
        layout.addWidget(self.tbl_list, 1)

    def _make_items_table(self):
        tbl = QTableWidget()
        tbl.setColumnCount(6)
        tbl.setHorizontalHeaderLabels(['#', 'الصنف', 'الكمية', 'الوحدة', 'ملاحظات', 'حذف'])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.setAlternatingRowColors(True)
        return tbl

    def _add_table_row(self, tbl):
        row = tbl.rowCount()
        tbl.insertRow(row)
        tbl.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        cb = QComboBox()
        cb.addItem('-- اختر --', None)
        for itm in self._items:
            cb.addItem(f"{itm.get('item_code', '')} - {itm.get('name', '')}", itm.get('id'))
        tbl.setCellWidget(row, 1, cb)
        sb = QDoubleSpinBox()
        sb.setMaximum(999999)
        tbl.setCellWidget(row, 2, sb)
        tbl.setItem(row, 3, QTableWidgetItem('-'))
        le = QLineEdit()
        le.setPlaceholderText('ملاحظات')
        tbl.setCellWidget(row, 5, btn)

    def _load_metadata(self):
        try:
            ok, data = self.api.get_units(limit=1000)
            if ok and data:
                self._units = data
                for u in data:
                    self.cb_unit_in.addItem(f"{u.get('code', '')} - {u.get('name', '')}", u.get('id'))
        except Exception as e:
            print(f"Error: {e}")
        try:
            ok, data = self.api.get_warehouses(limit=1000)
            if ok and data:
                self._warehouses = data
                for w in data:
                    wh_item = f"{w.get('code', '')} - {w.get('name', '')}"
                    self.cb_wh_in.addItem(wh_item, w.get('id'))
                    self.cb_wh_out.addItem(wh_item, w.get('id'))
        except Exception as e:
            print(f"Error: {e}")
        try:
            ok, data = self.api.get_suppliers()
            if ok and data:
                self._suppliers = data
                for s in data:
                    self.cb_sup_out.addItem(f"{s.get('code', '')} - {s.get('name', '')}", s.get('id'))
        except Exception as e:
            print(f"Error: {e}")
        try:
            ok, data = self.api.get_items(limit=1000)
            if ok and data:
                self._items = data
        except Exception as e:
            print(f"Error: {e}")
        self._load_list()

    def _save_in(self):
        if not self.cb_unit_in.currentData():
            QMessageBox.warning(self, 'تنبيه', 'اختر الوحدة')
            return
        if not self.cb_wh_in.currentData():
            QMessageBox.warning(self, 'تنبيه', 'اختر المخزن')
            return
        items = self._collect_table_items(self.tbl_in)
        if not items:
            QMessageBox.warning(self, 'تنبيه', 'أضف أصناف')
            return
        payload = {'return_date': self.dt_in.date().toString('yyyy-MM-dd'),
                   'ref_number': self.le_ref_in.text().strip(),
                   'return_type': 'INBOUND',
                   'source_unit_id': self.cb_unit_in.currentData(),
                   'warehouse_id': self.cb_wh_in.currentData(),
                   'reason': self.cb_reason_in.currentText(),
                   'notes': self.txt_in.toPlainText().strip(),
                   'items': items}
        try:
            ok, _ = self.api._request('POST', '/api/stock/returns', json=payload)
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم الحفظ')
                self.tbl_in.setRowCount(0)
                self.txt_in.clear()
                self._load_list()
            else:
                QMessageBox.critical(self, 'خطأ', 'فشل الحفظ')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', str(e))

    def _save_out(self):
        if not self.cb_wh_out.currentData():
            QMessageBox.warning(self, 'تنبيه', 'اختر المخزن')
            return
        if not self.cb_sup_out.currentData():
            QMessageBox.warning(self, 'تنبيه', 'اختر المورّد')
            return
        items = self._collect_table_items(self.tbl_out)
        if not items:
            QMessageBox.warning(self, 'تنبيه', 'أضف أصناف')
            return
        payload = {'return_date': self.dt_out.date().toString('yyyy-MM-dd'),
                   'ref_number': self.le_ref_out.text().strip(),
                   'return_type': 'OUTBOUND',
                   'warehouse_id': self.cb_wh_out.currentData(),
                   'supplier_id': self.cb_sup_out.currentData(),
                   'reason': self.cb_reason_out.currentText(),
                   'notes': self.txt_out.toPlainText().strip(),
                   'items': items}
        try:
            ok, _ = self.api._request('POST', '/api/stock/returns', json=payload)
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم الحفظ')
                self.tbl_out.setRowCount(0)
                self.txt_out.clear()
                self._load_list()
            else:
                QMessageBox.critical(self, 'خطأ', 'فشل الحفظ')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', str(e))

    def _collect_table_items(self, tbl):
        items = []
        for r in range(tbl.rowCount()):
            cb = tbl.cellWidget(r, 1)
            sb = tbl.cellWidget(r, 2)
            if cb and sb and cb.currentData() and sb.value() > 0:
                items.append({'item_id': cb.currentData(), 'quantity': sb.value(),
                             'notes': tbl.cellWidget(r, 4).text().strip() if tbl.cellWidget(r, 4) else ''})
        return items

    def _load_list(self):
        try:
            ok, data = self.api._request('GET', '/api/stock/returns', params={'limit': 100})
            if not ok:
                data = []
            self.tbl_list.setRowCount(len(data))
            for r, ret in enumerate(data):
                ret_type = 'وارد' if ret.get('return_type') == 'INBOUND' else 'صادر'
                self.tbl_list.setItem(r, 0, QTableWidgetItem(str(r + 1)))
                self.tbl_list.setItem(r, 1, QTableWidgetItem(str(ret.get('return_date', '-'))))
                self.tbl_list.setItem(r, 2, QTableWidgetItem(ret_type))
                self.tbl_list.setItem(r, 3, QTableWidgetItem(ret.get('ref_number', '-')))
                self.tbl_list.setItem(r, 4, QTableWidgetItem(str(ret.get('source_unit_id') or ret.get('supplier_id', '-'))))
                self.tbl_list.setItem(r, 5, QTableWidgetItem(str(len(ret.get('items', [])))))
                self.tbl_list.setItem(r, 6, QTableWidgetItem(ret.get('notes', '-')))
        except Exception as e:
            print(f"Error: {e}")

    def load_data(self):
        self._load_metadata()
        self._load_list()
