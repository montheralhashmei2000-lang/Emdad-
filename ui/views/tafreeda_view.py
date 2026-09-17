"""التفريدة اليومية - Tafreeda (Daily Allocations) View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QDateEdit,
    QMessageBox, QTabWidget, QFormLayout, QFrame, QDoubleSpinBox,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService
from ui.theme import make_header_label


class TafreedaView(QWidget):
    """إدارة التفريدة اليومية - تسجيل توزيع المؤن حسب القوة."""

    def __init__(self, parent=None, api_service: ApiService | None = None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._tafreeda_id = None
        self._units = []
        self._items = []
        self._init_ui()
        self._load_metadata()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label('التفريدة اليومية (تسجيل توزيع المؤن)'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._tab_form = QWidget()
        self._tab_archive = QWidget()
        self.tabs.addTab(self._tab_form, 'تسجيل تفريدة جديدة')
        self.tabs.addTab(self._tab_archive, 'أرشيف التفريدات')
        self._build_form_tab()
        self._build_archive_tab()

    def _build_form_tab(self):
        layout = QVBoxLayout(self._tab_form)
        layout.setSpacing(12)
        header_card = QFrame()
        header_card.setObjectName('card')
        header_card.setStyleSheet(
            "QFrame#card { background:#f9f9f9; border:1px solid #ddd; "
            "border-radius:6px; padding:10px; }"
        )
        form = QFormLayout(header_card)
        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.cb_unit = QComboBox()
        self.cb_unit.addItem('-- اختر الوحدة --', None)
        self.cb_unit.currentIndexChanged.connect(self._on_unit_changed)
        self.le_total_strength = QLineEdit('0')
        self.le_total_strength.setReadOnly(True)
        self.le_total_strength.setStyleSheet(
            "background-color: #E8F5E9; font-weight: bold;"
        )
        form.addRow('تاريخ التفريدة:', self.dt_date)
        form.addRow('الوحدة المستفيدة:', self.cb_unit)
        form.addRow('إجمالي القوة:', self.le_total_strength)
        layout.addWidget(header_card)
        toolbar = QHBoxLayout()
        self.btn_calc = QPushButton('🧮 احتساب من الاستحقاقات')
        self.btn_calc.clicked.connect(self._calculate_from_entitlements)
        self.btn_calc.setStyleSheet(
            "background-color:#3498DB; color:white; font-weight:bold; padding:8px;"
        )
        toolbar.addWidget(self.btn_calc)
        self.btn_add_row = QPushButton('➕ إضافة صنف')
        self.btn_add_row.clicked.connect(self._add_empty_row)
        toolbar.addWidget(self.btn_add_row)
        self.btn_save = QPushButton('💾 حفظ التفريدة')
        self.btn_save.clicked.connect(self._save_tafreeda)
        self.btn_save.setStyleSheet(
            "background-color:#27AE60; color:white; font-weight:bold; padding:8px;"
        )
        toolbar.addWidget(self.btn_save)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.tbl_items = QTableWidget()
        self.tbl_items.setColumnCount(5)
        self.tbl_items.setHorizontalHeaderLabels([
            '#', 'الصنف', 'وحدة القياس', 'كمية الفرد', 'الكمية الإجمالية'
        ])
        self.tbl_items.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tbl_items.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tbl_items.setAlternatingRowColors(True)
        layout.addWidget(self.tbl_items, 1)
        self.le_notes = QLineEdit()
        self.le_notes.setPlaceholderText('ملاحظات...')
        layout.addWidget(QLabel('ملاحظات:'))
        layout.addWidget(self.le_notes)

    def _build_archive_tab(self):
        layout = QVBoxLayout(self._tab_archive)
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel('الوحدة:'))
        self.cb_filter_unit = QComboBox()
        self.cb_filter_unit.addItem('الكل', None)
        filter_bar.addWidget(self.cb_filter_unit, 1)
        btn_refresh = QPushButton('🔄 تحديث')
        btn_refresh.clicked.connect(self._load_archive)
        filter_bar.addWidget(btn_refresh)
        layout.addLayout(filter_bar)
        self.tbl_archive = QTableWidget()
        self.tbl_archive.setColumnCount(6)
        self.tbl_archive.setHorizontalHeaderLabels([
            '#', 'التاريخ', 'الوحدة', 'عدد الأصناف', 'إجمالي القوة', 'إجراءات'
        ])
        self.tbl_archive.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tbl_archive.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tbl_archive.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tbl_archive.setAlternatingRowColors(True)
        layout.addWidget(self.tbl_archive, 1)

    def _load_metadata(self):
        try:
            ok, units = self.api_service.get_units()
            if ok and units:
                self._units = units
                for u in units:
                    self.cb_unit.addItem(
                        f"{u.get('code', '')} - {u.get('name', '')}",
                        u.get('id')
                    )
                    self.cb_filter_unit.addItem(u.get('name', ''), u.get('id'))
        except Exception as e:
            print(f"Error loading units: {e}")
        try:
            ok, items = self.api_service.get_items()
            if ok and items:
                self._items = items
        except Exception as e:
            print(f"Error loading items: {e}")

    def _on_unit_changed(self):
        unit_id = self.cb_unit.currentData()
        if not unit_id:
            return
        date_str = self.dt_date.date().toString('yyyy-MM-dd')
        try:
            ok, data = self.api_service.get_strength_by_date(unit_id, date_str)
            if ok and data:
                total = sum(d.get('total', 0) for d in data)
                self.le_total_strength.setText(str(total))
            else:
                self.le_total_strength.setText('0')
        except Exception:
            self.le_total_strength.setText('0')

    def _add_empty_row(self):
        row = self.tbl_items.rowCount()
        self.tbl_items.insertRow(row)
        self.tbl_items.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        cb_item = QComboBox()
        cb_item.addItem('-- اختر --', None)
        for itm in self._items:
            cb_item.addItem(
                f"{itm.get('item_code', '')} - {itm.get('name', '')}",
                itm.get('id')
            )
        cb_item.currentIndexChanged.connect(
            lambda _, r=row: self._on_item_selected(r)
        )
        self.tbl_items.setCellWidget(row, 1, cb_item)
        self.tbl_items.setItem(row, 2, QTableWidgetItem('-'))
        sb_qty = QDoubleSpinBox()
        sb_qty.setMaximum(999999.99)
        sb_qty.setDecimals(3)
        sb_qty.valueChanged.connect(lambda _, r=row: self._recalc_total(r))
        self.tbl_items.setCellWidget(row, 3, sb_qty)
        self.tbl_items.setItem(row, 4, QTableWidgetItem('0'))

    def _on_item_selected(self, row):
        cb_item = self.tbl_items.cellWidget(row, 1)
        if not cb_item:
            return
        item_id = cb_item.currentData()
        if not item_id:
            return
        item = next((i for i in self._items if i.get('id') == item_id), None)
        if not item:
            return
        units = item.get('units', [])
        if units:
            base = next((u for u in units if u.get('is_base_unit')), units[0])
            self.tbl_items.item(row, 2).setText(base.get('unit_name', '-'))

    def _recalc_total(self, row):
        sb_qty = self.tbl_items.cellWidget(row, 3)
        if not sb_qty:
            return
        try:
            strength = int(self.le_total_strength.text() or '0')
            total = sb_qty.value() * strength
            self.tbl_items.item(row, 4).setText(f"{total:.3f}")
        except (ValueError, AttributeError):
            pass

    def _calculate_from_entitlements(self):
        unit_id = self.cb_unit.currentData()
        if not unit_id:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء اختيار الوحدة أولاً.')
            return
        try:
            ok, entitlements = self.api_service.get_entitlements()
            if not ok or not entitlements:
                QMessageBox.information(
                    self, 'لا توجد استحقاقات',
                    'لا توجد استحقاقات مسجلة للأصناف.'
                )
                return
            self.tbl_items.setRowCount(0)
            for ent in entitlements:
                self._add_empty_row()
                row = self.tbl_items.rowCount() - 1
                cb_item = self.tbl_items.cellWidget(row, 1)
                for i in range(cb_item.count()):
                    if cb_item.itemData(i) == ent.get('item_id'):
                        cb_item.setCurrentIndex(i)
                        break
                sb_qty = self.tbl_items.cellWidget(row, 3)
                sb_qty.setValue(ent.get('qty_per_person', 0))
                self._recalc_total(row)
            QMessageBox.information(self, 'تم', 'تم تحميل الاستحقاقات بنجاح.')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'فشل تحميل الاستحقاقات: {e}')

    def _save_tafreeda(self):
        unit_id = self.cb_unit.currentData()
        if not unit_id:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء اختيار الوحدة.')
            return
        if self.tbl_items.rowCount() == 0:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد أصناف في التفريدة.')
            return
        items = []
        for r in range(self.tbl_items.rowCount()):
            cb_item = self.tbl_items.cellWidget(r, 1)
            sb_qty = self.tbl_items.cellWidget(r, 3)
            if not cb_item or not sb_qty:
                continue
            item_id = cb_item.currentData()
            if not item_id:
                continue
            qty = sb_qty.value()
            if qty <= 0:
                continue
            item = next((i for i in self._items if i.get('id') == item_id), None)
            unit_id_measure = None
            if item and item.get('units'):
                base = next(
                    (u for u in item['units'] if u.get('is_base_unit')),
                    item['units'][0]
                )
                unit_id_measure = base.get('id')
            if unit_id_measure:
                items.append({
                    'item_id': item_id,
                    'measure_unit_id': unit_id_measure,
                    'qty_per_person': qty,
                })
        if not items:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد أصناف صالحة للحفظ.')
            return
        payload = {
            'tafreeda_date': self.dt_date.date().toString('yyyy-MM-dd'),
            'beneficiary_unit_id': unit_id,
            'notes': self.le_notes.text().strip(),
            'items': items,
        }
        try:
            ok, data = self.api_service._request('POST', '/api/tafreeda', json=payload)
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم حفظ التفريدة بنجاح.')
                self._reset_form()
                self._load_archive()
            else:
                QMessageBox.critical(self, 'خطأ', f'فشل الحفظ: {data}')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', f'حدث خطأ: {e}')

    def _reset_form(self):
        self.tbl_items.setRowCount(0)
        self.le_notes.clear()
        self.le_total_strength.setText('0')
        self.cb_unit.setCurrentIndex(0)

    def _load_archive(self):
        unit_filter = self.cb_filter_unit.currentData()
        params = {}
        if unit_filter:
            params['unit_id'] = unit_filter
        try:
            ok, data = self.api_service._request('GET', '/api/tafreeda', params=params)
            if not ok:
                return
            self.tbl_archive.setRowCount(len(data) if data else 0)
            for r, taf in enumerate(data or []):
                self.tbl_archive.setItem(r, 0, QTableWidgetItem(str(r + 1)))
                self.tbl_archive.setItem(r, 1, QTableWidgetItem(str(taf.get('tafreeda_date', ''))))
                self.tbl_archive.setItem(
                    r, 2, QTableWidgetItem(
                        next((u.get('name', '-') for u in self._units
                             if u.get('id') == taf.get('beneficiary_unit_id')), '-')
                    )
                )
                self.tbl_archive.setItem(r, 3, QTableWidgetItem(str(len(taf.get('items', [])))))
                self.tbl_archive.setItem(r, 4, QTableWidgetItem(str(taf.get('total_strength', 0))))
                btn_view = QPushButton('👁️ عرض')
                btn_view.clicked.connect(lambda _, t=taf: self._view_tafreeda(t))
                self.tbl_archive.setCellWidget(r, 5, btn_view)
        except Exception as e:
            print(f"Error loading archive: {e}")

    def _view_tafreeda(self, taf):
        items_text = ""
        for itm in taf.get('items', []):
            items_text += f"• صنف #{itm.get('item_id')}: {itm.get('qty_per_person', 0)}\n"
        QMessageBox.information(
            self,
            f"تفريدة {taf.get('tafreeda_date', '')}",
            f"الوحدة: {taf.get('beneficiary_unit_id', '-')}\n"
            f"ملاحظات: {taf.get('notes', '-')}\n\nالأصناف:\n{items_text or 'لا توجد أصناف'}"
        )

    def load_data(self):
        """Public method to refresh all data."""
        self._load_metadata()
        self._load_archive()