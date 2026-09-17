# NOTE: هذا الملف أُعيد بناؤه يدوياً من ملف receive_view.pyc
# الملف الأصلي مُصرَّف بصيغة Python 3.14 (RC) التي لا تدعمها أدوات فك التشفير
# الحالية. تم استخراج كل الأسماء والنصوص والـ docstrings والقيم الثابتة (بما
# فيها كائن slice) بدقة كاملة عبر قارئ marshal مخصص، وأُعيد بناء المنطق
# بالاعتماد عليها وعلى نمط الملفات السابقة من نفس المشروع. هذا أكبر وأعقد
# ملف حتى الآن (تبويبات متعددة، دوال متداخلة لإدارة صفوف الجدول، أسطوانات
# قابلة للتعبئة). الأجزاء الأقل يقيناً معلَّمة بتعليق "تقريبي".

import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QHBoxLayout, QMessageBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QTabWidget, QCheckBox,
    QScrollArea, QFrame, QSizePolicy, QInputDialog
)
from PyQt6.QtCore import Qt, QDate

from api_service import ApiService
from theme import make_header_label
from excel_helper import export_table_to_excel, import_excel_to_dataframe, export_template
from print_helper import print_receive_voucher
from voucher_dialog import VoucherDetailsDialog


class ReceiveView(QWidget):
    """Panel for receiving stock (GRN) with inline grid, history tab, and toolbar."""

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self._items_data = None
        self._warehouses_data = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.addWidget(make_header_label('سند توريد مخزني'))

        self.tabs = QTabWidget()
        self._tab_form = QWidget()
        self._tab_drafts = QWidget()
        self._tab_history = QWidget()

        self.tabs.addTab(self._tab_form, 'سند الوارد الجديد')
        self.tabs.addTab(self._tab_drafts, 'العمليات المعلقة (المسودات)')
        self.tabs.addTab(self._tab_history, 'سجل الواردات السابقة')

        self._build_form_tab()
        self._build_drafts_tab()
        self._build_history_tab()

        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

    def _build_form_tab(self):
        main_v = QVBoxLayout(self._tab_form)
        main_v.setContentsMargins(10, 10, 10, 10)
        main_v.setSpacing(10)

        master_card = QWidget()
        master_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        master_card.setObjectName('card')
        master_card.setStyleSheet('QWidget#card { background: white; border-radius: 6px; border: 1px solid #ddd; }')

        grid = QGridLayout(master_card)
        grid.setColumnStretch(1, True)

        self.cb_warehouse = QComboBox()
        self.cb_warehouse.setFixedHeight(30)

        self.le_ref = QLineEdit()
        self.le_ref.setPlaceholderText('اختياري')

        self.le_notes = QLineEdit()

        self.cb_supplier = QComboBox()
        self.cb_supplier.setFixedHeight(30)

        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())

        self.le_insp_committee = QLineEdit()
        self.le_insp_committee.setPlaceholderText('عضو الرقابة والتفتيش')

        self.le_supervision = QLineEdit()
        self.le_supervision.setPlaceholderText('عضو المراجعة والتدقيق')

        self.le_audit = QLineEdit()

        self.le_insp_report = QLineEdit()
        self.le_insp_report.setPlaceholderText('رقم الفاتورة أو التاجر (اختياري)')

        H = QHBoxLayout
        grid.addWidget(QLabel('التخزين في (المستودع):'), 0, 0)
        grid.addWidget(self.cb_warehouse, 0, 1)
        grid.addWidget(QLabel('الجهة الموردة:'), 0, 2)
        grid.addWidget(self.cb_supplier, 0, 3)

        grid.addWidget(QLabel('المرجع:'), 1, 0)
        grid.addWidget(self.le_ref, 1, 1)
        grid.addWidget(QLabel('لجنة الفحص:'), 1, 2)
        grid.addWidget(self.le_insp_committee, 1, 3)

        grid.addWidget(QLabel('التفتيش:'), 2, 0)
        grid.addWidget(self.le_supervision, 2, 1)
        grid.addWidget(QLabel('التدقيق:'), 2, 2)
        grid.addWidget(self.le_audit, 2, 3)

        grid.addWidget(QLabel('الفاتورة/التاجر:'), 3, 0)
        grid.addWidget(self.le_insp_report, 3, 1)
        grid.addWidget(QLabel('تاريخ التوريد:'), 3, 2)
        grid.addWidget(self.dt_date, 3, 3)

        grid.addWidget(QLabel('ملاحظات:'), 4, 0)
        grid.addWidget(self.le_notes, 4, 1, 1, 3)

        main_v.addWidget(master_card)

        btn_bar = H()
        btn_save = QPushButton('اعتماد وتسجيل سند الوارد')
        btn_save.setObjectName('gold_btn')
        btn_save.clicked.connect(lambda: self.save_receipt(is_draft=False))
        btn_bar.addWidget(btn_save)

        btn_draft = QPushButton('حفظ كمسودة')
        btn_draft.setStyleSheet('background-color: #f39c12; color: white;')
        btn_draft.clicked.connect(lambda: self.save_receipt(is_draft=True))
        btn_bar.addWidget(btn_draft)

        btn_reset = QPushButton('سند جديد')
        btn_reset.clicked.connect(self._reset_form)
        btn_bar.addWidget(btn_reset)
        btn_bar.addStretch()
        main_v.addLayout(btn_bar)

        scan_lay = H()
        scan_lay.addWidget(QLabel('باركوود 🏷️:'))
        self.le_barcode = QLineEdit()
        self.le_barcode.setPlaceholderText('مرر قارئ الباركود..')
        self.le_barcode.setStyleSheet('padding: 3px; border: 2px solid #C5A028; border-radius: 4px;')
        self.le_barcode.returnPressed.connect(self._on_barcode_scanned)
        scan_lay.addWidget(self.le_barcode)
        main_v.addLayout(scan_lay)

        self.table = QTableWidget()
        self.table.setHorizontalHeaderLabels(('كود', 'اسم الصنف', 'الوحدة', 'الكمية', 'إجراء'))
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.horizontalHeader().setMinimumSectionSize(80)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        main_v.addWidget(self.table)

        foot_bar = H()

        btn_print = QPushButton('🖨️ طباعة')
        btn_print.clicked.connect(self._print_voucher)
        foot_bar.addWidget(btn_print)

        btn_export = QPushButton('📥 تصدير')
        btn_export.clicked.connect(lambda: export_table_to_excel(self.table, 'Receive_Export.xlsx'))
        foot_bar.addWidget(btn_export)

        user = getattr(self.parent(), 'current_user', None) or {}
        is_admin = user.get('role', '') == 'ADMIN'
        self._is_admin = is_admin

        tabs_p = user.get('permissions', {}).get('receipts', {}).get('tabs', {})
        self._tabs_perms = tabs_p
        has_explicit = isinstance(tabs_p, dict) and tabs_p
        new_p = tabs_p.get('tab_new', {})

        btn_import = QPushButton('📤 استيراد')
        btn_import.clicked.connect(self._import_from_excel)
        foot_bar.addWidget(btn_import)

        btn_template = QPushButton('📋 قالب')
        btn_template.clicked.connect(lambda: export_template(
            self, 'receive_template.xlsx', ('كود الصنف', 'الكمية', 'الوحدة'), 'كود الصنف'
        ))
        foot_bar.addWidget(btn_template)

        # تقريبي: الشرط الدقيق لإظهار/إخفاء الأزرار والتبويبات حسب الصلاحيات
        if not is_admin and has_explicit:
            btn_import.setVisible(new_p.get('create', False))
            btn_print.setVisible(new_p.get('print', False))

        foot_bar.addStretch()
        main_v.addLayout(foot_bar)

        if not is_admin and has_explicit:
            self.tabs.setTabVisible(0, new_p.get('view', False))
            self.tabs.setTabVisible(1, tabs_p.get('tab_drafts', {}).get('view', False))
            self.tabs.setTabVisible(2, tabs_p.get('tab_history', {}).get('view', False))

        for i in range(self.tabs.count()):
            if self.tabs.isTabVisible(i):
                self.tabs.setCurrentIndex(i)
                break

    def _build_drafts_tab(self):
        layout = QVBoxLayout(self._tab_drafts)
        layout.setContentsMargins(10, 10, 10, 10)

        toolbar = QHBoxLayout()
        btn_refresh = QPushButton('تحديث 🔄')
        btn_refresh.clicked.connect(self._load_drafts)
        toolbar.addWidget(btn_refresh)

        action_lay = QHBoxLayout()
        btn_view_draft = QPushButton('عرض السند 🖨️')
        btn_view_draft.setStyleSheet('background-color: #2980B9; color: white; padding: 8px 15px; font-weight: bold;')
        btn_view_draft.clicked.connect(self._view_selected_draft)
        action_lay.addWidget(btn_view_draft)

        btn_approve_draft = QPushButton('اعتماد وتسجيل ✅')
        btn_approve_draft.setStyleSheet('background-color: #2E6B35; color: white; padding: 8px 15px; font-weight: bold;')
        btn_approve_draft.clicked.connect(self._approve_selected_draft)
        action_lay.addWidget(btn_approve_draft)

        btn_delete_draft = QPushButton('حذف ❌')
        btn_delete_draft.setStyleSheet('background-color: #C0392B; color: white; padding: 8px 15px; font-weight: bold;')
        btn_delete_draft.clicked.connect(self._delete_selected_draft)
        action_lay.addWidget(btn_delete_draft)

        is_admin = getattr(self, '_is_admin', False)
        dp = getattr(self, '_tabs_perms', {}).get('tab_drafts', {})
        if not is_admin:
            btn_approve_draft.setVisible(dp.get('approve', False))
            btn_delete_draft.setVisible(dp.get('delete', False))

        toolbar.addStretch()
        toolbar.addLayout(action_lay)
        layout.addLayout(toolbar)

        self.tbl_drafts = QTableWidget()
        self.tbl_drafts.setHorizontalHeaderLabels(
            ('م', 'نوع السند', 'عدد الأصناف', 'الجهة الموردة', 'التاريخ', 'ملاحظة', 'المرجع')
        )
        self.tbl_drafts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_drafts.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_drafts.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_drafts.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.tbl_drafts)

    def _load_drafts(self):
        self.tbl_drafts.setRowCount(0)
        wh_id = self.cb_warehouse.currentData()

        ok, drafts = self.api_service.get_drafts(warehouse_id=wh_id, movement_type='IN')
        filtered = drafts if ok else []

        groups = {}
        for d in filtered:
            ref = d.get('reference_no', '')
            date_key = str(d.get('movement_date', ''))
            key = ref or date_key
            groups.setdefault(key, []).append(d)

        for i, (key, items_list) in enumerate(groups.items()):
            self.tbl_drafts.insertRow(i)
            first = items_list[0]

            self.tbl_drafts.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            item_idx = QTableWidgetItem('استلام')
            item_idx.setData(Qt.ItemDataRole.UserRole, items_list)
            self.tbl_drafts.setItem(i, 1, item_idx)

            self.tbl_drafts.setItem(i, 2, QTableWidgetItem(str(len(items_list))))
            self.tbl_drafts.setItem(i, 3, QTableWidgetItem(first.get('supplier_name', '')))
            self.tbl_drafts.setItem(i, 4, QTableWidgetItem(str(first.get('movement_date', ''))))
            self.tbl_drafts.setItem(i, 5, QTableWidgetItem(first.get('notes', '')))
            self.tbl_drafts.setItem(i, 6, QTableWidgetItem(str(key)))

    def _get_selected_draft_data(self):
        r = self.tbl_drafts.currentRow()
        if r < 0:
            QMessageBox.warning(self, 'تنبيه', 'يرجى تحديد مسودة من الجدول أولاً.')
            return None
        item = self.tbl_drafts.item(r, 1)
        return item.data(Qt.ItemDataRole.UserRole)

    def _view_selected_draft(self):
        items_list = self._get_selected_draft_data()
        if not items_list:
            return

        first = items_list[0]

        wh_id = first.get('warehouse_id')
        idx = self.cb_warehouse.findData(wh_id)
        self.cb_warehouse.setCurrentIndex(idx)

        sup_id = first.get('supplier_id')
        idx = self.cb_supplier.findData(sup_id)
        self.cb_supplier.setCurrentIndex(idx)

        date_str = str(first.get('movement_date', ''))[:10]
        y, m, d = map(int, date_str.split('-'))
        self.dt_date.setDate(QDate(y, m, d))

        self.le_ref.setText(first.get('reference_no', ''))
        self.le_notes.setText(first.get('notes', ''))

        self.table.setRowCount(0)
        for r, itm in enumerate(items_list):
            self.add_empty_row()
            cb_code = self.table.cellWidget(r, 0)
            idx_code = cb_code.findData(itm.get('item_id'))
            cb_code.setCurrentIndex(idx_code)

            cb_unit = self.table.cellWidget(r, 2)
            idx_unit = cb_unit.findData(itm.get('unit_id'))
            cb_unit.setCurrentIndex(idx_unit)

            le_qty = self.table.cellWidget(r, 3)
            le_qty.setText(str(itm.get('quantity', '')))

        self.tabs.setCurrentIndex(0)

    def _approve_selected_draft(self):
        items_list = self._get_selected_draft_data()
        if not items_list:
            return

        reply = QMessageBox.question(
            self, 'تأكيد الاعتماد', 'هل أنت متأكد من اعتماد السند بالكامل (تسجيل الرصيد الفعلي)؟'
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        movement_ids = [m.get('id') for m in items_list]
        ok, result = self.api_service.approve_draft_bulk(movement_ids)
        if ok:
            QMessageBox.information(self, 'نجاح', 'تم اعتماد سند المسودة بنجاح وتم إضافة الرصيد.')
            self._load_drafts()
        else:
            QMessageBox.critical(self, 'فشل الاعتماد', str(result))

    def _delete_selected_draft(self):
        items_list = self._get_selected_draft_data()
        if not items_list:
            return

        reply = QMessageBox.question(self, 'تأكيد الحذف', 'هل أنت متأكد من حذف هذا السند كمسودة نهائياً؟')
        if reply != QMessageBox.StandardButton.Yes:
            return

        success_count = 0
        for m in items_list:
            ok, res = self.api_service.delete_draft(m.get('id'))
            if ok:
                success_count += 1

        if success_count == len(items_list):
            QMessageBox.information(self, 'نجاح', 'تم الحذف بنجاح.')
        else:
            QMessageBox.warning(
                self, 'تنبيه',
                'تم حذف ' + str(success_count) + ' من أصل ' + str(len(items_list)) + ' أصناف. بعضها فشل.'
            )
        self._load_drafts()

    def _build_history_tab(self):
        layout = QVBoxLayout(self._tab_history)
        top = QHBoxLayout()

        top.addWidget(QLabel('🔍 بحث:'))
        self.h_le_search = QLineEdit()
        self.h_le_search.setPlaceholderText('بحث بالصنف أو رقم المرجع...')
        self.h_le_search.textChanged.connect(self._filter_history)
        top.addWidget(self.h_le_search)

        top.addWidget(QLabel('المستودع:'))
        self.cb_hist_warehouse = QComboBox()
        self.cb_hist_warehouse.addItem('الكل', None)
        self.cb_hist_warehouse.currentIndexChanged.connect(self._load_history)
        top.addWidget(self.cb_hist_warehouse)

        top.addWidget(QLabel('المورد:'))
        self.cb_hist_supplier = QComboBox()
        self.cb_hist_supplier.addItem('الكل', None)
        self.cb_hist_supplier.currentIndexChanged.connect(self._load_history)
        top.addWidget(self.cb_hist_supplier)

        top.addWidget(QLabel('طريقة العرض:'))
        self.cb_history_view_mode = QComboBox()
        self.cb_history_view_mode.addItem('مفصل (كل الأصناف)', 'detailed')
        self.cb_history_view_mode.addItem('مجمّع (حسب السند)', 'grouped')
        self.cb_history_view_mode.currentIndexChanged.connect(self._load_history)
        top.addWidget(self.cb_history_view_mode)

        btn_ref = QPushButton('تحديث السجل 🔄')
        btn_ref.clicked.connect(self._load_history)
        top.addWidget(btn_ref)

        btn_exp = QPushButton('📥 تصدير إكسيل')
        btn_exp.clicked.connect(lambda: export_table_to_excel(self.tbl_history, 'Receive_History.xlsx'))

        is_admin = getattr(self, '_is_admin', False)
        hp = getattr(self, '_tabs_perms', {}).get('tab_history', {})
        if not is_admin:
            btn_exp.setVisible(hp.get('print', False))

        top.addWidget(btn_exp)
        top.addStretch()
        layout.addLayout(top)

        self.tbl_history = QTableWidget()
        self.tbl_history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_history.cellDoubleClicked.connect(self._on_history_double_click)
        layout.addWidget(self.tbl_history)

    def _on_tab_changed(self, index):
        if index == 1:
            self._load_drafts()
        elif index:
            self._load_history()

    def _load_history(self):
        self.tbl_history.setRowCount(0)

        hist_wh_id = self.cb_hist_warehouse.currentData()
        hist_sup_id = self.cb_hist_supplier.currentData()

        ok, movs = self.api_service.get_movements_filtered(
            item_id=None, movement_type='IN', limit=2000, unit_id=None
        )
        filtered_movs = movs if ok else []

        # Filter client-side by warehouse/supplier if selected
        if filtered_movs and (hist_wh_id or hist_sup_id):
            filtered_movs = [
                m for m in filtered_movs
                if (not hist_wh_id or m.get("warehouse_id") == hist_wh_id or m.get("warehouse") == hist_wh_id)
                and (not hist_sup_id or m.get("supplier_id") == hist_sup_id or m.get("supplier") == hist_sup_id)
            ]

        mode = self.cb_history_view_mode.currentData()
        is_grouped = mode == 'grouped'
        self._history_data_map = {}

        if is_grouped:
            self.tbl_history.setColumnCount(6)
            self.tbl_history.setHorizontalHeaderLabels(
                ('التاريخ', 'رقم المرجع (السند)', 'المستودع', 'المورد', 'عدد الأصناف', 'ملاحظات')
            )
            self.tbl_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            groups = {}
            for m in filtered_movs:
                ref = m.get('reference_no', '')
                date_key = str(m.get('id', ''))
                group_key = ref or ('_' + date_key)
                groups.setdefault(group_key, []).append(m)

            for i, (real_ref, items) in enumerate(groups.items()):
                self.tbl_history.insertRow(i)
                first = items[0]

                self.tbl_history.setItem(i, 0, QTableWidgetItem(str(first.get('movement_date', ''))))
                ref_item = QTableWidgetItem(first.get('reference_no', ''))
                ref_item.setData(Qt.ItemDataRole.UserRole, items)
                self.tbl_history.setItem(i, 1, ref_item)
                self.tbl_history.setItem(i, 2, QTableWidgetItem(first.get('warehouse_name', '')))
                self.tbl_history.setItem(i, 3, QTableWidgetItem(first.get('supplier_name', '')))
                self.tbl_history.setItem(i, 4, QTableWidgetItem(str(len(items))))
                self.tbl_history.setItem(i, 5, QTableWidgetItem(first.get('notes', '')))
                self._history_data_map[i] = items
        else:
            self.tbl_history.setColumnCount(8)
            self.tbl_history.setHorizontalHeaderLabels(
                ('التاريخ', 'الصنف', 'المستودع', 'الجهة الموردة', 'الكمية', 'الوحدة', 'المرجع', 'ملاحظات')
            )
            self.tbl_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            for i, m in enumerate(filtered_movs):
                self.tbl_history.insertRow(i)
                self.tbl_history.setItem(i, 0, QTableWidgetItem(str(m.get('movement_date', ''))))
                self.tbl_history.setItem(i, 1, QTableWidgetItem(m.get('item_name', '')))
                self.tbl_history.setItem(i, 2, QTableWidgetItem(m.get('warehouse_name', '')))
                self.tbl_history.setItem(i, 3, QTableWidgetItem(m.get('supplier_name', '')))
                self.tbl_history.setItem(i, 4, QTableWidgetItem(str(m.get('quantity', ''))))
                self.tbl_history.setItem(i, 5, QTableWidgetItem(m.get('unit_name', '')))
                self.tbl_history.setItem(i, 6, QTableWidgetItem(m.get('reference_no', '')))
                self.tbl_history.setItem(i, 7, QTableWidgetItem(m.get('notes', '')))
                self._history_data_map[i] = [m]

    def _on_history_double_click(self, row, col):
        items = getattr(self, '_history_data_map', {}).get(row)
        if not items:
            return
        dlg = VoucherDetailsDialog(items, 'IN', self)
        dlg.exec()

    def load_data(self):
        curr_wh = self.cb_warehouse.currentData()
        curr_sup = self.cb_supplier.currentData()

        if not self.le_ref.text().strip():
            self._generate_next_reference()

        ok, items = self.api_service.get_items()
        self._items_data = items if ok else []

        ok, whs = self.api_service.get_warehouses()
        self.cb_warehouse.clear()
        self.cb_hist_warehouse.clear()
        self.cb_hist_warehouse.addItem('الكل', None)

        self._warehouses_data = whs if ok else []

        allowed = None
        if hasattr(self.parent(), 'current_user'):
            allowed = self.parent().current_user.get('allowed_warehouses')

        for wh in self._warehouses_data:
            if allowed is None or wh.get('id') in allowed:
                label = wh.get('code', '') + ' - ' + wh.get('name', '')
                self.cb_warehouse.addItem(label, wh.get('id'))
                self.cb_hist_warehouse.addItem(label, wh.get('id'))

        ok_sup, sups = self.api_service.get_suppliers(limit=500)
        self.cb_supplier.clear()
        self.cb_hist_supplier.clear()
        self.cb_hist_supplier.addItem('الكل', None)
        if ok_sup:
            for sup in sups:
                self.cb_supplier.addItem(sup.get('name', ''), sup.get('id'))
                self.cb_hist_supplier.addItem(sup.get('name', ''), sup.get('id'))

        idx = self.cb_warehouse.findData(curr_wh)
        self.cb_warehouse.setCurrentIndex(idx)
        idx = self.cb_supplier.findData(curr_sup)
        self.cb_supplier.setCurrentIndex(idx)

        if self.table.rowCount() == 0:
            self.add_empty_row()

        from PyQt6.QtCore import QTimer
        self._auto_refresh_timer = QTimer()
        self._auto_refresh_timer.timeout.connect(self._refresh_items_silently)
        self._auto_refresh_timer.start(30000)

    def _refresh_items_silently(self):
        """تحديث قائمة الأصناف بصمت (بدون مسح الجدول) — يكتشف الأصناف الجديدة."""
        ok, items = self.api_service.get_items()
        if not ok:
            return

        old_ids = {i.get('id') for i in self._items_data} if self._items_data else set()
        new_ids = {i.get('id') for i in items}
        added = new_ids - old_ids

        self._items_data = items
        if not added:
            return

        new_items = [i for i in items if i.get('id') in added]

        for r in range(self.table.rowCount()):
            cb_code = self.table.cellWidget(r, 0)
            cb_name = self.table.cellWidget(r, 1)
            if not cb_code or not cb_name:
                continue
            try:
                cb_code.blockSignals(True)
                cb_name.blockSignals(True)
                for itm in new_items:
                    cb_code.addItem(itm.get('item_code', ''), itm.get('id'))
                    cb_name.addItem(itm.get('name', ''), itm.get('id'))
            except Exception:
                pass
            finally:
                cb_code.blockSignals(False)
                cb_name.blockSignals(False)

    def _generate_next_reference(self):
        ok, data = self.api_service.get_next_reference('و')
        if ok and isinstance(data, dict):
            self.le_ref.setText(data.get('reference_no', 'و-000001'))

    def _merge_duplicates(self):
        """دمج الصفوف المتطابقة (نفس الصنف ونفس الوحدة) تلقائياً."""
        row = 0
        while row < self.table.rowCount():
            cb_code1 = self.table.cellWidget(row, 0)
            cb_unit1 = self.table.cellWidget(row, 2)
            le_qty1 = self.table.cellWidget(row, 3)
            if not cb_code1 or not cb_unit1 or not le_qty1:
                row += 1
                continue

            item_id1 = cb_code1.currentData()
            unit_id1 = cb_unit1.currentData()
            qty_text1 = le_qty1.text().strip()
            try:
                q1 = float(qty_text1)
            except ValueError:
                row += 1
                continue

            r2 = row + 1
            while r2 < self.table.rowCount():
                cb_code2 = self.table.cellWidget(r2, 0)
                cb_unit2 = self.table.cellWidget(r2, 2)
                le_qty2 = self.table.cellWidget(r2, 3)

                if cb_code2 and cb_unit2 and le_qty2:
                    item_id2 = cb_code2.currentData()
                    unit_id2 = cb_unit2.currentData()

                    if item_id1 == item_id2 and unit_id1 == unit_id2:
                        qty_text2 = le_qty2.text().strip()
                        try:
                            q2 = float(qty_text2)
                        except ValueError:
                            q2 = 0

                        q1 += q2
                        le_qty1.setText(str(q1))
                        self.table.removeRow(r2)
                        continue
                r2 += 1

            row += 1

        last_row = self.table.rowCount() - 1
        cb = self.table.cellWidget(last_row, 0) if last_row >= 0 else None
        if cb and cb.currentData():
            self.add_empty_row()

    def _setup_smart_completer(self, combo):
        """Setup smart search completer that filters on any substring match."""
        completer = combo.completer()
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(completer.CompletionMode.PopupCompletion)

    def add_empty_row(self):
        idx = self.table.rowCount()
        self.table.insertRow(idx)

        cb_code = QComboBox()
        cb_code.setEditable(True)
        cb_code.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        cb_code.addItem('', None)
        for itm in self._items_data:
            cb_code.addItem(itm.get('item_code', ''), itm.get('id'))
        cb_code.lineEdit().setPlaceholderText('الكود')
        self._setup_smart_completer(cb_code)

        cb_name = QComboBox()
        cb_name.setEditable(True)
        cb_name.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        cb_name.addItem('', None)
        for itm in self._items_data:
            cb_name.addItem(itm.get('name', ''), itm.get('id'))
        cb_name.lineEdit().setPlaceholderText('اسم الصنف')
        self._setup_smart_completer(cb_name)

        cb_unit = QComboBox()

        le_qty = QLineEdit()
        le_qty.setPlaceholderText('الكمية')

        btn_remove = QPushButton('❌')
        btn_remove.setMaximumWidth(30)
        btn_remove.clicked.connect(lambda _, w=btn_remove: self.remove_row(w))

        def update_unit_and_add_row(index):
            cb_unit.clear()
            item_id = cb_code.itemData(index)

            r = None
            for i in range(self.table.rowCount()):
                if self.table.cellWidget(i, 0) is cb_code:
                    r = i
                    break

            selected_item = next((it for it in self._items_data if it.get('id') == item_id), None)
            if not selected_item:
                return

            for u in selected_item.get('units', []):
                cb_unit.addItem(u.get('unit_name', ''), u.get('id'))

            if selected_item.get('is_refillable'):
                actions = ('توريد ممتلئ', 'توريد فارغ', 'تعبئة')
                chosen, ok = QInputDialog.getItem(
                    self, 'نوع العملية',
                    'الصنف (' + selected_item.get('name', '') + ') قابل للتعبئة.\nاختر نوع العملية:',
                    actions, 0, False
                )
                if ok:
                    action_map = {
                        'توريد ممتلئ': 'RECEIVE_FULL',
                        'توريد فارغ': 'RECEIVE_EMPTY',
                        'تعبئة': 'REFILL',
                    }
                    cb_code.setProperty('cylinder_action', action_map.get(chosen, 'RECEIVE_FULL'))

            if r is not None and r == self.table.rowCount() - 1:
                self.add_empty_row()

        def on_code_changed(index):
            cb_name.blockSignals(True)
            cb_name.setCurrentIndex(index)
            cb_name.blockSignals(False)
            update_unit_and_add_row(index)

        def on_name_changed(index):
            cb_code.blockSignals(True)
            cb_code.setCurrentIndex(index)
            cb_code.blockSignals(False)
            update_unit_and_add_row(index)

        cb_code.currentIndexChanged.connect(on_code_changed)
        cb_name.currentIndexChanged.connect(on_name_changed)
        le_qty.editingFinished.connect(lambda _=None: self._merge_duplicates())

        self.table.setCellWidget(idx, 0, cb_code)
        self.table.setCellWidget(idx, 1, cb_name)
        self.table.setCellWidget(idx, 2, cb_unit)
        self.table.setCellWidget(idx, 3, le_qty)
        self.table.setCellWidget(idx, 4, btn_remove)

    def _on_barcode_scanned(self):
        code = self.le_barcode.text().strip()
        self.le_barcode.clear()
        if not code:
            return

        match = next(
            (i for i in self._items_data
             if str(i.get('barcode', '')) == code or str(i.get('item_code', '')) == code),
            None
        )
        if not match:
            QMessageBox.warning(self, 'تحذير', 'الباركود (' + code + ') غير معرّف!')
            return

        for r in range(self.table.rowCount()):
            cb_code = self.table.cellWidget(r, 0)
            if cb_code and cb_code.currentData() == match.get('id'):
                le_qty = self.table.cellWidget(r, 3)
                curr_qty_str = le_qty.text().strip() or '0'
                try:
                    qty = float(curr_qty_str) + 1
                except ValueError:
                    qty = 1
                le_qty.setText(str(qty))
                self._merge_duplicates()
                return

        self.add_empty_row()
        last_row = self.table.rowCount() - 1
        cb_code = self.table.cellWidget(last_row, 0)
        idx = cb_code.findData(match.get('id'))
        cb_code.setCurrentIndex(idx)
        le_qty = self.table.cellWidget(last_row, 3)
        le_qty.setText('1')

    def remove_row(self, cell_widget):
        for i in range(self.table.rowCount()):
            if self.table.cellWidget(i, 4) is cell_widget:
                self.table.removeRow(i)
                break

        if self.table.rowCount() == 0:
            self.add_empty_row()
        else:
            last_cb = self.table.cellWidget(self.table.rowCount() - 1, 0)
            if last_cb and last_cb.currentData():
                self.add_empty_row()

    def save_receipt(self, is_draft=False):
        wh_id = self.cb_warehouse.currentData()
        if not wh_id:
            QMessageBox.warning(self, 'خطأ', 'يجب اختيار مستودع التخزين.')
            return

        items_payload = []
        for r in range(self.table.rowCount()):
            cb_code = self.table.cellWidget(r, 0)
            cb_unit = self.table.cellWidget(r, 2)
            le_qty = self.table.cellWidget(r, 3)

            item_id = cb_code.currentData() if cb_code else None
            if not item_id:
                continue

            unit_id = cb_unit.currentData() if cb_unit else None
            if not unit_id:
                QMessageBox.warning(self, 'خطأ', 'يجب اختيار الوحدة في السطر ' + str(r + 1))
                return

            qty_text = le_qty.text().strip() if le_qty else ''
            try:
                qty = float(qty_text)
            except ValueError:
                QMessageBox.warning(self, 'خطأ', 'الكمية غير صالحة في السطر ' + str(r + 1))
                return

            cylinder_action = cb_code.property('cylinder_action')

            item_row = {
                'item_id': item_id,
                'warehouse_id': wh_id,
                'unit_id': unit_id,
                'quantity': qty,
            }
            if cylinder_action:
                item_row['cylinder_action'] = cylinder_action
            items_payload.append(item_row)

        if not items_payload:
            QMessageBox.warning(self, 'خطأ', 'القائمة فارغة.')
            return

        sup_id = self.cb_supplier.currentData()
        if not sup_id:
            QMessageBox.warning(self, 'خطأ', 'الرجاء اختيار الجهة الموردة.')
            return

        payload = {
            'reference_no': self.le_ref.text().strip(),
            'movement_date': self.dt_date.date().toString(Qt.DateFormat.ISODate),
            'supplier_id': sup_id,
            'notes': self.le_notes.text().strip(),
            'inspection_committee': self.le_insp_committee.text().strip(),
            'inspection_supervision': self.le_supervision.text().strip(),
            'inspection_audit': self.le_audit.text().strip(),
            'inspection_report_no': self.le_insp_report.text().strip(),
            'items': items_payload,
            'status': 'DRAFT' if is_draft else 'COMPLETED',
        }

        if not is_draft:
            reply = QMessageBox.question(
                self, 'تأكيد التوريد',
                'هل أنت متأكد من حفظ سند التوريد النهائي؟\n'
                'سيتم إضافة الكميات إلى المستودع ولا يمكن التراجع عن هذا الإجراء.'
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        ok, msg = self.api_service.receive_stock_bulk(payload)
        if ok:
            if is_draft:
                QMessageBox.information(
                    self, 'مسودة محفوظة',
                    'تم حفظ المسودة بنجاح (لم يتم التأثير على الرصيد). يمكنك العودة إليها من تبويبة المسودات.'
                )
            else:
                QMessageBox.information(self, 'بحمد الله', 'تم استلام الكميات وإضافتها للرصيد بنجاح.')

            self.table.setRowCount(0)
            self.add_empty_row()
            self.le_notes.clear()
            self.le_insp_committee.clear()
            self.le_supervision.clear()
            self.le_audit.clear()
            self.le_insp_report.clear()
            self.cb_warehouse.setCurrentIndex(0)
            self.cb_supplier.setCurrentIndex(0)
            self._generate_next_reference()
        else:
            QMessageBox.critical(self, 'خطأ', str(msg))

    def _print_voucher(self):
        rows = []
        for r in range(self.table.rowCount()):
            cb_code = self.table.cellWidget(r, 0)
            cb_unit = self.table.cellWidget(r, 2)
            le_qty = self.table.cellWidget(r, 3)
            if cb_code and cb_code.currentData():
                rows.append((
                    cb_code.currentText(),
                    cb_unit.currentText() if cb_unit else '',
                    le_qty.text() if le_qty else '',
                ))

        if not rows:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد أصناف للطباعة.')
            return

        master = {
            'warehouse': self.cb_warehouse.currentText(),
            'supplier': self.cb_supplier.currentText(),
            'ref': self.le_ref.text(),
            'date': self.dt_date.date().toString(Qt.DateFormat.ISODate),
            'committee': self.le_insp_committee.text(),
            'supervision': self.le_supervision.text(),
            'audit': self.le_audit.text(),
            'report_no': self.le_insp_report.text(),
            'notes': self.le_notes.text(),
        }

        print_receive_voucher(rows, master, self)

    def _import_from_excel(self):
        df = import_excel_to_dataframe(self)
        if df is None:
            return

        self.table.setRowCount(0)

        for _, row in df.iterrows():
            code = str(row.get('كود الصنف', '')).strip()
            qty = str(row.get('الكمية', '')).strip()
            if not code:
                continue

            self.add_empty_row()
            r = self.table.rowCount() - 1
            cb_code = self.table.cellWidget(r, 0)
            idx = cb_code.findText(code, Qt.MatchFlag.MatchContains)
            cb_code.setCurrentIndex(idx)

            le_qty = self.table.cellWidget(r, 3)
            le_qty.setText(qty)

        QMessageBox.information(self, 'نجاح', 'تم استيراد ' + str(len(df)) + ' سطر من الملف.')

    def _reset_form(self):
        """مسح النموذج لسند جديد."""
        self.table.setRowCount(0)
        self.le_notes.clear()
        self.le_insp_committee.clear()
        self.le_supervision.clear()
        self.le_audit.clear()
        self.le_insp_report.clear()
        self.cb_warehouse.setCurrentIndex(0)
        self.cb_supplier.setCurrentIndex(0)
        self._generate_next_reference()
        if self._items_data:
            self.add_empty_row()

    def _filter_history(self, text):
        """فلتر جدول السجل التاريخي."""
        text = text.strip().lower()
        for r in range(self.tbl_history.rowCount()):
            show = not text
            match = False
            for c in range(self.tbl_history.columnCount()):
                it = self.tbl_history.item(r, c)
                if it and text in it.text().lower():
                    match = True
                    break
            self.tbl_history.setRowHidden(r, not (show or match))
