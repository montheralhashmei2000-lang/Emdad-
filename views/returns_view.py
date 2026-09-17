"""Returns View - ادارة المرتجعات."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit,
    QLineEdit, QTextEdit, QPushButton, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QDate
from api_service import ApiService
from theme import make_header_label, COLORS


class ReturnsView(QWidget):
    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api_service = api_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._warehouses = []
        self._items = []
        self._stock_balance = []
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.addWidget(make_header_label('ادارة المرتجعات'))
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_new_tab(), 'سند مرتجع جديد')
        self.tabs.addTab(self._build_history_tab(), 'سجل المرتجعات')
        self.tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self.tabs)

    def _build_new_tab(self):
        tab = QWidget()
        ly = QVBoxLayout(tab)
        ly.setContentsMargins(10, 10, 10, 10)
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet('background-color: #F5F5E8; border: 1px solid #C7B299;')
        grid = QGridLayout(card)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setHorizontalSpacing(10)
        grid.addWidget(QLabel('المستودع:'), 0, 0)
        self.cb_wh = QComboBox()
        self.cb_wh.setMinimumWidth(280)
        self.cb_wh.currentIndexChanged.connect(self._on_wh_changed)
        grid.addWidget(self.cb_wh, 0, 1)
        grid.addWidget(QLabel('التاريخ:'), 0, 2)
        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        grid.addWidget(self.dt_date, 0, 3)
        grid.addWidget(QLabel('نوع المرتجع:'), 1, 0)
        self.cb_type = QComboBox()
        self.cb_type.addItems(['من الوحدة', 'للمورد'])
        grid.addWidget(self.cb_type, 1, 1)
        grid.addWidget(QLabel('المرجع:'), 1, 2)
        self.le_ref = QLineEdit()
        grid.addWidget(self.le_ref, 1, 3)
        ly.addWidget(card)
        ly.addWidget(QLabel('الاصناف:'))
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(('الكود', 'الاسم', 'الوحدة', 'المتاح', 'الكمية', 'اجراء'))
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.itemChanged.connect(self._on_cell_changed)
        ly.addWidget(self.table)
        hb = QHBoxLayout()
        badd = QPushButton('اضافة سطر')
        badd.clicked.connect(lambda: self._add_row())
        badd.setStyleSheet('background-color: #2E7D32; color: white; padding: 6px 14px;')
        hb.addWidget(badd)
        hb.addStretch()
        bsave = QPushButton('حفظ')
        bsave.clicked.connect(self._save)
        bsave.setStyleSheet('background-color: #1B6B3A; color: white; padding: 8px 18px; font-weight: bold;')
        hb.addWidget(bsave)
        breset = QPushButton('تفريغ')
        breset.clicked.connect(self._reset)
        breset.setStyleSheet('background-color: ' + COLORS['gold'] + '; color: black; padding: 8px 18px;')
        hb.addWidget(breset)
        ly.addLayout(hb)
        ly.addWidget(QLabel('ملاحظات:'))
        self.te_notes = QTextEdit()
        self.te_notes.setMaximumHeight(60)
        ly.addWidget(self.te_notes)
        hint = QLabel('ادخل كود الصنف - سيملا الاسم والوحدة تلقائيا.')
        hint.setStyleSheet('color: #888C7A; font-size: 11px;')
        ly.addWidget(hint)
        return tab

    def _build_history_tab(self):
        tab = QWidget()
        ly = QVBoxLayout(tab)
        ly.setContentsMargins(10, 10, 10, 10)
        hb = QHBoxLayout()
        hb.addWidget(QLabel('النوع:'))
        self.cb_hist_type = QComboBox()
        self.cb_hist_type.addItems(['الكل', 'BENEFICIARY', 'SUPPLIER'])
        self.cb_hist_type.currentIndexChanged.connect(self._load_history)
        hb.addWidget(self.cb_hist_type)
        bshow = QPushButton('عرض')
        bshow.clicked.connect(self._load_history)
        hb.addWidget(bshow)
        hb.addStretch()
        ly.addLayout(hb)
        self.tbl_hist = QTableWidget()
        self.tbl_hist.setColumnCount(7)
        self.tbl_hist.setHorizontalHeaderLabels(
            ('التاريخ', 'النوع', 'المستودع', 'الكود', 'الصنف', 'الكمية', 'الحالة'))
        self.tbl_hist.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tbl_hist.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        ly.addWidget(self.tbl_hist)
        return tab

    def load_data(self):
        if not self.api_service:
            return
        ok, wh = self.api_service.get_warehouses(500)
        if ok:
            self._warehouses = wh or []
            self.cb_wh.blockSignals(True)
            self.cb_wh.clear()
            for w in self._warehouses:
                self.cb_wh.addItem(w.get('code', '') + ' - ' + w.get('name', ''), w.get('id'))
            self.cb_wh.blockSignals(False)
        ok2, items = self.api_service.get_items(500)
        if ok2:
            self._items = items or []
        if self.cb_wh.currentIndex() >= 0:
            self._refresh_balance()

    def _on_tab_changed(self, idx):
        if idx == 1:
            self._load_history()

    def _on_wh_changed(self, _):
        self._refresh_balance()

    def _refresh_balance(self):
        wid = self.cb_wh.currentData()
        if not wid:
            return
        ok, bal = self.api_service.get_stock_balance(wid)
        self._stock_balance = bal if ok else []
        for r in range(self.table.rowCount()):
            code = (self.table.item(r, 0) or QTableWidgetItem()).text().strip()
            avail = self._avail(code)
            it = self.table.item(r, 3)
            if it is None:
                it = QTableWidgetItem('0')
                self.table.setItem(r, 3, it)
            it.setText(str(avail))

    def _avail(self, code):
        if not code:
            return 0
        for row in (self._stock_balance or []):
            if str(row.get('item_code', row.get('code', ''))) == code:
                try:
                    return float(row.get('quantity', 0) or 0)
                except (TypeError, ValueError):
                    return 0
        return 0
        return None

    def _add_row(self, code=''):
        r = self.table.rowCount()
        self.table.insertRow(r)
        code_it = QTableWidgetItem(code)
        code_it.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable)
        self.table.setItem(r, 0, code_it)
        for col in range(1, 5):
            fl = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            if col == 4:
                fl = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable
            it = QTableWidgetItem('0' if col != 1 else '')
            it.setFlags(fl)
            if col in (3, 4):
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, col, it)
        del_btn = QPushButton('X')
        del_btn.setFixedWidth(40)
        del_btn.clicked.connect(lambda _, row=r: self.table.removeRow(row))
        cell = QWidget()
        ll = QHBoxLayout(cell)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(del_btn)
        self.table.setCellWidget(r, 5, cell)
        if code:
            self._fill_row(r, code)

    def _on_cell_changed(self, item):
        if item.column() == 0:
            self._fill_row(item.row(), item.text().strip())

    def _fill_row(self, row, code):
        it = self._find_item(code)
        if it:
            for col, key in [(1, 'name'), (2, 'unit')]:
                ci = self.table.item(row, col)
                if ci:
                    ci.setText(it.get(key, ''))
        avail = self._avail(code)
        ai = self.table.item(row, 3)
        if ai:
            ai.setText(str(avail))

    def _reset(self):
        self.le_ref.clear()
        self.te_notes.clear()
        self.dt_date.setDate(QDate.currentDate())
        self.table.setRowCount(0)

    def _collect_lines(self):
        lines = []
        for r in range(self.table.rowCount()):
            code = (self.table.item(r, 0) or QTableWidgetItem()).text().strip()
            if not code:
                continue
            try:
                qty = float((self.table.item(r, 4) or QTableWidgetItem()).text() or 0)
            except ValueError:
                return None, 'الكمية في السطر ' + str(r+1) + ' غير صحيحة.'
            if qty <= 0:
                return None, 'الكمية في السطر ' + str(r+1) + ' يجب ان تكون اكبر من صفر.'
            avail = self._avail(code)
            if qty > avail:
                nm = (self.table.item(r, 1) or QTableWidgetItem()).text()
                return None, 'الكمية (' + str(qty) + ') من ' + nm + ' اكبر من المتاح (' + str(avail) + ').'
            lines.append({'item_code': code, 'quantity': qty})
        if not lines:
            return None, 'اضف صنفا واحدا على الاقل.'
        return lines, None

    def _save(self):
        wid = self.cb_wh.currentData()
        if not wid:
            QMessageBox.warning(self, 'بيانات ناقصة', 'اختر المستودع.')
            return
        lines, err = self._collect_lines()
        if err:
            QMessageBox.warning(self, 'خطا', err)
            return
        rtype = 'BENEFICIARY' if self.cb_type.currentIndex() == 0 else 'SUPPLIER'
        payload = {
            'warehouse_id': wid,
            'return_type': rtype,
            'reference': self.le_ref.text().strip(),
            'notes': self.te_notes.toPlainText().strip(),
            'movement_date': self.dt_date.date().toString('yyyy-MM-dd'),
            'lines': lines,
        }
        try:
            ok, resp = self.api_service.create_bulk_return(payload)
        except AttributeError:
            ok, resp = False, 'API method غير متوفر'
        if ok:
            QMessageBox.information(self, 'نجاح', 'تم حفظ المرتجع بنجاح.')
            self._reset()
        else:
            QMessageBox.critical(self, 'فشل', str(resp))

    def _load_history(self):
        if not self.api_service:
            return
        idx = self.cb_hist_type.currentIndex()
        rtype = '' if idx == 0 else self.cb_hist_type.currentText()
        try:
            ok, rows = self.api_service.get_returns(rtype, 500)
        except TypeError:
            ok, rows = False, 'API call failed'
        self.tbl_hist.setRowCount(0)
        if not ok:
            return
        for i, m in enumerate(rows or []):
            self.tbl_hist.insertRow(i)
            self.tbl_hist.setItem(i, 0, QTableWidgetItem(str(m.get('movement_date', m.get('created_at', '')))))
            self.tbl_hist.setItem(i, 1, QTableWidgetItem(str(m.get('return_type', ''))))
            self.tbl_hist.setItem(i, 2, QTableWidgetItem(str(m.get('warehouse_name', ''))))
            self.tbl_hist.setItem(i, 3, QTableWidgetItem(str(m.get('item_code', ''))))
            self.tbl_hist.setItem(i, 4, QTableWidgetItem(str(m.get('item_name', ''))))
            self.tbl_hist.setItem(i, 5, QTableWidgetItem(str(m.get('quantity', ''))))
            self.tbl_hist.setItem(i, 6, QTableWidgetItem(str(m.get('status', 'POSTED'))))


    def _find_item(self, code):
        for it in (self._items or []):
            if str(it.get('code', '')) == code:
                return it
        return None

        hint = QLabel('ادخل كود الصنف - سيملا الاسم والوحدة تلقائيا.')
        hint.setStyleSheet('color: #888C7A; font-size: 11px;')
        ly.addWidget(hint)
        return tab

