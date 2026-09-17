"""محضر فحص البضاعة - Inspection Report View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDateEdit,
    QMessageBox, QTabWidget, QFormLayout, QFrame, QDoubleSpinBox,
    QAbstractItemView, QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService
from ui.theme import make_header_label


class InspectionReportView(QWidget):
    """محضر فحص البضاعة - يوثق حالة البضاعة عند الاستلام."""

    def __init__(self, parent=None, api_service: ApiService | None = None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._inspection_id = None
        self._suppliers = []
        self._items = []
        self._warehouses = []
        self._init_ui()
        self._load_metadata()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label('محضر فحص البضاعة (جودة الاستلام والمراجعة)'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._tab_form = QWidget()
        self._tab_list = QWidget()
        self.tabs.addTab(self._tab_form, 'إنشاء محضر فحص')
        self.tabs.addTab(self._tab_list, 'سجل المحاضر')
    def _build_form_tab(self):
        layout = QVBoxLayout(self._tab_form)
        layout.setSpacing(12)
        header_card = QGroupBox('بيانات المحضر الأساسية')
        form = QFormLayout(header_card)
        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.le_ref = QLineEdit()
        self.le_ref.setPlaceholderText('مثال: INS-2026-001')
        self.cb_supplier = QComboBox()
        self.cb_supplier.addItem('-- اختر المورد --', None)
        self.cb_warehouse = QComboBox()
        self.cb_warehouse.addItem('-- اختر المخزن --', None)
        self.le_inspector = QLineEdit()
        self.le_inspector.setPlaceholderText('اسم الفاحص/اللجنة')
        form.addRow('تاريخ الفحص:', self.dt_date)
        form.addRow('رقم المحضر:', self.le_ref)
        form.addRow('المورّد:', self.cb_supplier)
        form.addRow('المخزن الوجهة:', self.cb_warehouse)
        form.addRow('اسم الفاحص/اللجنة:', self.le_inspector)
        layout.addWidget(header_card)
        items_box = QGroupBox('أصناف البضاعة المفحوصة')
        items_layout = QVBoxLayout(items_box)
        toolbar = QHBoxLayout()
        btn_add = QPushButton('➕ إضافة صنف')
        btn_add.clicked.connect(self._add_item_row)
        toolbar.addWidget(btn_add)
        btn_clear = QPushButton('🗑️ تفريغ الجدول')
        btn_clear.clicked.connect(lambda: self.tbl_items.setRowCount(0))
        toolbar.addWidget(btn_clear)
        toolbar.addStretch()
        items_layout.addLayout(toolbar)
        self.tbl_items = QTableWidget()
        self.tbl_items.setColumnCount(7)
        self.tbl_items.setHorizontalHeaderLabels([
            '#', 'الصنف', 'الكمية المورّدة', 'الكمية السليمة', 'الكمية التالفة', 'سبب التلف', 'الإجراء'
        ])
        self.tbl_items.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_items.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_items.setAlternatingRowColors(True)
        items_layout.addWidget(self.tbl_items)
        layout.addWidget(items_box, 1)
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText('ملاحظات عامة، توصيات، تواقيع...')
        self.txt_notes.setMaximumHeight(100)
        layout.addWidget(QLabel('ملاحظات/التوصيات:'))
        layout.addWidget(self.txt_notes)
        action_bar = QHBoxLayout()
        btn_draft = QPushButton('💾 حفظ كمسودة')
        btn_draft.clicked.connect(lambda: self._save(status='DRAFT'))
        action_bar.addWidget(btn_draft)
        btn_approve = QPushButton('✅ اعتماد المحضر')
        btn_approve.setStyleSheet("background-color:#27AE60; color:white; font-weight:bold;")
        btn_approve.clicked.connect(lambda: self._save(status='APPROVED'))
        action_bar.addWidget(btn_approve)
        btn_print = QPushButton('🖨️ طباعة')
        btn_print.clicked.connect(self._print)
        action_bar.addWidget(btn_print)
        layout.addLayout(action_bar)
        self._build_form_tab()
        self._build_list_tab()


    def _build_list_tab(self):
        layout = QVBoxLayout(self._tab_list)
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel('الحالة:'))
        self.cb_status = QComboBox()
        self.cb_status.addItems(['الكل', 'مسودة', 'معتمد', 'مرفوض'])
        filter_bar.addWidget(self.cb_status)
        btn_refresh = QPushButton('🔄 تحديث')
        btn_refresh.clicked.connect(self._load_list)
        filter_bar.addWidget(btn_refresh)
        filter_bar.addStretch()
        layout.addLayout(filter_bar)
        self.tbl_list = QTableWidget()
        self.tbl_list.setColumnCount(7)
        self.tbl_list.setHorizontalHeaderLabels(['#', 'التاريخ', 'الرقم', 'المورّد', 'المخزن', 'الحالة', 'إجراءات'])
        self.tbl_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_list.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl_list.setAlternatingRowColors(True)
        layout.addWidget(self.tbl_list, 1)

    def _load_metadata(self):
        try:
            ok, suppliers = self.api_service.get_suppliers()
            if ok and suppliers:
                self._suppliers = suppliers
                for s in suppliers:
                    self.cb_supplier.addItem(s.get('name', ''), s.get('id'))
        except Exception as e:
            print(f"Error loading suppliers: {e}")
        try:
            ok, items = self.api_service.get_items()
            if ok and items:
                self._items = items
        except Exception as e:
            print(f"Error loading items: {e}")
        try:
            ok, warehouses = self.api_service.get_warehouses()
            if ok and warehouses:
                self._warehouses = warehouses
                for w in warehouses:
                    self.cb_warehouse.addItem(w.get('name', ''), w.get('id'))
        except Exception as e:
            print(f"Error loading warehouses: {e}")
        self._load_list()

    def _add_item_row(self):
        row = self.tbl_items.rowCount()
        self.tbl_items.insertRow(row)
        self.tbl_items.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        cb_item = QComboBox()
        cb_item.addItem('-- اختر --', None)
        for itm in self._items:
            cb_item.addItem(f"{itm.get('item_code', '')} - {itm.get('name', '')}", itm.get('id'))
        self.tbl_items.setCellWidget(row, 1, cb_item)
        sb_supplied = QDoubleSpinBox()
        sb_supplied.setMaximum(999999.99)
        sb_supplied.setDecimals(3)
        self.tbl_items.setCellWidget(row, 2, sb_supplied)
        sb_good = QDoubleSpinBox()
        sb_good.setMaximum(999999.99)
        sb_good.setDecimals(3)
        sb_good.valueChanged.connect(lambda _, r=row: self._calc_damaged(r))
        self.tbl_items.setCellWidget(row, 3, sb_good)
        self.tbl_items.setItem(row, 4, QTableWidgetItem('0'))
        le_reason = QLineEdit()
        le_reason.setPlaceholderText('مثال: تلف، نقص وزن، سوء تغليف...')
        self.tbl_items.setCellWidget(row, 5, le_reason)

    def _save(self, status='DRAFT'):
        supplier_id = self.cb_supplier.currentData()
        warehouse_id = self.cb_warehouse.currentData()
        if not supplier_id or not warehouse_id:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء تعبئة جميع الحقول الإلزامية.')
            return
        if self.tbl_items.rowCount() == 0:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء إضافة أصناف للفحص.')
            return
        items = []
        for r in range(self.tbl_items.rowCount()):
            cb_item = self.tbl_items.cellWidget(r, 1)
            sb_supplied = self.tbl_items.cellWidget(r, 2)
            sb_good = self.tbl_items.cellWidget(r, 3)
            le_reason = self.tbl_items.cellWidget(r, 5)
            cb_action = self.tbl_items.cellWidget(r, 6)
            if not cb_item or not sb_supplied or not sb_good:
                continue
            item_id = cb_item.currentData()
            if not item_id:
                continue
            items.append({
                'item_id': item_id,
                'qty_supplied': sb_supplied.value(),
                'qty_good': sb_good.value(),
                'qty_damaged': sb_supplied.value() - sb_good.value(),
                'damage_reason': le_reason.text().strip() if le_reason else '',
                'action': cb_action.currentText() if cb_action else 'اعتماد',
            })
        if not items:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد أصناف صالحة للحفظ.')
            return
        payload = {
            'inspection_date': self.dt_date.date().toString('yyyy-MM-dd'),
            'ref_number': self.le_ref.text().strip(),
            'supplier_id': supplier_id,
            'warehouse_id': warehouse_id,
            'inspector_name': self.le_inspector.text().strip(),
            'status': status,
            'notes': self.txt_notes.toPlainText().strip(),
            'items': items,
        }
        try:
            ok, data = self.api_service._request('POST', '/api/inspection-reports', json=payload)
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم حفظ المحضر بنجاح.')
                self._reset_form()
                self._load_list()
            else:
                QMessageBox.critical(self, 'خطأ', f'فشل الحفظ: {data}')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'حدث خطأ: {e}')

    def _reset_form(self):
        self.tbl_items.setRowCount(0)
        self.txt_notes.clear()
        self.le_ref.clear()
        self.le_inspector.clear()
        self.cb_supplier.setCurrentIndex(0)
        self.cb_warehouse.setCurrentIndex(0)

    def _load_list(self):
        try:
            ok, data = self.api_service._request('GET', '/api/inspection-reports')
            if not ok:
                return
            self.tbl_list.setRowCount(len(data) if data else 0)
            for r, ins in enumerate(data or []):
                self.tbl_list.setItem(r, 0, QTableWidgetItem(str(r + 1)))
                self.tbl_list.setItem(r, 1, QTableWidgetItem(str(ins.get('inspection_date', ''))))
                self.tbl_list.setItem(r, 2, QTableWidgetItem(ins.get('ref_number', '-')))
                self.tbl_list.setItem(r, 3, QTableWidgetItem(
                    next((s.get('name', '-') for s in self._suppliers
                         if s.get('id') == ins.get('supplier_id')), '-')))
                self.tbl_list.setItem(r, 4, QTableWidgetItem(
                    next((w.get('name', '-') for w in self._warehouses
                         if w.get('id') == ins.get('warehouse_id')), '-')))
                status_text = {'DRAFT': 'مسودة', 'APPROVED': 'معتمد', 'REJECTED': 'مرفوض'}.get(
                    ins.get('status', ''), ins.get('status', '-'))
                self.tbl_list.setItem(r, 5, QTableWidgetItem(status_text))
                btn_view = QPushButton('👁️ عرض')
                btn_view.clicked.connect(lambda _, i=ins: self._view_report(i))
                self.tbl_list.setCellWidget(r, 6, btn_view)
        except Exception as e:
            print(f"Error loading list: {e}")

    def _view_report(self, ins):
        QMessageBox.information(
            self, f"محضر {ins.get('ref_number', '')}",
            f"التاريخ: {ins.get('inspection_date', '-')}\n"
            f"الفاحص: {ins.get('inspector_name', '-')}\n"
            f"الحالة: {ins.get('status', '-')}\n"
            f"ملاحظات: {ins.get('notes', '-')}")

    def _print(self):
        QMessageBox.information(self, 'طباعة', 'جاري إرسال المحضر للطباعة...')

    def load_data(self):
        self._load_metadata()
        cb_action = QComboBox()
        cb_action.addItems(['اعتماد', 'رفض', 'إعادة تغليف', 'للمطالبة', 'إتلاف'])
        self.tbl_items.setCellWidget(row, 6, cb_action)

    def _calc_damaged(self, row):
        sb_sup = self.tbl_items.cellWidget(row, 2)
        sb_good = self.tbl_items.cellWidget(row, 3)
        if sb_sup and sb_good:
            damaged = max(0.0, sb_sup.value() - sb_good.value())
            self.tbl_items.item(row, 4).setText(f"{damaged:.3f}")