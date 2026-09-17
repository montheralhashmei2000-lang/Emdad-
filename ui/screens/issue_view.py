from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QGridLayout, QFormLayout, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QMessageBox, QDateEdit, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QSpinBox, QTabWidget, QRadioButton, QButtonGroup, QScrollArea, QFrame, QSizePolicy, QStackedWidget, QTabBar, QInputDialog)
from PyQt6.QtCore import Qt, QDate
from ..api_service import ApiService
from ..theme import make_header_label
from ..excel_helper import export_table_to_excel
from ..print_helper import print_issue_voucher, print_issue_with_receipt
from .voucher_dialog import VoucherDetailsDialog
import re


class IssueFormTab(QWidget):
    """Form-only tab for issuing stock — no history/drafts (those are shared in IssueView)."""

    def __init__(self, parent, api_service: ApiService | None = None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()
        self._items_data = []
        self._entitlements = {}
        self._current_strength = 0
        self._units_data = []
        self._facilities_data = []
        self._updating_unit = False
        self._init_ui()

    def _init_ui(self):
        self._build_form_tab()

    def _build_form_tab(self):
        main_v = QVBoxLayout(self)
        main_v.setContentsMargins(10, 10, 10, 10)
        main_v.setSpacing(10)

        master_card = QWidget()
        master_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        master_card.setObjectName('card')
        master_card.setStyleSheet('QWidget#card { background: white; border-radius: 6px; border: 1px solid #ddd; }')

        grid = QGridLayout(master_card)
        grid.setSpacing(6)
        grid.setContentsMargins(10, 8, 10, 8)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(5, 1)

        H = 28

        self.cb_warehouse = QComboBox()
        self.cb_warehouse.setFixedHeight(H)
        self.cb_warehouse.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.r_ben = QRadioButton('وحدة')
        self.r_facility = QRadioButton('مطبخ/فرن')
        self.r_custom = QRadioButton('استثنائي')
        self.r_multi = QRadioButton('وحدات متعددة')
        self.r_ben.setChecked(True)

        self.target_group = QButtonGroup()
        self.target_group.addButton(self.r_ben, 0)
        self.target_group.addButton(self.r_facility, 1)
        self.target_group.addButton(self.r_custom, 2)
        self.target_group.addButton(self.r_multi, 3)

        target_group_widget = QWidget(); target_group_widget.setFixedHeight(H)
        target_group_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        tg_lay = QHBoxLayout(target_group_widget)
        tg_lay.setContentsMargins(0, 0, 0, 0)
        tg_lay.setSpacing(8)

        tg_lay.addWidget(self.r_ben)
        tg_lay.addWidget(self.r_facility)
        tg_lay.addWidget(self.r_custom)
        tg_lay.addWidget(self.r_multi)
        tg_lay.addStretch()

        self.cb_parent_unit = QComboBox()
        self.cb_parent_unit.setFixedHeight(H)
        self.cb_parent_unit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cb_parent_unit.currentIndexChanged.connect(self._on_parent_unit_changed)

        self.cb_ben_unit = QComboBox()
        self.cb_ben_unit.setFixedHeight(H)
        self.cb_ben_unit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cb_ben_unit.currentIndexChanged.connect(self._on_unit_changed)

        self.cb_facility = QComboBox()
        self.cb_facility.setFixedHeight(H)
        self.cb_facility.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.cb_facility.currentIndexChanged.connect(self._on_facility_changed)

        self.le_custom_recipient = QLineEdit()
        self.le_custom_recipient.setFixedHeight(H)
        self.le_custom_recipient.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.le_custom_recipient.setPlaceholderText('اسم المستلم (للاستثناءات) ..')

        self.lbl_strength = QLineEdit('0')
        self.lbl_strength.setReadOnly(True)
        self.lbl_strength.setStyleSheet('background-color: #f0f0f0; color: #155724; font-weight: bold;')
        self.lbl_strength.setFixedHeight(H)
        self.lbl_strength.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.dt_strength_date = QDateEdit()
        self.dt_strength_date.setCalendarPopup(True)
        self.dt_strength_date.setDate(QDate.currentDate())
        self.dt_strength_date.setFixedHeight(H)
        self.dt_strength_date.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.dt_strength_date.dateChanged.connect(self._fetch_strength)

        self.target_lbl_stack = QStackedWidget()
        self.target_lbl_stack.setFixedHeight(H)

        lbl1 = QLabel('الوحدة الفرعية:'); lbl1.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        lbl2 = QLabel('المطبخ/الفرن:'); lbl2.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        lbl3 = QLabel('اسم المستلم:'); lbl3.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.target_lbl_stack.addWidget(lbl1)
        self.target_lbl_stack.addWidget(lbl2)
        self.target_lbl_stack.addWidget(lbl3)

        self.target_input_stack = QStackedWidget(); self.target_input_stack.setFixedHeight(H)
        self.target_input_stack.addWidget(self.cb_ben_unit)
        self.target_input_stack.addWidget(self.cb_facility)
        self.target_input_stack.addWidget(self.le_custom_recipient)
        self.target_input_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        def _on_target_idx_changed(btn_id):
            self.target_lbl_stack.setCurrentIndex(btn_id)
            self.target_input_stack.setCurrentIndex(btn_id)
            self._on_target_type_changed(btn_id)

        self.target_group.idToggled.connect(lambda b_id, checked: _on_target_idx_changed(b_id) if checked else None)

        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.dt_date.setFixedHeight(H)
        self.dt_date.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.sp_days = QSpinBox()
        self.sp_days.setRange(1, 1000)
        self.sp_days.setValue(1)
        self.sp_days.setFixedHeight(H)
        self.sp_days.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.le_ref = QLineEdit()
        self.le_ref.setFixedHeight(H)
        self.le_ref.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.le_notes = QLineEdit()
        self.le_notes.setFixedHeight(H)
        self.le_notes.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.lbl_next_issue = QLineEdit('—')
        self.lbl_next_issue.setReadOnly(True)
        self.lbl_next_issue.setStyleSheet('background-color: #fff3cd; color: #856404; font-weight: bold; border: 1px solid #ffc107; border-radius: 4px; padding: 2px 6px;')
        self.lbl_next_issue.setFixedHeight(H)
        self.lbl_next_issue.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        grid.addWidget(QLabel('توجيه الصرف من:'), 0, 0)
        grid.addWidget(self.cb_warehouse, 0, 1)
        grid.addWidget(QLabel('نوع الصرف:'), 0, 2)
        grid.addWidget(target_group_widget, 0, 3)
        grid.addWidget(QLabel('المرجع/السند:'), 0, 4)
        grid.addWidget(self.le_ref, 0, 5)

        grid.addWidget(QLabel('الوحدة الرئيسية:'), 1, 0)
        grid.addWidget(self.cb_parent_unit, 1, 1)
        grid.addWidget(self.target_lbl_stack, 1, 2)
        grid.addWidget(self.target_input_stack, 1, 3)
        grid.addWidget(QLabel('تاريخ الصرف:'), 1, 4)
        grid.addWidget(self.dt_date, 1, 5)

        grid.addWidget(QLabel('تاريخ إلحاق القوة:'), 2, 0)
        grid.addWidget(self.dt_strength_date, 2, 1)
        grid.addWidget(QLabel('إجمالي القوة:'), 2, 2)
        grid.addWidget(self.lbl_strength, 2, 3)
        grid.addWidget(QLabel('مدة الإعاشة (أيام):'), 2, 4)
        grid.addWidget(self.sp_days, 2, 5)

        grid.addWidget(QLabel('ملاحظات:'), 3, 0)
        grid.addWidget(self.le_notes, 3, 1, 1, 3)

        self.lbl_next_issue_title = QLabel('موعد الصرف القادم:')
        grid.addWidget(self.lbl_next_issue_title, 3, 4)
        grid.addWidget(self.lbl_next_issue, 3, 5)

        main_v.addWidget(master_card)

        btn_bar = QHBoxLayout()

        btn_save = QPushButton('تنفيذ أمر الصرف')
        btn_save.setObjectName('danger_btn')
        btn_save.setFixedHeight(H)
        btn_save.clicked.connect(lambda: self.save_issue(move_status='COMPLETED'))

        btn_send_order = QPushButton('إرسال إشعار للمستودع')
        btn_send_order.setStyleSheet('background-color: #2980B9; color: white; font-weight: bold;')
        btn_send_order.setFixedHeight(H)
        btn_send_order.clicked.connect(lambda: self.save_issue(move_status='ORDER'))

        btn_draft = QPushButton('حفظ كمسودة')
        btn_draft.setStyleSheet('background-color: #f39c12; color: white;')
        btn_draft.setFixedHeight(H)
        btn_draft.clicked.connect(lambda: self.save_issue(move_status='DRAFT'))

        btn_reset = QPushButton('سند جديد')
        btn_reset.setFixedHeight(H)
        btn_reset.clicked.connect(self._reset_form)

        btn_bar.addWidget(btn_save)
        btn_bar.addWidget(btn_send_order)
        btn_bar.addWidget(btn_draft)
        btn_bar.addWidget(btn_reset)
        btn_bar.addStretch()

        scan_lay = QHBoxLayout(); scan_lay.setSpacing(4)
        scan_lay.addWidget(QLabel('باركوود 🏷️:'))

        self.le_barcode = QLineEdit()
        self.le_barcode.setPlaceholderText('مرر قارئ الباركود..')
        self.le_barcode.setStyleSheet('padding: 3px; border: 2px solid #C5A028; border-radius: 4px;')
        self.le_barcode.setFixedHeight(H)
        self.le_barcode.returnPressed.connect(self._on_barcode_scanned)

        scan_lay.addWidget(self.le_barcode)
        btn_bar.addLayout(scan_lay)

        main_v.addLayout(btn_bar)

        self._is_multi_unit_mode = False

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(['كود', 'اسم الصنف', 'الوحدة المستفيدة', 'وحدة القياس', 'الكمية', 'ملاحظة'])
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.verticalHeader().setMinimumSectionSize(30)
        self._apply_table_columns()

        main_v.addWidget(self.table)

        foot_bar = QHBoxLayout()

        btn_delete_row = QPushButton('❌ حذف السطر المحدد')
        btn_delete_row.setStyleSheet('color: #C0392B; font-weight: bold;')
        btn_delete_row.setFixedHeight(H)
        btn_delete_row.clicked.connect(self._delete_selected_row)

        btn_print_issue = QPushButton('🖨️ طباعة')
        btn_print_issue.clicked.connect(self._print_issue_only)

        btn_print_both = QPushButton('🖨️ طباعة صرف واستلام')
        btn_print_both.clicked.connect(self._print_issue_and_receipt)

        btn_export = QPushButton('📥 تصدير')
        btn_export.clicked.connect(lambda: export_table_to_excel(self.table, self, 'Issue_Export.xlsx'))

        foot_bar.addWidget(btn_delete_row)
        foot_bar.addStretch()
        foot_bar.addWidget(btn_print_issue)
        foot_bar.addWidget(btn_print_both)
        foot_bar.addWidget(btn_export)

        user = getattr(self.parent(), 'current_user', None)
        if user:
            is_admin = user.get('role', '').strip().upper() == 'ADMIN'
            has_explicit = 'issues' in user.get('permissions', {})
            tp = (user.get('permissions') or {}).get('issues', {})
            tabs_p = tp.get('tabs', {})
            new_p = tabs_p.get('tab_new', {})

            if has_explicit:
                can_create = new_p.get('create', False)
                btn_save.setVisible(can_create)
                btn_send_order.setVisible(can_create)
                btn_draft.setVisible(can_create)

                can_print = new_p.get('print', False)
                btn_print_issue.setVisible(can_print)
                btn_print_both.setVisible(can_print)
                btn_export.setVisible(can_print)
            else:
                btn_save.setVisible(is_admin)
                btn_send_order.setVisible(is_admin)
                btn_draft.setVisible(is_admin)
                btn_print_issue.setVisible(is_admin)
                btn_print_both.setVisible(is_admin)
                btn_export.setVisible(is_admin)

        main_v.addLayout(foot_bar)

        self._update_end_date()
        self._reset_form()
        self._update_end_date()

    def _build_drafts_tab(self):
        layout = QVBoxLayout(self._tab_drafts)
        layout.setContentsMargins(10, 10, 10, 10)

        toolbar = QHBoxLayout()

        btn_refresh = QPushButton('تحديث 🔄')
        btn_refresh.clicked.connect(self._load_drafts)

        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tbl_drafts = QTableWidget(0, 7)
        self.tbl_drafts.setHorizontalHeaderLabels(['م', 'نوع السند', 'عدد الأصناف', 'الجهة المستفيدة', 'التاريخ', 'ملاحظة', 'المرجع'])
        self.tbl_drafts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_drafts.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_drafts.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_drafts.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        layout.addWidget(self.tbl_drafts)

        action_lay = QHBoxLayout()

        btn_view_draft = QPushButton('عرض السند 🖨️')
        btn_view_draft.setStyleSheet('background-color: #2980B9; color: white; padding: 8px 15px; font-weight: bold;')
        btn_view_draft.clicked.connect(self._view_selected_draft)

        btn_approve_draft = QPushButton('اعتماد وتسجيل ✅')
        btn_approve_draft.setStyleSheet('background-color: #2E6B35; color: white; padding: 8px 15px; font-weight: bold;')
        btn_approve_draft.clicked.connect(self._approve_selected_draft)

        btn_delete_draft = QPushButton('حذف ❌')
        btn_delete_draft.setStyleSheet('background-color: #C0392B; color: white; padding: 8px 15px; font-weight: bold;')
        btn_delete_draft.clicked.connect(self._delete_selected_draft)

        action_lay.addWidget(btn_view_draft)
        action_lay.addStretch()
        action_lay.addWidget(btn_approve_draft)
        action_lay.addWidget(btn_delete_draft)

        layout.addLayout(action_lay)

    def _load_drafts(self):
        self.tbl_drafts.setRowCount(0)

        wh_id = self.cb_warehouse.currentData()
        if not wh_id:
            return

        ok, drafts = self.api_service.get_drafts(warehouse_id=wh_id)

        if not (ok and drafts):
            return

        filtered = [d for d in drafts if d.get('movement_type') == 'OUT']

        groups = {}
        for m in filtered:
            c_at = m.get('created_at', '') or ''
            time_key = c_at[:16] if c_at else ''
            key = (m.get('reference_no', ''), m.get('movement_date', ''), time_key)

            if key not in groups:
                groups[key] = []

            groups[key].append(m)

        for i, (key, items_list) in enumerate(groups.items()):
            first = items_list[0]
            status = first.get('status', 'DRAFT')

            self.tbl_drafts.insertRow(i)

            item_idx = QTableWidgetItem(str(i + 1))
            item_idx.setData(Qt.ItemDataRole.UserRole, items_list)
            self.tbl_drafts.setItem(i, 0, item_idx)

            recipient = first.get('recipient_display') or first.get('beneficiary_unit', '') or ''

            if status == 'REJECTED':
                status_item = QTableWidgetItem('🔴 مرفوض')
                status_item.setForeground(Qt.GlobalColor.red)
            elif status == 'ORDER':
                status_item = QTableWidgetItem('توجيه للمستودع')
                status_item.setForeground(Qt.GlobalColor.blue)
            else:
                status_item = QTableWidgetItem('مسودة محلية')

            self.tbl_drafts.setItem(i, 1, status_item)
            self.tbl_drafts.setItem(i, 2, QTableWidgetItem(str(len(items_list))))
            self.tbl_drafts.setItem(i, 3, QTableWidgetItem(recipient))
            self.tbl_drafts.setItem(i, 4, QTableWidgetItem(first.get('movement_date', '')))

            notes_text = first.get('notes', '') or ''
            notes_item = QTableWidgetItem(notes_text)

            if status == 'REJECTED':
                notes_item.setForeground(Qt.GlobalColor.red)

            self.tbl_drafts.setItem(i, 5, notes_item)
            self.tbl_drafts.setItem(i, 6, QTableWidgetItem(first.get('reference_no', '') or ''))

    def _get_selected_draft_data(self):
        r = self.tbl_drafts.currentRow()

        if r < 0:
            QMessageBox.warning(self, 'تنبيه', 'يرجى تحديد مسودة من الجدول أولاً.')
            return

        item = self.tbl_drafts.item(r, 0)
        return item.data(Qt.ItemDataRole.UserRole)

    def _view_selected_draft(self):
        items_list = self._get_selected_draft_data()
        if not items_list:
            return

        first = items_list[0]

        wh_id = first.get('warehouse_id')
        if wh_id:
            idx = self.cb_warehouse.findData(wh_id)
            if idx >= 0:
                self.cb_warehouse.setCurrentIndex(idx)

        date_str = first.get('movement_date')
        if date_str:
            y, m, d = map(int, str(date_str)[:10].split('-'))
            self.dt_date.setDate(QDate(y, m, d))

        self.le_ref.setText(first.get('reference_no', '') or '')
        self.le_notes.setText(first.get('notes', '') or '')

        if first.get('soldier_count'):
            self.dt_strength_date.blockSignals(True)
            self._current_strength = first.get('soldier_count')
            self.lbl_strength.setText(str(self._current_strength))
            self.dt_strength_date.blockSignals(False)

        if first.get('duration_days'):
            self.sp_days.setValue(first.get('duration_days'))

        ben_id = first.get('beneficiary_unit_id')

        if not ben_id:
            self.target_group.button(2).setChecked(True)
            self.le_custom_recipient.setText(first.get('recipient_display') or '')
        else:
            idx_fac = self.cb_facility.findData(ben_id)

            if idx_fac >= 0:
                self.target_group.button(1).setChecked(True)
                self.cb_facility.setCurrentIndex(idx_fac)
            else:
                self.target_group.button(0).setChecked(True)
                idx_ben = self.cb_ben_unit.findData(ben_id)
                if idx_ben >= 0:
                    self.cb_ben_unit.setCurrentIndex(idx_ben)

        self.table.setRowCount(0)
        self.add_empty_row()

        for m in items_list:
            r = self.table.rowCount() - 1

            cb_code = self.table.cellWidget(r, 0)
            idx_code = cb_code.findData(m.get('item_id'))
            if idx_code >= 0:
                cb_code.setCurrentIndex(idx_code)

            cb_unit = self.table.cellWidget(r, 3)
            idx_unit = cb_unit.findData(m.get('unit_id'))
            if idx_unit >= 0:
                cb_unit.setCurrentIndex(idx_unit)

            le_qty = self.table.cellWidget(r, 4)
            le_qty.blockSignals(True)
            le_qty.setText(str(m.get('quantity', 0)))
            le_qty.blockSignals(False)

        self.tabs.setCurrentIndex(0)

    def _approve_selected_draft(self):
        items_list = self._get_selected_draft_data()
        if not items_list:
            return

        reply = QMessageBox.question(self, 'تأكيد الاعتماد', 'هل أنت متأكد من اعتماد المسودة وسحب الأرصدة الفعلية لكافة الأصناف؟', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        movement_ids = [m.get('id') for m in items_list]

        ok, result = self.api_service.approve_draft_bulk(movement_ids)

        if ok:
            QMessageBox.information(self, 'نجاح', 'تم اعتماد سند المسودة وصرف الرصيد بالكامل.')
        else:
            QMessageBox.critical(self, 'فشل الاعتماد', str(result))

        self._load_drafts()

    def _delete_selected_draft(self):
        items_list = self._get_selected_draft_data()
        if not items_list:
            return

        reply = QMessageBox.question(self, 'تأكيد الحذف', 'هل أنت متأكد من حذف هذا السند نهائياً كمسودة؟', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        success_count = 0

        for m in items_list:
            ok, res = self.api_service.delete_draft(m.get('id'))
            if ok:
                success_count += 1

        if success_count == len(items_list):
            QMessageBox.information(self, 'نجاح', 'تم الحذف بنجاح.')
            self._load_drafts()
            return

        QMessageBox.warning(self, 'تنبيه', f'تم حذف {success_count} من أصل {len(items_list)} أصناف. بعضها فشل.')
        self._load_drafts()

    def _build_history_tab(self):
        layout = QVBoxLayout(self._tab_history)
        layout.setContentsMargins(10, 10, 10, 10)

        filter_card = QWidget()
        filter_card.setObjectName('card')

        filter_lay = QHBoxLayout(filter_card)

        filter_lay.addWidget(QLabel('من تاريخ:'))

        self.h_dt_from = QDateEdit()
        self.h_dt_from.setCalendarPopup(True)
        self.h_dt_from.setDate(QDate.currentDate().addMonths(-1))
        filter_lay.addWidget(self.h_dt_from)

        filter_lay.addWidget(QLabel('إلى تاريخ:'))

        self.h_dt_to = QDateEdit()
        self.h_dt_to.setCalendarPopup(True)
        self.h_dt_to.setDate(QDate.currentDate())
        filter_lay.addWidget(self.h_dt_to)

        filter_lay.addWidget(QLabel('المستودع:'))

        self.h_cb_warehouse = QComboBox()
        self.h_cb_warehouse.setMinimumWidth(120)
        filter_lay.addWidget(self.h_cb_warehouse)

        filter_lay.addWidget(QLabel('الوحدة المستفيدة:'))

        self.h_cb_unit = QComboBox()
        self.h_cb_unit.setMinimumWidth(150)
        filter_lay.addWidget(self.h_cb_unit)

        filter_lay.addWidget(QLabel('رقم السند:'))

        self.h_le_ref = QLineEdit()
        self.h_le_ref.setPlaceholderText('بحث بالرقم...')
        self.h_le_ref.setMaximumWidth(150)
        filter_lay.addWidget(self.h_le_ref)

        btn_search = QPushButton('بحث 🔍')
        btn_search.clicked.connect(self._load_history)
        filter_lay.addWidget(btn_search)

        layout.addWidget(filter_card)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel('طريقة العرض:'))

        self.cb_history_view_mode = QComboBox()
        self.cb_history_view_mode.addItem('مفصل (كل الأصناف)', 'detailed')
        self.cb_history_view_mode.addItem('مجمّع (حسب السند)', 'grouped')
        self.cb_history_view_mode.currentIndexChanged.connect(self._load_history)
        toolbar.addWidget(self.cb_history_view_mode)

        btn_print_agg = QPushButton('🖨️ طباعة مجمع كميات')
        btn_print_agg.setStyleSheet('background-color: #8E44AD; color: white; font-weight: bold;')
        btn_print_agg.clicked.connect(self._print_aggregated_quantities)
        toolbar.addWidget(btn_print_agg)

        btn_export_h = QPushButton('📥 تصدير إكسيل')
        btn_export_h.clicked.connect(lambda: export_table_to_excel(self.tbl_history, self, 'Issue_History.xlsx'))
        toolbar.addWidget(btn_export_h)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tbl_history = QTableWidget(0, 8)
        self.tbl_history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_history.cellDoubleClicked.connect(self._on_history_double_click)
        layout.addWidget(self.tbl_history)

    def _on_tab_changed(self, index):
        if index == 1:
            self._load_drafts()
            return

        if index == 2:
            self.h_cb_unit.blockSignals(True)

            if self.h_cb_unit.count() <= 1:
                self.h_cb_unit.clear()
                self.h_cb_unit.addItem('الكل', None)

                for bu in self._units_data:
                    self.h_cb_unit.addItem(f"وحدة: {bu['code']} - {bu['name']}", f"u_{bu['id']}")

                for fac in getattr(self, '_facilities_data', []):
                    self.h_cb_unit.addItem(f"مطبخ/فرن: {fac['name']}", f"f_{fac['id']}")

            self.h_cb_unit.blockSignals(False)

            self.h_cb_warehouse.blockSignals(True)

            if self.h_cb_warehouse.count() <= 1:
                self.h_cb_warehouse.clear()
                self.h_cb_warehouse.addItem('الكل', None)

                for w in self._warehouses:
                    self.h_cb_warehouse.addItem(w['name'], w['id'])

            self.h_cb_warehouse.blockSignals(False)

            self._load_history()

    def _load_history(self):
        self.tbl_history.setRowCount(0)

        ok, movs = self.api_service.get_movements_filtered(movement_type='OUT', limit=2000)

        if not (ok and movs):
            return

        dt_from = self.h_dt_from.date().toString(Qt.DateFormat.ISODate)
        dt_to = self.h_dt_to.date().toString(Qt.DateFormat.ISODate)
        target_token = self.h_cb_unit.currentData()
        ref_search = self.h_le_ref.text().strip()
        wh_id = self.h_cb_warehouse.currentData()

        filtered = []

        for m in movs:
            d = m.get('movement_date', '')
            if d and (d < dt_from or d > dt_to):
                continue

            if wh_id and m.get('warehouse_id') != wh_id:
                continue

            if target_token:
                prefix, tid = target_token.split('_')
                tid = int(tid)

                if prefix == 'u':
                    if m.get('beneficiary_unit_id') != tid:
                        continue
                elif prefix == 'f':
                    if m.get('facility_id') != tid:
                        continue

            ref = m.get('reference_no', '') or ''
            if ref_search and ref_search not in ref:
                continue

            filtered.append(m)

        self._current_filtered_history = filtered

        mode = getattr(self, 'cb_history_view_mode', None)
        is_grouped = mode is not None and mode.currentData() == 'grouped'

        self._history_data_map = {}

        if is_grouped:
            self.tbl_history.setColumnCount(5)
            self.tbl_history.setHorizontalHeaderLabels(['التاريخ', 'رقم السند المرجعي', 'المستودع', 'الجهة المستفيدة', 'عدد الأصناف'])
            self.tbl_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            groups = {}
            for m in filtered:
                ref = m.get('reference_no', '')
                if not ref:
                    ref = str(m.get('id', ''))

                date_key = m.get('movement_date', '')
                group_key = f'{ref}_{date_key}'

                if group_key not in groups:
                    groups[group_key] = []

                groups[group_key].append(m)

            for i, (group_key, items) in enumerate(groups.items()):
                first = items[0]
                self._history_data_map[i] = items

                real_ref = first.get('reference_no', '') or str(first.get('id', ''))

                self.tbl_history.insertRow(i)
                self.tbl_history.setItem(i, 0, QTableWidgetItem(first.get('movement_date', '')))

                ref_item = QTableWidgetItem(real_ref)
                ref_item.setData(Qt.ItemDataRole.UserRole, real_ref)
                self.tbl_history.setItem(i, 1, ref_item)

                self.tbl_history.setItem(i, 2, QTableWidgetItem(first.get('warehouse_name', '')))

                recipient = first.get('recipient_display') or first.get('beneficiary_unit', '') or ''
                self.tbl_history.setItem(i, 3, QTableWidgetItem(recipient))
                self.tbl_history.setItem(i, 4, QTableWidgetItem(str(len(items))))
            return

        self.tbl_history.setColumnCount(8)
        self.tbl_history.setHorizontalHeaderLabels(['التاريخ', 'الصنف', 'المستودع', 'الكمية', 'الوحدة', 'الجهة المستفيدة', 'المرجع', 'إجراء'])
        self.tbl_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for i, m in enumerate(filtered):
            self._history_data_map[i] = [m]

            self.tbl_history.insertRow(i)
            self.tbl_history.setItem(i, 0, QTableWidgetItem(m.get('movement_date', '')))
            self.tbl_history.setItem(i, 1, QTableWidgetItem(m.get('item_name', '')))
            self.tbl_history.setItem(i, 2, QTableWidgetItem(m.get('warehouse_name', '')))
            self.tbl_history.setItem(i, 3, QTableWidgetItem(str(m.get('quantity', 0))))
            self.tbl_history.setItem(i, 4, QTableWidgetItem(m.get('unit_name', '')))

            recipient = m.get('recipient_display') or m.get('beneficiary_unit', '') or ''
            self.tbl_history.setItem(i, 5, QTableWidgetItem(recipient))

            ref_item = QTableWidgetItem(m.get('reference_no', '') or '')
            ref_item.setData(Qt.ItemDataRole.UserRole, m.get('reference_no', ''))
            self.tbl_history.setItem(i, 6, ref_item)

            btn_w = QWidget()
            btn_l = QHBoxLayout(btn_w)
            btn_l.setContentsMargins(2, 2, 2, 2)

            btn_view = QPushButton('عرض 🖨️')
            mov_data = m
            btn_view.clicked.connect(lambda md=mov_data: self._view_history_record(md))
            btn_l.addWidget(btn_view)

            self.tbl_history.setCellWidget(i, 7, btn_w)

    def _on_history_double_click(self, row, col):
        items = getattr(self, '_history_data_map', {}).get(row)
        if not items:
            return

        dlg = VoucherDetailsDialog('OUT', items, self)
        dlg.exec()

    def _view_history_record(self, mov):
        from ..print_helper import print_issue_with_receipt

        recipient = mov.get('recipient_display') or mov.get('beneficiary_unit', '') or ''

        master = {
            'warehouse': mov.get('warehouse_name', ''),
            'beneficiary': recipient,
            'strength': str(mov.get('soldier_count', '') or ''),
            'days': str(mov.get('duration_days', '') or ''),
            'start_date': mov.get('movement_date', ''),
            'end_date': '',
            'ref': mov.get('reference_no', '') or '',
            'notes': mov.get('notes', '') or '',
        }

        rows = [[str(1), mov.get('item_name', ''), str(mov.get('quantity', 0)), mov.get('unit_name', ''), '']]

        print_issue_with_receipt(self, master, rows)

    def _print_aggregated_quantities(self):
        filtered = getattr(self, '_current_filtered_history', [])

        if not filtered:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد بيانات للطباعة. يرجى البحث أولاً.')
            return

        agg_data = {}

        for m in filtered:
            item_name = m.get('item_name', '')
            unit_name = m.get('unit_name', '')
            qty = float(m.get('quantity', 0))

            key = (item_name, unit_name)

            if key not in agg_data:
                agg_data[key] = 0.0

            agg_data[key] += qty

        rows = []
        idx = 1

        for (item_name, unit_name), total_qty in agg_data.items():
            rows.append([str(idx), item_name, str(total_qty), unit_name, ''])
            idx += 1

        wh_name = self.h_cb_warehouse.currentText()

        if wh_name == 'الكل' or not wh_name:
            wh_name = 'جميع المستودعات'

        unit_name = self.h_cb_unit.currentText()

        if unit_name == 'الكل' or not unit_name:
            unit_name = 'جميع الوحدات المستفيدة'

        master = {
            'warehouse': wh_name,
            'unit': unit_name,
            'date_from': self.h_dt_from.date().toString(Qt.DateFormat.ISODate),
            'date_to': self.h_dt_to.date().toString(Qt.DateFormat.ISODate),
        }

        from ..print_helper import print_aggregated_report

        print_aggregated_report(self, master, rows, title='مجمّع كميات أوامر الصرف')

    def _setup_smart_completer(self, combo):
        from PyQt6.QtCore import QSortFilterProxyModel, QStringListModel

        completer = combo.completer()

        if completer:
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setCompletionMode(completer.CompletionMode.PopupCompletion)

    def _merge_duplicates(self):
        row = 0

        while row < self.table.rowCount():
            cb_code1 = self.table.cellWidget(row, 0)
            cb_ben1 = self.table.cellWidget(row, 2)
            cb_unit1 = self.table.cellWidget(row, 3)
            le_qty1 = self.table.cellWidget(row, 4)

            if not (cb_code1 and cb_unit1 and le_qty1):
                row += 1
                continue

            item_id1 = cb_code1.currentData()
            unit_id1 = cb_unit1.currentData()
            ben_id1 = cb_ben1.currentData() if cb_ben1 else None
            qty_text1 = le_qty1.text().strip()

            if not (item_id1 and unit_id1 and qty_text1):
                row += 1
                continue

            try:
                q1 = float(qty_text1)
            except ValueError:
                row += 1
                continue

            r2 = row + 1

            while r2 < self.table.rowCount():
                cb_code2 = self.table.cellWidget(r2, 0)
                cb_ben2 = self.table.cellWidget(r2, 2)
                cb_unit2 = self.table.cellWidget(r2, 3)
                le_qty2 = self.table.cellWidget(r2, 4)

                if not (cb_code2 and cb_unit2 and le_qty2):
                    r2 += 1
                    continue

                item_id2 = cb_code2.currentData()
                unit_id2 = cb_unit2.currentData()
                ben_id2 = cb_ben2.currentData() if cb_ben2 else None
                qty_text2 = le_qty2.text().strip()

                if item_id1 == item_id2 and unit_id1 == unit_id2 and ben_id1 == ben_id2 and qty_text2:
                    try:
                        q2 = float(qty_text2)
                        le_qty1.setText(str(q1 + q2))
                        q1 += q2
                        self.table.removeRow(r2)
                        continue
                    except ValueError:
                        pass

                r2 += 1

            row += 1

        last_row = self.table.rowCount() - 1

        if last_row < 0:
            self.add_empty_row()
            return

        cb = self.table.cellWidget(last_row, 0)

        if cb and cb.currentData() is not None:
            self.add_empty_row()
            return

    def load_data(self):
        curr_wh = self.cb_warehouse.currentData()
        curr_parent = self.cb_parent_unit.currentData()
        curr_ben = self.cb_ben_unit.currentData()
        curr_fac = self.cb_facility.currentData()
        curr_strength_date = self.dt_strength_date.date()

        if not self.le_ref.text().strip():
            self._generate_next_reference()

        ok, items = self.api_service.get_items()
        self._items_data = items if (ok and items) else []

        ok, ents = self.api_service.get_entitlements()
        self._entitlements = {e['item_id']: e for e in ents} if (ok and ents) else {}

        ok, whs = self.api_service.get_warehouses()

        self.cb_warehouse.clear()

        allowed = None
        if hasattr(self.parent(), 'current_user') and self.parent().current_user:
            allowed = self.parent().current_user.get('allowed_warehouses')

        if ok and whs:
            for wh in whs:
                if allowed and wh['id'] not in allowed:
                    continue

                self.cb_warehouse.addItem(f"{wh['code']} - {wh['name']}", wh['id'])

        self.cb_parent_unit.blockSignals(True)
        self.cb_ben_unit.blockSignals(True)

        ok, bunits = self.api_service.get_units()

        self.cb_parent_unit.clear()
        self.cb_ben_unit.clear()

        self._units_data = bunits if (ok and bunits) else []

        self.cb_parent_unit.addItem('الكل / لا يوجد', None)

        for bu in self._units_data:
            if bu.get('parent_id'):
                continue

            self.cb_parent_unit.addItem(f"{bu['code']} - {bu['name']}", bu['id'])

        self.cb_parent_unit.blockSignals(False)
        self.cb_ben_unit.blockSignals(False)

        ok, facs = self.api_service.get_facilities()

        self.cb_facility.clear()

        self._facilities_data = facs if (ok and facs) else []

        for fac in self._facilities_data:
            ftype = 'مطبخ' if fac.get('f_type') == 'KITCHEN' else 'فرن'
            self.cb_facility.addItem(f"{fac['name']} ({ftype})", fac['id'])

        if curr_wh is not None:
            idx = self.cb_warehouse.findData(curr_wh)
            if idx >= 0:
                self.cb_warehouse.setCurrentIndex(idx)

        if curr_parent is not None:
            self.cb_parent_unit.blockSignals(True)
            idx = self.cb_parent_unit.findData(curr_parent)
            if idx >= 0:
                self.cb_parent_unit.setCurrentIndex(idx)
            self.cb_parent_unit.blockSignals(False)

        if curr_ben is not None:
            self.cb_ben_unit.blockSignals(True)
            idx = self.cb_ben_unit.findData(curr_ben)
            if idx >= 0:
                self.cb_ben_unit.setCurrentIndex(idx)
            self.cb_ben_unit.blockSignals(False)

        if curr_fac is not None:
            idx = self.cb_facility.findData(curr_fac)
            if idx >= 0:
                self.cb_facility.setCurrentIndex(idx)

        self.dt_strength_date.blockSignals(True)
        self.dt_strength_date.setDate(curr_strength_date)
        self.dt_strength_date.blockSignals(False)

        self._on_target_type_changed(self.target_group.checkedId())
        self._on_unit_changed()

        if self.table.rowCount() == 0 and self._items_data:
            self.add_empty_row()

        if not hasattr(self, '_auto_refresh_timer'):
            from PyQt6.QtCore import QTimer

            self._auto_refresh_timer = QTimer(self)
            self._auto_refresh_timer.timeout.connect(self._refresh_items_silently)
            self._auto_refresh_timer.start(30000)

    def _refresh_items_silently(self):
        try:
            ok, items = self.api_service.get_items()

            if not (ok and items):
                return

            old_ids = {i['id'] for i in self._items_data}
            new_ids = {i['id'] for i in items}
            added = new_ids - old_ids

            if not added:
                return

            self._items_data = items

            new_items = [i for i in items if i['id'] in added]

            for r in range(self.table.rowCount()):
                cb_code = self.table.cellWidget(r, 0)
                cb_name = self.table.cellWidget(r, 1)

                if not cb_code:
                    continue
                if not cb_name:
                    continue

                cb_code.blockSignals(True)
                cb_name.blockSignals(True)

                for itm in new_items:
                    cb_code.addItem(itm['item_code'], itm['id'])
                    cb_name.addItem(itm['name'], itm['id'])

                cb_code.blockSignals(False)
                cb_name.blockSignals(False)
        except Exception:
            return

    def _on_parent_unit_changed(self):
        parent_id = self.cb_parent_unit.currentData()

        self.cb_ben_unit.blockSignals(True)
        self.cb_ben_unit.clear()

        for bu in self._units_data:
            if not parent_id or bu.get('parent_id') == parent_id:
                self.cb_ben_unit.addItem(f"{bu['code']} - {bu['name']}", bu['id'])

        self.cb_ben_unit.blockSignals(False)

        self._on_unit_changed()

        if self.table.rowCount() == 0:
            if self._items_data:
                self.add_empty_row()
                return
            return

    def _on_target_type_changed(self, id):
        if id == 0:
            self.cb_parent_unit.setVisible(True)
            self.cb_ben_unit.setVisible(True)
            self.cb_facility.setVisible(False)
            self.le_custom_recipient.setVisible(False)
            self.dt_strength_date.setEnabled(True)
            self.sp_days.setEnabled(True)
            self.lbl_next_issue_title.setVisible(True)
            self.lbl_next_issue.setVisible(True)
        elif id == 1:
            self.cb_parent_unit.setVisible(False)
            self.cb_ben_unit.setVisible(False)
            self.cb_facility.setVisible(True)
            self.le_custom_recipient.setVisible(False)
            self.dt_strength_date.setEnabled(True)
            self.sp_days.setEnabled(True)
            self.lbl_next_issue_title.setVisible(False)
            self.lbl_next_issue.setVisible(False)
            self._on_facility_changed()
        elif id == 2:
            self.cb_parent_unit.setVisible(False)
            self.cb_ben_unit.setVisible(False)
            self.cb_facility.setVisible(False)
            self.le_custom_recipient.setVisible(True)
            self.dt_strength_date.setEnabled(False)
            self.sp_days.setEnabled(False)
            self._current_strength = 0
            self.lbl_strength.setText('0')
            self.lbl_next_issue_title.setVisible(False)
            self.lbl_next_issue.setVisible(False)
        elif id == 3:
            self.cb_parent_unit.setVisible(False)
            self.cb_ben_unit.setVisible(False)
            self.cb_facility.setVisible(False)
            self.le_custom_recipient.setVisible(False)
            self.dt_strength_date.setEnabled(False)
            self.sp_days.setEnabled(False)
            self._current_strength = 0
            self.lbl_strength.setText('0')
            self.lbl_next_issue_title.setVisible(False)
            self.lbl_next_issue.setVisible(False)

        was_multi = self._is_multi_unit_mode
        self._is_multi_unit_mode = id == 3

        if was_multi != self._is_multi_unit_mode:
            self._apply_table_columns()

            self.table.setRowCount(0)

            if self._items_data:
                self.add_empty_row()
                return
            return

    def _apply_table_columns(self):
        header = self.table.horizontalHeader()

        if self._is_multi_unit_mode:
            self.table.setColumnHidden(2, False)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
            self.table.setColumnWidth(0, 90)
            self.table.setColumnWidth(2, 180)
            self.table.setColumnWidth(3, 100)
            self.table.setColumnWidth(4, 80)
            self.table.setColumnWidth(5, 180)
            return

        self.table.setColumnHidden(2, True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 90)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 200)

    def _delete_selected_row(self):
        row = self.table.currentRow()

        if row < 0:
            QMessageBox.warning(self, 'تنبيه', 'يرجى تحديد السطر المراد حذفه أولاً.')
            return

        cb_code = self.table.cellWidget(row, 0)

        if cb_code and cb_code.currentData():
            self.table.removeRow(row)
        else:
            self.table.removeRow(row)

        if self.table.rowCount() == 0:
            self.add_empty_row()
            return

        last_cb = self.table.cellWidget(self.table.rowCount() - 1, 0)

        if last_cb and last_cb.currentData():
            self.add_empty_row()

    def _on_unit_changed(self):
        if self.target_group.checkedId() != 0:
            return

        if self._updating_unit:
            return

        self._updating_unit = True
        try:
            self._do_unit_update()
        finally:
            self._updating_unit = False

    def _do_unit_update(self):
        unit_id = self.cb_ben_unit.currentData()

        if not unit_id:
            return

        self.dt_strength_date.blockSignals(True)

        ok, data = self.api_service.get_latest_strength(unit_id)

        if ok and data and data.get('strength_date'):
            y, m, d = map(int, data['strength_date'].split('-'))
            self.dt_strength_date.setDate(QDate(y, m, d))
            self._current_strength = data.get('total', 0)
            self.lbl_strength.setText(str(self._current_strength))
        else:
            self._current_strength = 0
            self.lbl_strength.setText('0')

        self.dt_strength_date.blockSignals(False)

        self._recalc_all_rows()

        self._update_next_issue_date(unit_id)

    def _update_next_issue_date(self, unit_id):
        try:
            ok, movs = self.api_service.get_movements_filtered(movement_type='OUT', limit=100, unit_id=unit_id)

            if not (ok and movs):
                self.lbl_next_issue.setText('لا يوجد صرف سابق')
                self.lbl_next_issue.setStyleSheet('background-color: #d4edda; color: #155724; font-weight: bold; border: 1px solid #28a745; border-radius: 4px; padding: 2px 6px;')
                return

            unit_movs = [m for m in movs if m.get('beneficiary_unit_id') == unit_id and m.get('status', '') == 'COMPLETED']

            if not unit_movs:
                self.lbl_next_issue.setText('لا يوجد صرف سابق')
                self.lbl_next_issue.setStyleSheet('background-color: #d4edda; color: #155724; font-weight: bold; border: 1px solid #28a745; border-radius: 4px; padding: 2px 6px;')
                return

            max_next_date = None

            for m in unit_movs:
                m_date_str = m.get('movement_date', '')
                duration = m.get('duration_days', 1) or 1

                if not m_date_str:
                    continue

                try:
                    y, mo, d = map(int, m_date_str[:10].split('-'))
                    n_date = QDate(y, mo, d).addDays(int(duration))

                    if not max_next_date or n_date > max_next_date:
                        max_next_date = n_date
                except Exception:
                    continue

            if max_next_date:
                today = QDate.currentDate()
                diff = today.daysTo(max_next_date)
                next_str = max_next_date.toString(Qt.DateFormat.ISODate)

                if diff < 0:
                    self.lbl_next_issue.setText(f'⚠️ متأخر! كان يجب الصرف في {next_str}')
                    self.lbl_next_issue.setStyleSheet('background-color: #f8d7da; color: #721c24; font-weight: bold; border: 1px solid #dc3545; border-radius: 4px; padding: 2px 6px;')
                    return

                if diff == 0:
                    self.lbl_next_issue.setText(f'📢 اليوم! موعد الصرف {next_str}')
                    self.lbl_next_issue.setStyleSheet('background-color: #fff3cd; color: #856404; font-weight: bold; border: 1px solid #ffc107; border-radius: 4px; padding: 2px 6px;')
                    return

                self.lbl_next_issue.setText(f'📅 {next_str} (بعد {diff} يوم)')
                self.lbl_next_issue.setStyleSheet('background-color: #d4edda; color: #155724; font-weight: bold; border: 1px solid #28a745; border-radius: 4px; padding: 2px 6px;')
                return

            self.lbl_next_issue.setText('—')
        except Exception:
            self.lbl_next_issue.setText('—')

    def _on_facility_changed(self):
        if self.target_group.checkedId() != 1:
            return

        fac_id = self.cb_facility.currentData()

        if not fac_id:
            return

        self.dt_strength_date.blockSignals(True)

        ok_subs, subs = self.api_service.get_facility_subscriptions(fac_id)

        total_str = 0
        latest_date = None

        if ok_subs and subs:
            for sub in subs:
                ok_s, data_s = self.api_service.get_latest_strength(sub['unit_id'])

                if not ok_s:
                    continue
                if not data_s:
                    continue
                if not data_s.get('strength_date'):
                    continue

                total_str += data_s.get('total', 0)

                if not latest_date or data_s['strength_date'] > latest_date:
                    latest_date = data_s['strength_date']

        if latest_date:
            y, m, d = map(int, latest_date.split('-'))
            self.dt_strength_date.setDate(QDate(y, m, d))

        self._current_strength = total_str
        self.lbl_strength.setText(str(self._current_strength))

        self.dt_strength_date.blockSignals(False)

        self._recalc_all_rows()

    def _generate_next_reference(self):
        ok, data = self.api_service.get_next_reference('ص')

        if ok and isinstance(data, dict):
            self.le_ref.setText(data.get('reference_no', 'ص-000001'))
            return

        self.le_ref.setText('ص-000001')

    def _fetch_strength(self):
        target_id = self.target_group.checkedId()

        if target_id == 2:
            return

        target_date = self.dt_strength_date.date().toString(Qt.DateFormat.ISODate)

        ok, data = self.api_service.get_strength_by_date(target_date)

        found_total = 0

        if ok and data:
            if target_id == 0:
                unit_id = self.cb_ben_unit.currentData()

                for s in data:
                    if s['unit_id'] == unit_id:
                        found_total = s['total']
                        break
            elif target_id == 1:
                fac_id = self.cb_facility.currentData()

                if fac_id:
                    ok_subs, subs = self.api_service.get_facility_subscriptions(fac_id)

                    if ok_subs and subs:
                        sub_unit_ids = [sub['unit_id'] for sub in subs]

                        for s in data:
                            if s['unit_id'] in sub_unit_ids:
                                found_total += s['total']

        self._current_strength = found_total
        self.lbl_strength.setText(str(found_total))

        self._recalc_all_rows()

    def _update_end_date(self):
        self._recalc_all_rows()

    def _recalc_all_rows(self):
        for r in range(self.table.rowCount()):
            cb_code = self.table.cellWidget(r, 0)

            if not cb_code:
                continue

            item_id = cb_code.currentData()

            if not item_id:
                continue

            self._fill_smart_qty(item_id, r)

    def _fill_smart_qty(self, item_id, row):
        if item_id not in self._entitlements or self._current_strength <= 0:
            return

        item = next((i for i in self._items_data if i['id'] == item_id), None)

        if not item or not item.get('units'):
            return

        largest_unit = max(item['units'], key=lambda u: u['conversion_factor'])

        cb_unit = self.table.cellWidget(row, 3)
        cb_unit.blockSignals(True)

        idx = cb_unit.findData(largest_unit['id'])

        if idx >= 0:
            cb_unit.setCurrentIndex(idx)

        cb_unit.blockSignals(False)

        self._recalc_row_if_changed(self.table.cellWidget(row, 0), cb_unit)

    def _recalc_row_if_changed(self, cb_code, cb_unit):
        item_id = cb_code.currentData()

        if item_id:
            if item_id not in self._entitlements or self._current_strength <= 0:
                return

        r = -1

        for i in range(self.table.rowCount()):
            if self.table.cellWidget(i, 0) == cb_code:
                r = i
                break

        if r == -1:
            return

        unit_id = cb_unit.currentData()

        if not unit_id:
            return

        ent = self._entitlements[item_id]; days = self.sp_days.value()

        qty_per_person_per_day = ent['qty_per_person'] / 30.0
        total_required_base = qty_per_person_per_day * self._current_strength * days

        item = next((i for i in self._items_data if i['id'] == item_id), None)

        if not item or not item.get('units'):
            return

        base_unit_factor = 1.0

        for u in item['units']:
            if u['id'] == ent['measure_unit_id']:
                base_unit_factor = u['conversion_factor']
                break

        standard_qty = total_required_base * base_unit_factor

        target_unit_factor = 1.0

        for u in item['units']:
            if u['id'] == unit_id:
                target_unit_factor = u['conversion_factor']
                break

        final_qty = standard_qty / target_unit_factor

        le_qty = self.table.cellWidget(r, 4)
        le_qty.setText(str(round(final_qty, 3)))

    def add_empty_row(self):
        idx = self.table.rowCount()
        self.table.insertRow(idx)

        cb_code = QComboBox()
        cb_code.setEditable(True)
        cb_code.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        cb_name = QComboBox()
        cb_name.setEditable(True)
        cb_name.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        cb_code.addItem('', None)
        cb_name.addItem('', None)

        for itm in self._items_data:
            cb_code.addItem(itm['item_code'], itm['id'])
            cb_name.addItem(itm['name'], itm['id'])

        cb_code.lineEdit().setPlaceholderText('الكود')
        cb_name.lineEdit().setPlaceholderText('اسم الصنف')

        self._setup_smart_completer(cb_code)
        self._setup_smart_completer(cb_name)

        cb_ben = QComboBox(); cb_ben.setEditable(True)
        cb_ben.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        cb_ben.addItem('', None)

        for bu in self._units_data:
            cb_ben.addItem(f"{bu['code']} - {bu['name']}", bu['id'])

        cb_ben.lineEdit().setPlaceholderText('اختر الوحدة...')

        self._setup_smart_completer(cb_ben)

        cb_unit = QComboBox()

        cb_unit.currentIndexChanged.connect(lambda index: self._recalc_row_if_changed(cb_code, cb_unit))

        le_qty = QLineEdit(); le_qty.setPlaceholderText('الكمية')

        le_notes = QLineEdit()
        le_notes.setPlaceholderText('ملاحظة...')

        def update_unit_and_add_row(index):
            cb_unit.blockSignals(True)
            cb_unit.clear()

            item_id = cb_code.itemData(index)

            if not item_id:
                cb_unit.blockSignals(False)
                return

            r = -1

            for i in range(self.table.rowCount()):
                if self.table.cellWidget(i, 0) == cb_code:
                    r = i
                    break

            selected_item = next((i for i in self._items_data if i['id'] == item_id), None)

            if selected_item:
                for u in selected_item.get('units', []):
                    cb_unit.addItem(u['unit_name'], u['id'])

                if selected_item.get('is_refillable'):
                    actions = ['استبدال', 'صرف ممتلئ', 'صرف فارغ', 'استهلاك داخلي']

                    chosen, ok = QInputDialog.getItem(self, 'نوع العملية', f"الصنف ({selected_item['name']}) قابل للتعبئة.\nاختر نوع العملية:", actions, 0, False)

                    if ok and chosen:
                        action_map = {'استبدال': 'EXCHANGE', 'صرف ممتلئ': 'ISSUE_FULL', 'صرف فارغ': 'ISSUE_EMPTY', 'استهلاك داخلي': 'CONSUME'}

                        cb_code.setProperty('cylinder_action', action_map.get(chosen))
                        le_notes.setText(f'[{chosen}] {le_notes.text()}')
                    else:
                        cb_code.setProperty('cylinder_action', None)
                else:
                    cb_code.setProperty('cylinder_action', None)

            cb_unit.blockSignals(False)

            if r != -1:
                self._fill_smart_qty(item_id, r)

            if r == self.table.rowCount() - 1:
                self.add_empty_row()
                return

        def on_code_changed(index):
            if index <= 0:
                return

            cb_name.blockSignals(True)
            cb_name.setCurrentIndex(index)
            cb_name.blockSignals(False)

            update_unit_and_add_row(index)

        def on_name_changed(index):
            if index <= 0:
                return

            cb_code.blockSignals(True)
            cb_code.setCurrentIndex(index)
            cb_code.blockSignals(False)

            update_unit_and_add_row(index)

        cb_code.currentIndexChanged.connect(on_code_changed)
        cb_name.currentIndexChanged.connect(on_name_changed)

        le_qty.editingFinished.connect(self._merge_duplicates)

        cb_unit.currentIndexChanged.connect(lambda: self._merge_duplicates())

        self.table.setCellWidget(idx, 0, cb_code)
        self.table.setCellWidget(idx, 1, cb_name)

        self.table.setCellWidget(idx, 2, cb_ben)
        self.table.setCellWidget(idx, 3, cb_unit)

        self.table.setCellWidget(idx, 4, le_qty)
        self.table.setCellWidget(idx, 5, le_notes)

    def _on_barcode_scanned(self):
        code = self.le_barcode.text().strip()
        self.le_barcode.clear()

        if not code:
            return

        match = None

        for itm in self._items_data:
            if itm.get('barcode') == code or itm['item_code'] == code:
                match = itm
                break

        if not match:
            QMessageBox.warning(self, 'تحذير', f'الباركود ({code}) غير معرّف!')
            return

        for r in range(self.table.rowCount()):
            cb_code = self.table.cellWidget(r, 0)

            if not cb_code:
                continue

            if cb_code.currentData() == match['id']:
                le_qty = self.table.cellWidget(r, 4)

                if le_qty:
                    curr_qty_str = le_qty.text() or '0'

                    try:
                        qty = float(curr_qty_str)
                        le_qty.setText(str(qty + 1))
                        self._merge_duplicates()
                    except ValueError:
                        return

                return

        last_row = self.table.rowCount() - 1

        if last_row < 0:
            self.add_empty_row()
            last_row = 0

        cb_code = self.table.cellWidget(last_row, 0)

        if cb_code and cb_code.currentData() is not None:
            self.add_empty_row()
            last_row += 1
            cb_code = self.table.cellWidget(last_row, 0)

        idx = cb_code.findData(match['id'])

        if idx >= 0:
            cb_code.setCurrentIndex(idx)

            le_qty = self.table.cellWidget(last_row, 4)

            if le_qty:
                le_qty.setText('1')

    def remove_row(self, cell_widget):
        for i in range(self.table.rowCount()):
            if self.table.cellWidget(i, 0) == cell_widget:
                self.table.removeRow(i)
                break

        if self._items_data:
            if self.table.rowCount() == 0:
                self.add_empty_row()
                return

            last_cb = self.table.cellWidget(self.table.rowCount() - 1, 0)

            if last_cb and last_cb.currentData():
                self.add_empty_row()

    def save_issue(self, move_status):
        wh_id = self.cb_warehouse.currentData()

        if not wh_id:
            QMessageBox.warning(self, 'خطأ', 'يجب اختيار مستودع الصرف.')
            return

        items_payload = []
        target_id = self.target_group.checkedId()

        for r in range(self.table.rowCount()):
            cb_code = self.table.cellWidget(r, 0); cb_unit = self.table.cellWidget(r, 3); le_qty = self.table.cellWidget(r, 4)

            item_id = cb_code.currentData()

            if not item_id:
                continue

            unit_id = cb_unit.currentData(); qty_text = le_qty.text()

            if not unit_id:
                QMessageBox.warning(self, 'خطأ', f'يجب اختيار الوحدة في السطر {r + 1}')
                return

            try:
                qty = float(qty_text)

                if qty <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, 'خطأ', f'الكمية غير صالحة في السطر {r + 1}')
                return

            cylinder_action = cb_code.property('cylinder_action') if cb_code else None

            item_entry = {'item_id': item_id, 'warehouse_id': wh_id, 'unit_id': unit_id, 'quantity': qty, 'cylinder_action': cylinder_action}

            if target_id == 3:
                cb_ben = self.table.cellWidget(r, 2)
                ben_id = cb_ben.currentData() if cb_ben else None

                if not ben_id:
                    QMessageBox.warning(self, 'خطأ', f'يجب اختيار الوحدة المستفيدة في السطر {r + 1}')
                    return

                item_entry['beneficiary_unit_id'] = ben_id

            le_notes = self.table.cellWidget(r, 5)

            if le_notes and le_notes.text().strip():
                item_entry['notes'] = le_notes.text().strip()

            items_payload.append(item_entry)

        if not items_payload:
            QMessageBox.warning(self, 'خطأ', 'القائمة فارغة.')
            return

        if target_id == 0 and not self.cb_ben_unit.currentData():
            QMessageBox.warning(self, 'خطأ', 'يجب اختيار جهة مستفيدة.')
            return

        if target_id == 1 and not self.cb_facility.currentData():
            QMessageBox.warning(self, 'خطأ', 'يجب اختيار المطبخ أو الفرن.')
            return

        if target_id == 2 and not self.le_custom_recipient.text().strip():
            QMessageBox.warning(self, 'خطأ', 'يجب كتابة اسم جهة الصرف (المستلم).')
            return

        if target_id == 3:
            pass

        payload = {
            'reference_no': self.le_ref.text(),
            'movement_date': self.dt_date.date().toString(Qt.DateFormat.ISODate),
            'notes': self.le_notes.text(),
            'items': items_payload,
            'beneficiary_unit_id': self.cb_ben_unit.currentData() if target_id == 0 else None,
            'facility_id': self.cb_facility.currentData() if target_id == 1 else None,
            'custom_recipient': self.le_custom_recipient.text().strip() if target_id == 2 else None,
            'status': move_status,
            'officer_count': 0,
            'soldier_count': self._current_strength,
            'duration_days': self.sp_days.value(),
        }

        if move_status == 'COMPLETED':
            reply = QMessageBox.question(self, 'تأكيد الصرف', 'هل أنت متأكد من تنفيذ أمر الصرف؟\nهذا الإجراء سيخصم الكميات من المستودع مباشرة.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

            if reply != QMessageBox.StandardButton.Yes:
                return

        ok, msg = self.api_service.issue_stock_bulk(payload)

        if not ok:
            QMessageBox.critical(self, 'فشل الصرف', str(msg))
            return

        if move_status == 'ORDER':
            QMessageBox.information(self, 'تم إرسال الأمر', 'تم إرسال أمر التوجيه بنجاح للمستودع (في انتظار التنفيذ من أمين المخزن).')
        elif move_status == 'DRAFT':
            QMessageBox.information(self, 'مسودة محفوظة', 'تم حفظ المسودة المحلية بنجاح، يمكنك العودة لها لاحقاً.')
        else:
            QMessageBox.information(self, 'عملية ناجحة', 'تم تنفيذ عملية الصرف وخصم الكميات من العهدة بنجاح.')

        self._reset_form()

    def _reset_form(self):
        self.table.setRowCount(0)
        self.add_empty_row()

        self.le_notes.clear()
        self.le_custom_recipient.clear()

        if self.cb_ben_unit.count() > 0:
            self.cb_ben_unit.setCurrentIndex(-1)

        if self.cb_facility.count() > 0:
            self.cb_facility.setCurrentIndex(-1)

        self.dt_date.setDate(QDate.currentDate())
        self.sp_days.setValue(1)

        self._generate_next_reference()

    def _get_print_data(self):
        target_id = self.target_group.checkedId()
        rows = []

        for r in range(self.table.rowCount()):
            cb_code = self.table.cellWidget(r, 0)
            cb_unit = self.table.cellWidget(r, 3)
            le_qty = self.table.cellWidget(r, 4)

            if not (cb_code and cb_code.currentData()):
                continue

            le_notes_w = self.table.cellWidget(r, 5)
            note_text = le_notes_w.text().strip() if le_notes_w else ''

            if target_id == 3:
                cb_ben = self.table.cellWidget(r, 2)
                ben_text = cb_ben.currentText().split(' - ', 1)[-1] if (cb_ben and cb_ben.currentData()) else ''

                rows.append([str(r + 1), self.table.cellWidget(r, 1).currentText(), le_qty.text(), cb_unit.currentText(), ben_text, note_text])
            else:
                rows.append([str(r + 1), self.table.cellWidget(r, 1).currentText(), le_qty.text(), cb_unit.currentText(), note_text])

        if target_id == 0:
            beneficiary_name = self.cb_ben_unit.currentText().split(' - ', 1)[-1]
        elif target_id == 1:
            beneficiary_name = f'مطبخ/فرن: {self.cb_facility.currentText()}'
        elif target_id == 3:
            beneficiary_name = 'صرف لوحدات متعددة'
        else:
            beneficiary_name = f'مستلم استثنائي: {self.le_custom_recipient.text()}'

        master = {
            'warehouse': self.cb_warehouse.currentText().split(' - ', 1)[-1],
            'beneficiary': beneficiary_name,
            'strength': self.lbl_strength.text() if target_id == 0 else '-',
            'days': str(self.sp_days.value()) if target_id == 0 else '-',
            'start_date': self.dt_date.date().toString(Qt.DateFormat.ISODate),
            'end_date': self.dt_strength_date.date().addDays(self.sp_days.value() - 1).toString(Qt.DateFormat.ISODate) if target_id == 0 else '-',
            'ref': self.le_ref.text(),
            'notes': self.le_notes.text(),
            'is_multi_unit': target_id == 3,
        }

        return (master, rows)

    def _print_issue_only(self):
        master, rows = self._get_print_data()

        if not rows:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد أصناف للطباعة.')
            return

        print_issue_voucher(self, master, rows)

    def _print_issue_and_receipt(self):
        master, rows = self._get_print_data()

        if not rows:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد أصناف للطباعة.')
            return

        print_issue_with_receipt(self, master, rows)


class IssueView(QWidget):
    """Tab manager: [سند صرف ...] [سجل الصادرات] [المسودات] [➕ فتح سند جديد]"""

    _form_counter = 0

    def __init__(self, parent=None, api_service: ApiService | None = None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()
        self._units_data = []
        self._facilities_data = []
        self._history_data_map = {}
        self._init_ui()

    def _first_form(self):
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)

            if isinstance(w, IssueFormTab):
                return w

        return None

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)

        layout.addWidget(self.tabs)

        self._add_form_tab('سند صرف')

        self._tab_history = QWidget()
        self.tabs.addTab(self._tab_history, 'سجل الصادرات')
        self._build_history_tab()

        self._tab_drafts = QWidget()
        self.tabs.addTab(self._tab_drafts, 'المسودات')
        self._build_drafts_tab()

        self.tabs.addTab(QWidget(), '➕ فتح سند جديد')

        bar = self.tabs.tabBar()

        for fi in range(self.tabs.count() - 3, self.tabs.count()):
            bar.setTabButton(fi, QTabBar.ButtonPosition.RightSide, None)
            bar.setTabButton(fi, QTabBar.ButtonPosition.LeftSide, None)

        user = getattr(self.parent(), 'current_user', None)

        if user:
            is_admin = user.get('role', '').strip().upper() == 'ADMIN'
            has_explicit = 'issues' in user.get('permissions', {})
            self._tabs_perms = user.get('permissions', {}).get('issues', {}).get('tabs', {})
            self._is_admin = is_admin and not has_explicit

            if has_explicit:
                drafts_p = self._tabs_perms.get('tab_drafts', {})
                self.tabs.setTabVisible(self.tabs.indexOf(self._tab_drafts), drafts_p.get('view', False))

                hist_p = self._tabs_perms.get('tab_history', {})
                self.tabs.setTabVisible(self.tabs.indexOf(self._tab_history), hist_p.get('view', False))
            else:
                self.tabs.setTabVisible(self.tabs.indexOf(self._tab_drafts), is_admin)
                self.tabs.setTabVisible(self.tabs.indexOf(self._tab_history), is_admin)
        else:
            self._is_admin = False
            self._tabs_perms = {}

        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _add_form_tab(self, title='سند صرف'):
        IssueView._form_counter += 1

        new_form = IssueFormTab(parent=self.parent(), api_service=self.api_service)

        fixed = 3
        insert_idx = max(self.tabs.count() - fixed, 0)

        tab_title = f'{title} {IssueView._form_counter}' if IssueView._form_counter > 1 else title

        self.tabs.insertTab(insert_idx, new_form, tab_title)
        self.tabs.setCurrentIndex(insert_idx)

        new_form.load_data()

        return new_form

    def _close_tab(self, index):
        widget = self.tabs.widget(index)
        txt = self.tabs.tabText(index)

        if txt in ('سجل الصادرات', 'المسودات', '➕ فتح سند جديد'):
            return

        form_count = sum((1 for i in range(self.tabs.count()) if isinstance(self.tabs.widget(i), IssueFormTab)))

        if form_count <= 1:
            QMessageBox.warning(self, 'تنبيه', 'لا يمكن إغلاق آخر سند مفتوح.')
            return

        if isinstance(widget, IssueFormTab):
            self.tabs.removeTab(index)
            widget.deleteLater()
            return

        return

    def _on_tab_changed(self, index):
        if index < 0:
            return

        txt = self.tabs.tabText(index)

        if txt == '➕ فتح سند جديد':
            self._add_form_tab('سند صرف')
            return

        if txt == 'المسودات':
            self._load_drafts()
            return

        if txt == 'سجل الصادرات':
            self._populate_history_filter()
            self._load_history()
            return

    def _build_history_tab(self):
        layout = QVBoxLayout(self._tab_history)
        layout.setContentsMargins(10, 10, 10, 10)

        filter_card = QWidget(); filter_card.setObjectName('card')

        fl = QHBoxLayout(filter_card)

        fl.addWidget(QLabel('من تاريخ:'))

        self.h_dt_from = QDateEdit()
        self.h_dt_from.setCalendarPopup(True)
        self.h_dt_from.setDate(QDate.currentDate().addMonths(-1))
        fl.addWidget(self.h_dt_from)

        fl.addWidget(QLabel('إلى تاريخ:'))

        self.h_dt_to = QDateEdit()
        self.h_dt_to.setCalendarPopup(True)
        self.h_dt_to.setDate(QDate.currentDate())
        fl.addWidget(self.h_dt_to)

        fl.addWidget(QLabel('المستودع:'))

        self.h_cb_warehouse = QComboBox()
        self.h_cb_warehouse.setMinimumWidth(120)
        fl.addWidget(self.h_cb_warehouse)

        fl.addWidget(QLabel('الوحدة المستفيدة:'))

        self.h_cb_unit = QComboBox()
        self.h_cb_unit.setMinimumWidth(150)
        fl.addWidget(self.h_cb_unit)

        fl.addWidget(QLabel('رقم السند:'))

        self.h_le_ref = QLineEdit()
        self.h_le_ref.setPlaceholderText('بحث بالرقم...')

        self.h_le_ref.setMaximumWidth(150)
        fl.addWidget(self.h_le_ref)

        btn_search = QPushButton('بحث 🔍'); btn_search.clicked.connect(self._load_history)

        fl.addWidget(btn_search)
        layout.addWidget(filter_card)

        toolbar = QHBoxLayout(); toolbar.addWidget(QLabel('طريقة العرض:'))

        self.cb_history_view_mode = QComboBox()

        self.cb_history_view_mode.addItem('مفصل (كل الأصناف)', 'detailed')
        self.cb_history_view_mode.addItem('مجمّع (حسب السند)', 'grouped')
        self.cb_history_view_mode.currentIndexChanged.connect(self._load_history)

        toolbar.addWidget(self.cb_history_view_mode)

        btn_print_agg = QPushButton('🖨️ طباعة مجمع كميات')
        btn_print_agg.setStyleSheet('background-color: #8E44AD; color: white; font-weight: bold;')
        btn_print_agg.clicked.connect(self._print_aggregated_quantities)

        toolbar.addWidget(btn_print_agg)

        btn_edit_ent = QPushButton('✏️ تعديل بيانات السند')
        btn_edit_ent.setStyleSheet('background-color: #E67E22; color: white; font-weight: bold;')
        btn_edit_ent.clicked.connect(self._edit_voucher_entitlement)

        toolbar.addWidget(btn_edit_ent)

        btn_exp = QPushButton('📥 تصدير إكسيل')
        btn_exp.clicked.connect(lambda: export_table_to_excel(self.tbl_history, self, 'Issue_History.xlsx'))

        toolbar.addWidget(btn_exp)

        if not getattr(self, '_is_admin', False):
            hp = getattr(self, '_tabs_perms', {}).get('tab_history', {})
            btn_exp.setVisible(hp.get('print', False))

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tbl_history = QTableWidget(0, 8)
        self.tbl_history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_history.cellDoubleClicked.connect(self._on_history_double_click)

        layout.addWidget(self.tbl_history)

    def _populate_history_filter(self):
        form = self._first_form()

        if form:
            self._units_data = form._units_data
            self._facilities_data = form._facilities_data

        self.h_cb_unit.blockSignals(True)

        if self.h_cb_unit.count() <= 1:
            self.h_cb_unit.clear()
            self.h_cb_unit.addItem('الكل', None)

            for bu in self._units_data:
                self.h_cb_unit.addItem(f"وحدة: {bu['code']} - {bu['name']}", f"u_{bu['id']}")

            for fac in self._facilities_data:
                self.h_cb_unit.addItem(f"مطبخ/فرن: {fac['name']}", f"f_{fac['id']}")

        self.h_cb_unit.blockSignals(False)

        self.h_cb_warehouse.blockSignals(True)

        if self.h_cb_warehouse.count() <= 1:
            self.h_cb_warehouse.clear()
            self.h_cb_warehouse.addItem('الكل', None)

            from ..api_service import ApiService

            ok, warehouses = self.api_service.get_warehouses()

            if ok:
                for w in warehouses:
                    self.h_cb_warehouse.addItem(w['name'], w['id'])

        self.h_cb_warehouse.blockSignals(False)

    def _load_history(self):
        self.tbl_history.setRowCount(0)

        ok, movs = self.api_service.get_movements_filtered(movement_type='OUT', limit=2000)

        if not (ok and movs):
            return

        dt_from = self.h_dt_from.date().toString(Qt.DateFormat.ISODate)
        dt_to = self.h_dt_to.date().toString(Qt.DateFormat.ISODate)
        target_token = self.h_cb_unit.currentData()
        ref_search = self.h_le_ref.text().strip()
        wh_id = self.h_cb_warehouse.currentData()

        filtered = []

        for m in movs:
            d = m.get('movement_date', '')
            if d and (d < dt_from or d > dt_to):
                continue

            if target_token:
                prefix, tid = target_token.split('_')
                tid = int(tid)

                if prefix == 'u':
                    if m.get('beneficiary_unit_id') != tid:
                        continue
                if prefix == 'f':
                    if m.get('facility_id') != tid:
                        continue

            ref = m.get('reference_no', '') or ''
            if ref_search and ref_search not in ref:
                continue

            if wh_id and m.get('warehouse_id') != wh_id:
                continue

            filtered.append(m)

        self._current_filtered_history = filtered

        is_grouped = self.cb_history_view_mode.currentData() == 'grouped'
        self._history_data_map = {}

        if is_grouped:
            self.tbl_history.setColumnCount(5)
            self.tbl_history.setHorizontalHeaderLabels(['التاريخ', 'رقم السند المرجعي', 'المستودع', 'الجهة المستفيدة', 'عدد الأصناف'])
            self.tbl_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            groups = {}
            for m in filtered:
                ref = m.get('reference_no', '') or str(m.get('id', ''))
                c_at = m.get('created_at', '')
                time_key = c_at[:16] if c_at else ''
                gk = f'{ref}_{time_key}'

                if gk not in groups:
                    groups[gk] = []

                groups[gk].append(m)

            for i, (gk, items) in enumerate(groups.items()):
                first = items[0]
                self._history_data_map[i] = items

                self.tbl_history.insertRow(i)
                self.tbl_history.setItem(i, 0, QTableWidgetItem(first.get('movement_date', '')))

                ri = QTableWidgetItem(first.get('reference_no', '') or str(first.get('id', '')))
                ri.setData(Qt.ItemDataRole.UserRole, ri.text())
                self.tbl_history.setItem(i, 1, ri)

                self.tbl_history.setItem(i, 2, QTableWidgetItem(first.get('warehouse_name', '')))

                recip = first.get('recipient_display') or first.get('beneficiary_unit', '') or ''
                self.tbl_history.setItem(i, 3, QTableWidgetItem(recip))
                self.tbl_history.setItem(i, 4, QTableWidgetItem(str(len(items))))

            return

        self.tbl_history.setColumnCount(8)
        self.tbl_history.setHorizontalHeaderLabels(['التاريخ', 'الصنف', 'المستودع', 'الكمية', 'الوحدة', 'الجهة المستفيدة', 'المرجع', 'إجراء'])
        self.tbl_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for i, m in enumerate(filtered):
            self._history_data_map[i] = [m]

            self.tbl_history.insertRow(i)
            self.tbl_history.setItem(i, 0, QTableWidgetItem(m.get('movement_date', '')))
            self.tbl_history.setItem(i, 1, QTableWidgetItem(m.get('item_name', '')))
            self.tbl_history.setItem(i, 2, QTableWidgetItem(m.get('warehouse_name', '')))
            self.tbl_history.setItem(i, 3, QTableWidgetItem(str(m.get('quantity', 0))))
            self.tbl_history.setItem(i, 4, QTableWidgetItem(m.get('unit_name', '')))

            recip = m.get('recipient_display') or m.get('beneficiary_unit', '') or ''
            self.tbl_history.setItem(i, 5, QTableWidgetItem(recip))

            ri = QTableWidgetItem(m.get('reference_no', '') or '')
            ri.setData(Qt.ItemDataRole.UserRole, m.get('reference_no', ''))
            self.tbl_history.setItem(i, 6, ri)

            bw = QWidget()
            bl = QHBoxLayout(bw)
            bl.setContentsMargins(2, 2, 2, 2)

            bv = QPushButton('عرض 🖨️')
            md = m

            bv.clicked.connect(lambda d=md: self._view_history_record(d))
            bl.addWidget(bv)

            self.tbl_history.setCellWidget(i, 7, bw)

    def _on_history_double_click(self, row, col):
        items = self._history_data_map.get(row)

        if not items:
            return

        dlg = VoucherDetailsDialog('OUT', items, self); dlg.exec()

    def _view_history_record(self, mov):
        from ..print_helper import print_issue_with_receipt

        recip = mov.get('recipient_display') or mov.get('beneficiary_unit', '') or ''

        start_date = mov.get('movement_date', '')
        duration = mov.get('duration_days', 0) or 0
        end_date = ''

        if start_date and duration:
            try:
                y, mo, d = map(int, start_date[:10].split('-'))
                end_date = QDate(y, mo, d).addDays(int(duration) - 1).toString(Qt.DateFormat.ISODate)
            except Exception:
                end_date = ''

        master = {
            'warehouse': mov.get('warehouse_name', ''),
            'beneficiary': recip,
            'strength': str(mov.get('soldier_count', '') or ''),
            'days': str(duration),
            'start_date': start_date,
            'end_date': end_date,
            'ref': mov.get('reference_no', '') or '',
            'notes': mov.get('notes', '') or '',
        }

        rows = [[str(1), mov.get('item_name', ''), str(mov.get('quantity', 0)), mov.get('unit_name', ''), '']]

        print_issue_with_receipt(self, master, rows)

    def _edit_voucher_entitlement(self):
        row = self.tbl_history.currentRow()

        if row < 0:
            QMessageBox.warning(self, 'تنبيه', 'يرجى تحديد سند من الجدول أولاً')
            return

        items = self._history_data_map.get(row, [])

        if not items:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد بيانات للسند المحدد')
            return

        first = items[0]
        ref = first.get('reference_no', '') or str(first.get('id', ''))

        from PyQt6.QtWidgets import QDialog, QFormLayout, QSpinBox, QDialogButtonBox

        dlg = QDialog(self)
        dlg.setWindowTitle(f'تعديل بيانات السند: {ref}')
        dlg.setMinimumWidth(380)

        form = QFormLayout(dlg)

        sp_soldiers = QSpinBox()
        sp_soldiers.setRange(0, 99999)
        sp_soldiers.setValue(int(first.get('soldier_count', 0) or 0))
        form.addRow('عدد القوة (أفراد):', sp_soldiers)

        sp_officers = QSpinBox()
        sp_officers.setRange(0, 99999)
        sp_officers.setValue(int(first.get('officer_count', 0) or 0))
        form.addRow('عدد الضباط:', sp_officers)

        sp_days = QSpinBox()
        sp_days.setRange(0, 365)
        sp_days.setValue(int(first.get('duration_days', 0) or 0))
        form.addRow('عدد الأيام:', sp_days)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        form.addRow(buttons)

        def do_save():
            payload = {'soldier_count': sp_soldiers.value(), 'officer_count': sp_officers.value(), 'duration_days': sp_days.value()}

            success_count = 0

            for m in items:
                mid = m.get('id')

                if not mid:
                    continue

                ok, _ = self.api_service.update_voucher_entitlement(mid, payload)

                if not ok:
                    continue

                success_count += 1

            if success_count > 0:
                QMessageBox.information(dlg, 'تم', f'تم تحديث {success_count} حركة بنجاح')
                dlg.accept()
                self._load_history()
                return

            QMessageBox.critical(dlg, 'خطأ', 'فشل التحديث')

        buttons.accepted.connect(do_save)
        buttons.rejected.connect(dlg.reject)

        dlg.exec()

    def _build_drafts_tab(self):
        layout = QVBoxLayout(self._tab_drafts); layout.setContentsMargins(10, 10, 10, 10)

        toolbar = QHBoxLayout()

        btn_r = QPushButton('تحديث 🔄'); btn_r.clicked.connect(self._load_drafts)

        toolbar.addWidget(btn_r)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.tbl_drafts = QTableWidget(0, 7)
        self.tbl_drafts.setHorizontalHeaderLabels(['م', 'نوع السند', 'عدد الأصناف', 'الجهة المستفيدة', 'التاريخ', 'ملاحظة', 'المرجع'])
        self.tbl_drafts.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_drafts.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_drafts.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_drafts.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        layout.addWidget(self.tbl_drafts)

        al = QHBoxLayout()

        bv = QPushButton('عرض السند 🖨️'); bv.setStyleSheet('background-color:#2980B9;color:white;padding:8px 15px;font-weight:bold;')

        bv.clicked.connect(self._view_selected_draft)
        al.addWidget(bv)
        al.addStretch()

        ba = QPushButton('اعتماد وتسجيل ✅'); ba.setStyleSheet('background-color:#2E6B35;color:white;padding:8px 15px;font-weight:bold;')

        ba.clicked.connect(self._approve_selected_draft)
        al.addWidget(ba)

        bd = QPushButton('حذف ❌'); bd.setStyleSheet('background-color:#C0392B;color:white;padding:8px 15px;font-weight:bold;')

        bd.clicked.connect(self._delete_selected_draft)
        al.addWidget(bd)

        layout.addLayout(al)

        if not getattr(self, '_is_admin', False):
            dp = getattr(self, '_tabs_perms', {}).get('tab_drafts', {})

            ba.setVisible(dp.get('approve', False))
            bd.setVisible(dp.get('delete', False))

    def _load_drafts(self):
        self.tbl_drafts.setRowCount(0)

        form = self._first_form()
        wh_id = form.cb_warehouse.currentData() if form else None

        if not wh_id:
            return

        ok, drafts = self.api_service.get_drafts(warehouse_id=wh_id)

        if not (ok and drafts):
            return

        filtered = [d for d in drafts if d.get('movement_type') == 'OUT']

        groups = {}
        for m in filtered:
            c_at = m.get('created_at', '') or ''; time_key = c_at[:16] if c_at else ''
            key = (m.get('reference_no', ''), m.get('movement_date', ''), time_key)

            if key not in groups:
                groups[key] = []

            groups[key].append(m)

        for i, (key, items_list) in enumerate(groups.items()):
            first = items_list[0]; status = first.get('status', 'DRAFT')

            self.tbl_drafts.insertRow(i)

            item_idx = QTableWidgetItem(str(i + 1))
            item_idx.setData(Qt.ItemDataRole.UserRole, items_list)
            self.tbl_drafts.setItem(i, 0, item_idx)

            recip = first.get('recipient_display') or first.get('beneficiary_unit', '') or ''

            if status == 'REJECTED':
                si = QTableWidgetItem('🔴 مرفوض')
                si.setForeground(Qt.GlobalColor.red)
            elif status == 'ORDER':
                si = QTableWidgetItem('توجيه للمستودع')
                si.setForeground(Qt.GlobalColor.blue)
            else:
                si = QTableWidgetItem('مسودة محلية')

            self.tbl_drafts.setItem(i, 1, si)
            self.tbl_drafts.setItem(i, 2, QTableWidgetItem(str(len(items_list))))
            self.tbl_drafts.setItem(i, 3, QTableWidgetItem(recip))
            self.tbl_drafts.setItem(i, 4, QTableWidgetItem(first.get('movement_date', '')))

            ni = QTableWidgetItem(first.get('notes', '') or '')

            if status == 'REJECTED':
                ni.setForeground(Qt.GlobalColor.red)

            self.tbl_drafts.setItem(i, 5, ni)
            self.tbl_drafts.setItem(i, 6, QTableWidgetItem(first.get('reference_no', '') or ''))

    def _get_selected_draft_data(self):
        r = self.tbl_drafts.currentRow()

        if r < 0:
            QMessageBox.warning(self, 'تنبيه', 'يرجى تحديد مسودة من الجدول أولاً.')
            return

        return self.tbl_drafts.item(r, 0).data(Qt.ItemDataRole.UserRole)

    def _view_selected_draft(self):
        items_list = self._get_selected_draft_data()

        if not items_list:
            return

        first = items_list[0]

        form = self._add_form_tab('مسودة')

        wh_id = first.get('warehouse_id')

        if wh_id:
            idx = form.cb_warehouse.findData(wh_id)

            if idx >= 0:
                form.cb_warehouse.setCurrentIndex(idx)

        ds = first.get('movement_date')

        if ds:
            y, mo, d = map(int, str(ds)[:10].split('-')); form.dt_date.setDate(QDate(y, mo, d))

        form.le_ref.setText(first.get('reference_no', '') or '')
        form.le_notes.setText(first.get('notes', '') or '')

        if first.get('soldier_count'):
            form._current_strength = first['soldier_count']
            form.lbl_strength.setText(str(form._current_strength))

        if first.get('duration_days'):
            form.sp_days.setValue(first['duration_days'])

        ben_id = first.get('beneficiary_unit_id')

        if not ben_id:
            form.target_group.button(2).setChecked(True)
            form.le_custom_recipient.setText(first.get('recipient_display') or '')
        else:
            idx_f = form.cb_facility.findData(ben_id)

            if idx_f >= 0:
                form.target_group.button(1).setChecked(True)
                form.cb_facility.setCurrentIndex(idx_f)
            else:
                form.target_group.button(0).setChecked(True)

                idx_b = form.cb_ben_unit.findData(ben_id)

                if idx_b >= 0:
                    form.cb_ben_unit.setCurrentIndex(idx_b)

        form.table.setRowCount(0)
        form.add_empty_row()

        for m in items_list:
            r = form.table.rowCount() - 1

            cc = form.table.cellWidget(r, 0); ic = cc.findData(m.get('item_id'))

            if ic >= 0:
                cc.setCurrentIndex(ic)

            cu = form.table.cellWidget(r, 3)
            iu = cu.findData(m.get('unit_id'))

            if iu >= 0:
                cu.setCurrentIndex(iu)

            lq = form.table.cellWidget(r, 4)
            lq.blockSignals(True)

            lq.setText(str(m.get('quantity', 0)))
            lq.blockSignals(False)

    def _approve_selected_draft(self):
        items_list = self._get_selected_draft_data()

        if not items_list:
            return

        reply = QMessageBox.question(self, 'تأكيد الاعتماد', 'هل أنت متأكد من اعتماد المسودة وسحب الأرصدة الفعلية؟', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        ids = [m.get('id') for m in items_list]

        ok, result = self.api_service.approve_draft_bulk(ids)

        if ok:
            QMessageBox.information(self, 'نجاح', 'تم اعتماد سند المسودة وصرف الرصيد بالكامل.')
        else:
            QMessageBox.critical(self, 'فشل الاعتماد', str(result))

        self._load_drafts()

    def _delete_selected_draft(self):
        items_list = self._get_selected_draft_data()

        if not items_list:
            return

        reply = QMessageBox.question(self, 'تأكيد الحذف', 'هل أنت متأكد من حذف هذا السند نهائياً؟', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        sc = sum((1 for m in items_list if self.api_service.delete_draft(m.get('id'))[0]))

        if sc == len(items_list):
            QMessageBox.information(self, 'نجاح', 'تم الحذف بنجاح.')
        else:
            QMessageBox.warning(self, 'تنبيه', f'تم حذف {sc} من أصل {len(items_list)} أصناف.')

        self._load_drafts()

    def _print_aggregated_quantities(self):
        filtered = getattr(self, '_current_filtered_history', [])

        if not filtered:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد بيانات للطباعة. يرجى البحث أولاً.')
            return

        items_dict = {}

        form = self._first_form()

        if form and getattr(form, '_items_data', None):
            for it in form._items_data:
                items_dict[it['id']] = it

        agg_data = {}
        raw_fallback_agg = {}

        for m in filtered:
            item_id = m.get('item_id')
            item_name = m.get('item_name', '').strip()
            unit_name = m.get('unit_name', '').strip()
            qty = float(m.get('quantity', 0))

            item_obj = items_dict.get(item_id)

            if item_obj and item_obj.get('units'):
                factor = 1.0

                for u in item_obj['units']:
                    if u['unit_name'] == unit_name:
                        factor = float(u.get('conversion_factor', 1.0))
                        break

                if item_id not in agg_data:
                    agg_data[item_id] = {'name': item_name, 'total_base': 0.0, 'units': item_obj['units']}

                agg_data[item_id]['total_base'] += qty * factor
                continue

            key = (item_name, unit_name)
            raw_fallback_agg[key] = raw_fallback_agg.get(key, 0.0) + qty

        rows = []
        idx = 1

        for item_id, data in agg_data.items():
            item_name = data['name']
            total_base = data['total_base']
            units = data['units']

            sorted_units = sorted(units, key=lambda x: float(x.get('conversion_factor', 1.0)), reverse=True)

            remaining = total_base

            for i, u in enumerate(sorted_units):
                factor = float(u.get('conversion_factor', 1.0))

                if remaining < 0.0001:
                    break

                if i == len(sorted_units) - 1:
                    val = remaining / factor
                    val_str = f'{val:g}'

                    rows.append([str(idx), item_name, val_str, u['unit_name'], ''])
                    idx += 1
                    remaining = 0
                    continue

                count = int(remaining // factor)

                if count > 0:
                    rows.append([str(idx), item_name, str(count), u['unit_name'], ''])
                    idx += 1
                    remaining -= count * factor

        for (item_name, unit_name), total_qty in raw_fallback_agg.items():
            rows.append([str(idx), item_name, f'{total_qty:g}', unit_name, ''])
            idx += 1

        wh_name = self.h_cb_warehouse.currentText()

        if wh_name == 'الكل' or not wh_name:
            wh_name = 'جميع المستودعات'

        unit_name = self.h_cb_unit.currentText()

        if unit_name == 'الكل' or not unit_name:
            unit_name = 'جميع الوحدات المستفيدة'

        master = {
            'warehouse': wh_name,
            'unit': unit_name,
            'date_from': self.h_dt_from.date().toString(Qt.DateFormat.ISODate),
            'date_to': self.h_dt_to.date().toString(Qt.DateFormat.ISODate),
        }

        from ..print_helper import print_aggregated_report

        print_aggregated_report(self, master, rows, title='مجمّع كميات أوامر الصرف')

    def load_data(self):
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)

            if isinstance(w, IssueFormTab):
                w.load_data()