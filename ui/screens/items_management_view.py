from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QFormLayout, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QPushButton, QHBoxLayout, QMessageBox, QLabel, QComboBox)
from PyQt6.QtCore import Qt
from ui.api_service import ApiService
from ui.theme import make_header_label
from excel_helper import export_table_to_excel, import_excel_to_dataframe, export_template
from ui.print_helper import print_item_card


class ItemsManagementView(QWidget):
    """Master Data Management for Items (Tabs: List, Form, Balances, Movements)"""

    def __init__(self, parent=None, api_service: ApiService | None = None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()
        self._current_item_id = None
        self._items_data = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        layout.addWidget(make_header_label('إدارة الأصناف (Master Data Management)'))

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._tab_list = QWidget()
        self._tab_form = QWidget()
        self._tab_bals = QWidget()
        self._tab_movs = QWidget()
        self._tab_cats = QWidget()
        self._tab_barcode = QWidget()

        self.tabs.addTab(self._tab_list, 'قائمة الأصناف')
        self.tabs.addTab(self._tab_cats, 'إدارة التصنيفات')
        self.tabs.addTab(self._tab_form, 'بطاقة الصنف (إضافة/تعديل)')
        self.tabs.addTab(self._tab_bals, 'أرصدة الصنف بالمستودعات')
        self.tabs.addTab(self._tab_movs, 'حركة الصنف (كارت الصنف)')
        self.tabs.addTab(self._tab_barcode, 'محطة الباركودات')

        user = getattr(self.parent(), 'current_user', None)
        if user:
            is_admin = user.get('role', '').strip().upper() == 'ADMIN'
            has_explicit = 'items_management' in user.get('permissions', {})
            self._tabs_perms = user.get('permissions', {}).get('items_management', {}).get('tabs', {})
            self._is_admin = is_admin and not has_explicit
        else:
            self._is_admin = False
            self._tabs_perms = {}

        self._build_list_tab()
        self._build_cats_tab()
        self._build_form_tab()
        self._build_bals_tab()
        self._build_movs_tab()
        self._build_barcode_tab()

        if user:
            if has_explicit:
                t1 = self._tabs_perms.get('tab_list', {})
                self.tabs.setTabVisible(0, t1.get('view', False))
                t2 = self._tabs_perms.get('tab_cats', {})
                self.tabs.setTabVisible(1, t2.get('view', False))
                t3 = self._tabs_perms.get('tab_form', {})
                self.tabs.setTabVisible(2, t3.get('view', False))
                t4 = self._tabs_perms.get('tab_bals', {})
                self.tabs.setTabVisible(3, t4.get('view', False))
                t5 = self._tabs_perms.get('tab_movs', {})
                self.tabs.setTabVisible(4, t5.get('view', False))
                t6 = self._tabs_perms.get('tab_barcode', {})
                self.tabs.setTabVisible(5, t6.get('view', False))
            else:
                self.tabs.setTabVisible(0, is_admin)
                self.tabs.setTabVisible(1, is_admin)
                self.tabs.setTabVisible(2, is_admin)
                self.tabs.setTabVisible(3, is_admin)
                self.tabs.setTabVisible(4, is_admin)
                self.tabs.setTabVisible(5, is_admin)

        for i in range(self.tabs.count()):
            if self.tabs.isTabVisible(i):
                self.tabs.setCurrentIndex(i)
                break

        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _generate_sys_barcode(self):
        import time

        ts = str(int(time.time() * 100))[-9:]
        sys_bc = f'104{ts}'
        self.barcode_input.setText(sys_bc)
        QMessageBox.information(self, 'نجاح', f'تم توليد باركود نظامي: {sys_bc}')

    def _build_list_tab(self):
        lay = QVBoxLayout(self._tab_list)

        top_lay = QHBoxLayout()

        btn_refresh = QPushButton('تحديث 🔄')
        btn_refresh.clicked.connect(self.load_data)

        btn_export = QPushButton('📥 تصدير إكسيل')
        btn_export.clicked.connect(lambda: export_table_to_excel(self.tbl_list, self, 'Items_List.xlsx'))

        btn_import = QPushButton('📤 استيراد أصناف من إكسيل')
        btn_import.clicked.connect(self._import_items_from_excel)

        btn_tmpl = QPushButton('📋 تحميل قالب')
        inst = ['كود الصنف: مطلوب. يجب أن يكون فريداً (لا يمكن تكراره) وأرقام فقط.', 'اسم الصنف: مطلوب. يمثل الاسم الظاهر في النظام.', 'التصنيف: اختياري. إذا تم إدخال تصنيف جديد سيتم إنشاؤه تلقائياً.', 'حد الطلب: رقم (الحد الأدنى للتنبيه عند نقص المخزون).', 'وحدة 1: مطلوبة. وتعتبر عادة الوحدة الصغرى.', 'معامل 1: الافتراضي 1.', 'وحدة 2: اختيارية. الوحدة الأكبر (كالكرتون).', 'معامل 2: سعة الوحدة 2 من الوحدة 1 (مثال: الكرتون = 12 حبة).', 'رقم الوحدة الأساسية: اكتب 1 لتكون وحدة 1 هي الأساسية، أو 2 لتكون وحدة 2 هي الأساسية.']
        btn_tmpl.clicked.connect(lambda: export_template(['كود الصنف', 'الباركود', 'اسم الصنف', 'التصنيف', 'حد الطلب', 'وحدة 1', 'معامل 1', 'وحدة 2', 'معامل 2', 'رقم الوحدة الأساسية'], self, 'items_template.xlsx', inst))

        btn_new = QPushButton('إضافة صنف جديد +')
        btn_new.setObjectName('gold_btn')
        btn_new.clicked.connect(self._open_new_form)

        top_lay.addWidget(btn_refresh)
        top_lay.addWidget(btn_export)
        top_lay.addWidget(btn_import)
        top_lay.addWidget(btn_tmpl)
        top_lay.addStretch()
        top_lay.addWidget(btn_new)

        if not getattr(self, '_is_admin', False):
            t1 = getattr(self, '_tabs_perms', {}).get('tab_list', {})
            btn_new.setVisible(t1.get('create', False))
            btn_import.setVisible(t1.get('create', False))
            btn_export.setVisible(t1.get('print', False))
            btn_tmpl.setVisible(t1.get('print', False))

        lay.addLayout(top_lay)

        search_lay = QHBoxLayout()
        search_lay.addWidget(QLabel('🔍 بحث:'))
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText('ابحث بالكود أو اسم الصنف...')
        self.le_search.textChanged.connect(self._filter_list)
        search_lay.addWidget(self.le_search)
        lay.addLayout(search_lay)

        self.tbl_list = QTableWidget(0, 7)
        self.tbl_list.setHorizontalHeaderLabels(['م', 'الكود', 'اسم الصنف', 'التصنيف', 'حد الطلب', 'الوحدات (معامل التحويل)', 'إجراءات'])
        self.tbl_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_list.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.tbl_list.setColumnWidth(5, 250)
        self.tbl_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tbl_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.tbl_list)

    def _build_form_tab(self):
        main_lay = QVBoxLayout(self._tab_form)

        from PyQt6.QtWidgets import QScrollArea, QWidget

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; }')

        container = QWidget()
        lay = QVBoxLayout(container)

        self.lbl_form_mode = QLabel('<b>وضع الإضافة: تسجيل صنف جديد</b>')
        self.lbl_form_mode.setStyleSheet('color: #C5A028; font-size: 16px;')
        lay.addWidget(self.lbl_form_mode)

        form_card = QWidget()
        form_card.setObjectName('card')
        form_layout = QFormLayout(form_card)

        self.code_input = QLineEdit()
        self.barcode_input = QLineEdit()
        self.btn_gen_barcode = QPushButton('توليد آلي ⚙️')
        self.btn_gen_barcode.clicked.connect(self._generate_sys_barcode)

        barcode_lay = QHBoxLayout()
        barcode_lay.addWidget(self.barcode_input)
        barcode_lay.addWidget(self.btn_gen_barcode)

        self.name_input = QLineEdit()
        self.cat_input = QComboBox()
        self.min_input = QLineEdit()
        self.chk_is_refillable = QCheckBox('صنف قابل للتعبئة/الاستبدال (مثل الغاز)')

        form_layout.addRow('رقم التعيين / الكود', self.code_input)
        form_layout.addRow('الباركود (نظامي/مصنعي)', barcode_lay)
        form_layout.addRow('اسم الصنف بشجرة المواد', self.name_input)
        form_layout.addRow('التصنيف الرئيسي', self.cat_input)
        form_layout.addRow('الحد الأدنى للمخزون (إنذار)', self.min_input)
        form_layout.addRow('', self.chk_is_refillable)

        lay.addWidget(form_card)

        self.lbl_units_title = QLabel('<b>تعريف وحدات القياس (شوال، كيلو، جرام...)</b>')
        lay.addWidget(self.lbl_units_title)

        self.tbl_units = QTableWidget(0, 3)
        self.tbl_units.setHorizontalHeaderLabels(['اسم الوحدة', 'معامل التحويل', 'هل هي الأساسية؟'])
        self.tbl_units.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_units.setMinimumHeight(150)
        lay.addWidget(self.tbl_units)

        self.btn_layout_units = QHBoxLayout()
        btn_add_unit = QPushButton('إضافة وحدة +')
        btn_rem_unit = QPushButton('حذف وحدة -')
        btn_add_unit.clicked.connect(self.add_unit_row)
        btn_rem_unit.clicked.connect(self.remove_unit_row)
        self.btn_layout_units.addWidget(btn_add_unit)
        self.btn_layout_units.addWidget(btn_rem_unit)
        self.btn_layout_units.addStretch()
        lay.addLayout(self.btn_layout_units)

        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton('إلغاء / مسح')
        btn_cancel.clicked.connect(self._reset_form)

        self.btn_save = QPushButton('حفظ بطاقة الصنف')
        self.btn_save.setObjectName('gold_btn')
        self.btn_save.clicked.connect(self.save_item)

        if not getattr(self, '_is_admin', False):
            t3 = getattr(self, '_tabs_perms', {}).get('tab_form', {})
            self.btn_save.setVisible(t3.get('create', False))

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_save)

        lay.addLayout(btn_layout)

        scroll.setWidget(container)
        main_lay.addWidget(scroll)

    def _build_cats_tab(self):
        lay = QVBoxLayout(self._tab_cats)

        top_lay = QHBoxLayout()
        btn_refresh = QPushButton('تحديث 🔄')
        btn_refresh.clicked.connect(self._load_categories)

        self.cat_name_input = QLineEdit()
        self.cat_name_input.setPlaceholderText('اسم التصنيف الجديد...')
        self.cat_desc_input = QLineEdit()
        self.cat_desc_input.setPlaceholderText('وصف/ملاحظات...')

        btn_add = QPushButton('إضافة تصنيف +')
        btn_add.setObjectName('gold_btn')
        btn_add.clicked.connect(self._add_category)

        if not getattr(self, '_is_admin', False):
            t2 = getattr(self, '_tabs_perms', {}).get('tab_cats', {})
            btn_add.setVisible(t2.get('create', False))

        top_lay.addWidget(btn_refresh)
        top_lay.addWidget(self.cat_name_input)
        top_lay.addWidget(self.cat_desc_input)
        top_lay.addWidget(btn_add)
        lay.addLayout(top_lay)

        self.tbl_cats = QTableWidget(0, 4)
        self.tbl_cats.setHorizontalHeaderLabels(['م', 'الاسم', 'الوصف', 'إجراءات'])
        self.tbl_cats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_cats.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        lay.addWidget(self.tbl_cats)

    def _build_bals_tab(self):
        lay = QVBoxLayout(self._tab_bals)

        top_lay = QHBoxLayout()
        top_lay.addWidget(QLabel('اختر الصنف لمعاينة الأرصدة:'))

        self.cb_bals_item = QComboBox()
        self.cb_bals_item.setMinimumWidth(300)
        self.cb_bals_item.currentIndexChanged.connect(self._fetch_bals)
        top_lay.addWidget(self.cb_bals_item)
        top_lay.addStretch()
        lay.addLayout(top_lay)

        self.tbl_bals = QTableWidget(0, 4)
        self.tbl_bals.setHorizontalHeaderLabels(['المستودع', 'الوحدة', 'الكمية المتاحة', 'الحد الأدنى والصلاحية'])
        self.tbl_bals.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.tbl_bals)

    def _build_movs_tab(self):
        lay = QVBoxLayout(self._tab_movs)

        top_lay = QHBoxLayout()
        top_lay.addWidget(QLabel('اختر الصنف لعرض حركته:'))

        self.cb_movs_item = QComboBox()
        self.cb_movs_item.setMinimumWidth(300)
        self.cb_movs_item.currentIndexChanged.connect(self._fetch_movs)
        top_lay.addWidget(self.cb_movs_item)

        btn_ref = QPushButton('تحديث السجل 🔄')
        btn_ref.clicked.connect(self._fetch_movs)

        btn_exp_movs = QPushButton('📥 تصدير إكسيل')
        btn_exp_movs.clicked.connect(lambda: export_table_to_excel(self.tbl_movs, self, 'Item_Card.xlsx'))

        btn_print_card = QPushButton('🖨️ طباعة كارت الصنف')
        btn_print_card.clicked.connect(self._print_item_card)

        top_lay.addWidget(btn_ref)
        top_lay.addWidget(btn_exp_movs)
        top_lay.addWidget(btn_print_card)
        top_lay.addStretch()
        lay.addLayout(top_lay)

        self.tbl_movs = QTableWidget(0, 7)
        self.tbl_movs.setHorizontalHeaderLabels(['تاريخ الحركة', 'نوع الحركة', 'المستودع/الجهة', 'الكمية', 'الوحدة', 'الرقم التسلسلي/المستند', 'ملاحظات'])
        self.tbl_movs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.tbl_movs)

    def load_data(self):
        """Called automatically when switching to this view or clicking refresh."""
        ok, data = self.api_service.get_items()
        self.tbl_list.setRowCount(0)
        self.cb_bals_item.blockSignals(True)
        self.cb_movs_item.blockSignals(True)
        self.cb_bals_item.clear()
        self.cb_movs_item.clear()

        if ok and data:
            self._items_data = data
            for i, itm in enumerate(data):
                self.tbl_list.insertRow(i)
                self.tbl_list.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.tbl_list.setItem(i, 1, QTableWidgetItem(itm['item_code']))
                self.tbl_list.setItem(i, 2, QTableWidgetItem(itm['name']))
                self.tbl_list.setItem(i, 3, QTableWidgetItem(itm.get('category_name') or ''))
                self.tbl_list.setItem(i, 4, QTableWidgetItem(str(itm.get('min_limit', 0))))

                units_info = []
                for u in itm.get('units', []):
                    factor = str(u.get('conversion_factor', 1)).rstrip('0').rstrip('.') if '.' in str(u.get('conversion_factor', 1)) else str(u.get('conversion_factor', 1))
                    base_str = ' (أساسية)' if u.get('is_base_unit') else ''
                    units_info.append(f"{u['unit_name']}: {factor}{base_str}")

                self.tbl_list.setItem(i, 5, QTableWidgetItem(' | '.join(units_info)))

                btn_box = QWidget()
                btn_lay = QHBoxLayout(btn_box)
                btn_lay.setContentsMargins(0, 0, 0, 0)

                btn_ed = QPushButton('تعديل ✏️')
                btn_del = QPushButton('حذف 🗑️')

                btn_ed.clicked.connect(lambda _, item_id=itm['id']: self._open_edit_form(item_id))
                btn_del.clicked.connect(lambda _, item_id=itm['id']: self._delete_item(item_id))

                btn_lay.addWidget(btn_ed)
                btn_lay.addWidget(btn_del)

                if not getattr(self, '_is_admin', False):
                    t1 = getattr(self, '_tabs_perms', {}).get('tab_list', {})
                    btn_ed.setVisible(t1.get('edit', False))
                    btn_del.setVisible(t1.get('delete', False))

                self.tbl_list.setCellWidget(i, 6, btn_box)

                self.cb_bals_item.addItem(f"{itm['item_code']} - {itm['name']}", itm['id'])
                self.cb_movs_item.addItem(f"{itm['item_code']} - {itm['name']}", itm['id'])

        self.cb_bals_item.blockSignals(False)
        self.cb_movs_item.blockSignals(False)
        self._load_categories()

    def _load_categories(self):
        ok, data = self.api_service.get_categories()
        self.cat_input.clear()
        self.cat_input.addItem('--- بدون تصنيف ---', None)

        if ok and data:
            self.tbl_cats.setRowCount(len(data))
            for i, cat in enumerate(data):
                self.cat_input.addItem(cat['name'], cat['id'])

                self.tbl_cats.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.tbl_cats.setItem(i, 1, QTableWidgetItem(cat['name']))
                self.tbl_cats.setItem(i, 2, QTableWidgetItem(cat.get('description') or ''))

                btn_del = QPushButton('حذف 🗑️')
                btn_del.clicked.connect(lambda _, cat_id=cat['id']: self._delete_category(cat_id))

                if not getattr(self, '_is_admin', False):
                    t2 = getattr(self, '_tabs_perms', {}).get('tab_cats', {})
                    btn_del.setVisible(t2.get('delete', False))

                self.tbl_cats.setCellWidget(i, 3, btn_del)
        else:
            self.tbl_cats.setRowCount(0)

        import PyQt6.QtWidgets as QtWidgets
        QtWidgets.QApplication.processEvents()

    def _add_category(self):
        name = self.cat_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, 'خطأ', 'يجب إدخال اسم التصنيف')
            return

        data = {'name': name, 'description': self.cat_desc_input.text().strip()}
        ok, res = self.api_service.create_category(data)

        if ok:
            QMessageBox.information(self, 'نجاح', 'تم إضافة التصنيف بنجاح')
            self.cat_name_input.clear()
            self.cat_desc_input.clear()
            self._load_categories()
        else:
            QMessageBox.warning(self, 'خطأ', str(res))

    def _delete_category(self, cat_id):
        reply = QMessageBox.question(self, 'تأكيد', 'هل أنت متأكد من حذف التصنيف؟')
        if reply == QMessageBox.StandardButton.Yes:
            ok, res = self.api_service.delete_category(cat_id)
            if ok:
                self._load_categories()
            else:
                QMessageBox.warning(self, 'خطأ', str(res))

    def _on_tab_changed(self, index):
        if index == 0:
            self.load_data()
        elif index == 1:
            self._load_categories()
        elif index == 3:
            self._fetch_bals()
        elif index == 4:
            self._fetch_movs()
        elif index == 5:
            self._load_barcode_tab()

    def _open_new_form(self):
        self._reset_form()

        next_code = 1
        if hasattr(self, '_items_data') and self._items_data:
            import re
            codes = []
            for itm in self._items_data:
                m = re.search('\\d+', itm.get('item_code', ''))
                if not m:
                    continue
                codes.append(int(m.group()))
            if codes:
                next_code = max(codes) + 1

        self.code_input.setText(str(next_code))
        self.tabs.setCurrentIndex(2)

    def _open_edit_form(self, item_id):
        itm = next((x for x in self._items_data if x['id'] == item_id), None)
        if not itm:
            return

        self._current_item_id = item_id
        self.lbl_form_mode.setText(f"<b>وضع التعديل: تحديث الصنف ({itm['item_code']})</b>")
        self.code_input.setText(itm['item_code'])
        self.code_input.setReadOnly(True)
        self.barcode_input.setText(itm.get('barcode') or '')
        self.name_input.setText(itm['name'])

        cat_id = itm.get('category_id')
        if cat_id:
            idx = self.cat_input.findData(cat_id)
            if idx >= 0:
                self.cat_input.setCurrentIndex(idx)
        else:
            self.cat_input.setCurrentIndex(0)

        self.min_input.setText(str(itm.get('min_limit') or 0))
        self.chk_is_refillable.setChecked(bool(itm.get('is_refillable')))

        self.lbl_units_title.show()
        self.tbl_units.show()
        for i in range(self.btn_layout_units.count()):
            w = self.btn_layout_units.itemAt(i).widget()
            if not w:
                continue
            w.show()

        existing_units = itm.get('units', [])
        self.tbl_units.setRowCount(0)
        for u in existing_units:
            r = self.tbl_units.rowCount()
            self.tbl_units.insertRow(r)
            self.tbl_units.setItem(r, 0, QTableWidgetItem(u.get('unit_name', '')))
            self.tbl_units.setItem(r, 1, QTableWidgetItem(str(u.get('conversion_factor', 1.0))))

            chk = QCheckBox()
            chk.setChecked(u.get('is_base_unit', False))
            chk.stateChanged.connect(lambda state, row=r: self._base_changed(state, row))
            self.tbl_units.setCellWidget(r, 2, chk)

        self.btn_save.setText('حفظ التعديلات')
        self.tabs.setCurrentIndex(2)

    def _reset_form(self):
        self._current_item_id = None
        self.lbl_form_mode.setText('<b>وضع الإضافة: تسجيل صنف جديد</b>')
        self.code_input.setReadOnly(False)
        self.code_input.clear()
        self.barcode_input.clear()
        self.name_input.clear()
        self.cat_input.setCurrentIndex(0)
        self.min_input.clear()
        self.chk_is_refillable.setChecked(False)
        self.tbl_units.setRowCount(0)
        self.btn_save.setText('حفظ بطاقة الصنف')

        self.lbl_units_title.show()
        self.tbl_units.show()
        for i in range(self.btn_layout_units.count()):
            w = self.btn_layout_units.itemAt(i).widget()
            if not w:
                continue
            w.show()

    def add_unit_row(self):
        r = self.tbl_units.rowCount()
        self.tbl_units.insertRow(r)
        self.tbl_units.setItem(r, 0, QTableWidgetItem(''))
        self.tbl_units.setItem(r, 1, QTableWidgetItem('1.0'))

        chk = QCheckBox()
        chk.stateChanged.connect(lambda state, row=r: self._base_changed(state, row))
        self.tbl_units.setCellWidget(r, 2, chk)

    def remove_unit_row(self):
        curr = self.tbl_units.currentRow()
        if curr >= 0:
            self.tbl_units.removeRow(curr)

    def _base_changed(self, state, row):
        if state == Qt.CheckState.Checked.value:
            for r in range(self.tbl_units.rowCount()):
                if r != row:
                    w = self.tbl_units.cellWidget(r, 2)
                    if isinstance(w, QCheckBox):
                        w.blockSignals(True)
                        w.setChecked(False)
                        w.blockSignals(False)

    def save_item(self):
        name = self.name_input.text().strip()
        code = self.code_input.text().strip()
        min_lim = float(self.min_input.text() or 0)

        if not name or not (self._current_item_id or code):
            QMessageBox.warning(self, 'بيانات ناقصة', 'يجب إدخال كود الصنف واسم الصنف على الأقل.')
            return

        if self._current_item_id:
            units = []
            base_found = False
            for r in range(self.tbl_units.rowCount()):
                u_name = self.tbl_units.item(r, 0).text() if self.tbl_units.item(r, 0) else ''
                conv = float(self.tbl_units.item(r, 1).text() or 1.0)
                chk = self.tbl_units.cellWidget(r, 2)
                is_base = chk.isChecked() if isinstance(chk, QCheckBox) else False
                if is_base:
                    base_found = True
                units.append({'unit_name': u_name, 'conversion_factor': conv, 'is_base_unit': is_base})

            if not base_found and units:
                QMessageBox.warning(self, 'تنبيه', 'يجب تحديد الوحدة الأساسية للصنف.')
                return

            payload = {
                'name': name,
                'barcode': self.barcode_input.text().strip() or None,
                'category_id': self.cat_input.currentData(),
                'min_limit': min_lim,
                'is_refillable': self.chk_is_refillable.isChecked(),
                'units': units,
            }

            ok, msg = self.api_service._request('PUT', f'/items/{self._current_item_id}', json=payload)

            if ok:
                QMessageBox.information(self, 'نجاح', 'تم التعديل بنجاح.')
                self._reset_form()
                self.load_data()
                self.tabs.setCurrentIndex(0)
                return
            else:
                QMessageBox.critical(self, 'خطأ', str(msg))
                return

        code = self.code_input.text().strip()
        barcode_val = self.barcode_input.text().strip() or None

        units = []
        base_found = False
        for r in range(self.tbl_units.rowCount()):
            u_name = self.tbl_units.item(r, 0).text() if self.tbl_units.item(r, 0) else ''
            conv = float(self.tbl_units.item(r, 1).text() or 1.0)
            chk = self.tbl_units.cellWidget(r, 2)
            is_base = chk.isChecked() if isinstance(chk, QCheckBox) else False
            if is_base:
                base_found = True
            units.append({'unit_name': u_name, 'conversion_factor': conv, 'is_base_unit': is_base})

        if not base_found and units:
            QMessageBox.warning(self, 'تنبيه', 'يجب تحديد الوحدة الأساسية للصنف.')
            return

        payload = {
            'item_code': code,
            'barcode': barcode_val,
            'name': name,
            'category_id': self.cat_input.currentData(),
            'min_limit': min_lim,
            'is_refillable': self.chk_is_refillable.isChecked(),
            'units': units,
        }

        ok, msg = self.api_service.create_item(payload)

        if ok:
            QMessageBox.information(self, 'نجاح', 'تم حفظ الصنف بنجاح!')
            self._reset_form()
            self.load_data()
        else:
            QMessageBox.critical(self, 'خطأ', str(msg))

    def _delete_item(self, item_id):
        reply = QMessageBox.question(self, 'تأكيد', 'هل أنت متأكد من حذف هذا الصنف؟ لا يمكن التراجع.', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = self.api_service._request('DELETE', f'/items/{item_id}')
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم الحذف.')
                self.load_data()
            else:
                QMessageBox.critical(self, 'خطأ', str(msg))

    def _fetch_bals(self):
        item_id = self.cb_bals_item.currentData()
        self.tbl_bals.setRowCount(0)
        if not item_id:
            return

        ok, bals = self.api_service.get_stock_balance()

        if ok and bals:
            row = 0
            for b in bals:
                if b['item_id'] == item_id:
                    self.tbl_bals.insertRow(row)
                    self.tbl_bals.setItem(row, 0, QTableWidgetItem(b['warehouse_name']))
                    self.tbl_bals.setItem(row, 1, QTableWidgetItem(b['unit_name']))
                    self.tbl_bals.setItem(row, 2, QTableWidgetItem(str(b['quantity'])))

                    status = 'جيد ✅' if b['quantity'] > b['min_limit'] else 'تحت الحد ⚠️'
                    if b['quantity'] == 0:
                        status = 'فارغ ❌'

                    self.tbl_bals.setItem(row, 3, QTableWidgetItem(status))
                    row += 1

    def _fetch_movs(self):
        item_id = self.cb_movs_item.currentData()
        self.tbl_movs.setRowCount(0)
        if not item_id:
            return

        ok, movs = self.api_service._request('GET', f'/stock/movements?item_id={item_id}&limit=100')

        if ok and movs:
            for i, m in enumerate(movs):
                self.tbl_movs.insertRow(i)
                self.tbl_movs.setItem(i, 0, QTableWidgetItem(m.get('movement_date', '')))

                t = m.get('movement_type', '')
                type_map = {'IN': 'وارد 🔽', 'OUT': 'صادر 🔼', 'TRANSFER': 'تحويل ↔️'}

                w_info = m.get('warehouse_name', '')
                if t == 'OUT' and m.get('beneficiary_unit'):
                    w_info = f"{w_info} ← {m.get('beneficiary_unit')}"

                self.tbl_movs.setItem(i, 1, QTableWidgetItem(type_map.get(t, t)))
                self.tbl_movs.setItem(i, 2, QTableWidgetItem(w_info))
                self.tbl_movs.setItem(i, 3, QTableWidgetItem(str(m.get('quantity', 0))))
                self.tbl_movs.setItem(i, 4, QTableWidgetItem(m.get('unit_name', '')))
                self.tbl_movs.setItem(i, 5, QTableWidgetItem(m.get('reference_no', '')))
                self.tbl_movs.setItem(i, 6, QTableWidgetItem(m.get('notes', '')))

    def _print_item_card(self):
        item_name = self.cb_movs_item.currentText()
        rows = []
        for r in range(self.tbl_movs.rowCount()):
            row = []
            for c in range(self.tbl_movs.columnCount()):
                it = self.tbl_movs.item(r, c)
                row.append(it.text() if it else '')
            rows.append(row)

        if not rows:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد حركات لطباعتها.')
            return

        print_item_card(self, item_name, rows)

    def _import_items_from_excel(self):
        df = import_excel_to_dataframe(self)
        if df is None:
            return

        ok, cats_data = self.api_service.get_categories()
        cat_map = {c['name'].strip().lower(): c['id'] for c in cats_data} if ok and cats_data else {}

        success_count = 0
        failed_count = 0

        for _, row in df.iterrows():
            code = str(row.get('كود الصنف', '')).strip()
            if code.endswith('.0'):
                code = code[:-2]

            barcode = str(row.get('الباركود', '')).strip()
            if barcode.endswith('.0'):
                barcode = barcode[:-2]

            name = str(row.get('اسم الصنف', '')).strip()
            cat_name = str(row.get('التصنيف', '')).strip()
            min_l = float(row.get('حد الطلب', 0) or 0)

            if not (code and name):
                continue

            cat_id = None
            if cat_name:
                key = cat_name.lower()
                if key in cat_map:
                    cat_id = cat_map[key]
                else:
                    ok_c, new_c = self.api_service.create_category({'name': cat_name, 'description': 'مستورد من إكسيل'})
                    if ok_c:
                        cat_id = new_c['id']
                        cat_map[key] = cat_id

            units = []
            base_choice = str(row.get('رقم الوحدة الأساسية', '1')).strip()
            if base_choice not in ('1', '2'):
                base_choice = '1'

            u1 = str(row.get('وحدة 1', '')).strip()
            if u1:
                units.append({'unit_name': u1, 'conversion_factor': float(row.get('معامل 1', 1) or 1), 'is_base_unit': base_choice == '1'})

            u2 = str(row.get('وحدة 2', '')).strip()
            if u2:
                units.append({'unit_name': u2, 'conversion_factor': float(row.get('معامل 2', 1) or 1), 'is_base_unit': base_choice == '2'})

            if units and not any(u['is_base_unit'] for u in units):
                units[0]['is_base_unit'] = True

            payload = {
                'item_code': code,
                'barcode': barcode if barcode else None,
                'name': name,
                'category_id': cat_id,
                'min_limit': min_l,
                'units': units,
            }

            ok_i, _ = self.api_service.create_item(payload)

            if ok_i:
                success_count += 1
            else:
                failed_count += 1

        QMessageBox.information(self, 'نتيجة الاستيراد', f'تم إضافة {success_count} صنف بنجاح.\\nفشل: {failed_count}')
        self.load_data()

    def _filter_list(self, text):
        text = text.strip().lower()
        for r in range(self.tbl_list.rowCount()):
            show = True
            if text:
                match = False
                for c in range(self.tbl_list.columnCount() - 1):
                    it = self.tbl_list.item(r, c)
                    if not it:
                        continue
                    if text in it.text().lower():
                        match = True
                        break
                if not match:
                    show = False
            self.tbl_list.setRowHidden(r, not show)

    def _build_barcode_tab(self):
        lay = QVBoxLayout(self._tab_barcode)

        header_lbl = QLabel('<b>محطة إدارة وطباعة الباركودات</b>')
        header_lbl.setStyleSheet('font-size: 16px; color: #C5A028; margin-bottom: 5px;')
        lay.addWidget(header_lbl)

        toolbar = QHBoxLayout()

        btn_refresh_bc = QPushButton('تحديث القائمة 🔄')
        btn_refresh_bc.clicked.connect(self._load_barcode_tab)

        self.chk_only_missing = QCheckBox('إظهار الأصناف بدون باركود فقط')
        self.chk_only_missing.stateChanged.connect(self._load_barcode_tab)

        btn_gen_all = QPushButton('توليد باركود للأصناف الناقصة ⚙️')
        btn_gen_all.setObjectName('gold_btn')
        btn_gen_all.clicked.connect(self._generate_missing_barcodes)

        toolbar.addWidget(btn_refresh_bc)
        toolbar.addWidget(self.chk_only_missing)
        toolbar.addStretch()
        toolbar.addWidget(btn_gen_all)
        lay.addLayout(toolbar)

        toolbar2 = QHBoxLayout()

        btn_select_all = QPushButton('تحديد الكل ✅')
        btn_select_all.clicked.connect(self._select_all_barcodes)

        btn_deselect = QPushButton('إلغاء التحديد')
        btn_deselect.clicked.connect(self._deselect_all_barcodes)

        lbl_copies = QLabel('عدد النسخ لكل ملصق:')
        lbl_copies.setStyleSheet('font-weight: bold;')

        from PyQt6.QtWidgets import QSpinBox
        self.sp_bc_copies = QSpinBox()
        self.sp_bc_copies.setRange(1, 500)
        self.sp_bc_copies.setValue(1)
        self.sp_bc_copies.setSuffix(' نسخة')

        btn_print = QPushButton('🖨️ طباعة الباركودات المحددة')
        btn_print.setStyleSheet('background-color: #2E6B35; color: white; font-weight: bold; padding: 6px 16px; font-size: 14px;')
        btn_print.clicked.connect(self._print_selected_barcodes)

        toolbar2.addWidget(btn_select_all)
        toolbar2.addWidget(btn_deselect)
        toolbar2.addStretch()
        toolbar2.addWidget(lbl_copies)
        toolbar2.addWidget(self.sp_bc_copies)
        toolbar2.addWidget(btn_print)

        if not getattr(self, '_is_admin', False):
            t6 = getattr(self, '_tabs_perms', {}).get('tab_barcode', {})
            btn_gen_all.setVisible(t6.get('create', False))
            btn_print.setVisible(t6.get('print', False))

        lay.addLayout(toolbar2)

        self.tbl_barcode = QTableWidget(0, 5)
        self.tbl_barcode.setHorizontalHeaderLabels(['✓', 'كود الصنف', 'اسم الصنف', 'الباركود', 'الحالة'])
        self.tbl_barcode.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_barcode.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.tbl_barcode)

        self.lbl_bc_stats = QLabel('')
        self.lbl_bc_stats.setStyleSheet('color: #888; font-size: 12px; margin-top: 2px;')
        lay.addWidget(self.lbl_bc_stats)

    def _load_barcode_tab(self):
        ok, items = self.api_service.get_items()
        if not ok:
            return

        only_missing = self.chk_only_missing.isChecked()
        total = len(items)
        with_bc = sum(1 for x in items if x.get('barcode'))
        without_bc = total - with_bc

        if only_missing:
            items = [x for x in items if not x.get('barcode')]

        self.tbl_barcode.setRowCount(len(items))

        for row, itm in enumerate(items):
            chk = QCheckBox()
            chk.setChecked(True)

            w = QWidget()
            l = QHBoxLayout(w)
            l.addWidget(chk)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setContentsMargins(0, 0, 0, 0)

            self.tbl_barcode.setCellWidget(row, 0, w)
            self.tbl_barcode.setItem(row, 1, QTableWidgetItem(itm.get('item_code', '')))
            self.tbl_barcode.setItem(row, 2, QTableWidgetItem(itm.get('name', '')))

            bc = itm.get('barcode', '') or ''
            self.tbl_barcode.setItem(row, 3, QTableWidgetItem(bc))

            if bc:
                si = QTableWidgetItem('✅ مسجل')
                si.setForeground(Qt.GlobalColor.darkGreen)
            else:
                si = QTableWidgetItem('⚠️ غير مسجل')
                si.setForeground(Qt.GlobalColor.red)

            self.tbl_barcode.setItem(row, 4, si)

        self.lbl_bc_stats.setText(f'إجمالي: {total}  |  لديه باركود: {with_bc}  |  بدون: {without_bc}')

    def _select_all_barcodes(self):
        for row in range(self.tbl_barcode.rowCount()):
            w = self.tbl_barcode.cellWidget(row, 0)
            if not w:
                continue
            chk = w.findChild(QCheckBox)
            if not chk:
                continue
            chk.setChecked(True)

    def _deselect_all_barcodes(self):
        for row in range(self.tbl_barcode.rowCount()):
            w = self.tbl_barcode.cellWidget(row, 0)
            if not w:
                continue
            chk = w.findChild(QCheckBox)
            if not chk:
                continue
            chk.setChecked(False)

    def _generate_missing_barcodes(self):
        import time

        ok, items = self.api_service.get_items()
        if not ok:
            QMessageBox.critical(self, 'خطأ', 'تعذر جلب الأصناف')
            return

        missing = [x for x in items if not x.get('barcode')]

        if not missing:
            QMessageBox.information(self, 'تمام', 'جميع الأصناف لديها باركود.')
            return

        reply = QMessageBox.question(self, 'تأكيد', f'سيتم توليد باركود لـ {len(missing)} صنف. متابعة؟')
        if reply != QMessageBox.StandardButton.Yes:
            return

        count = 0
        for itm in missing:
            ts = str(int(time.time() * 1000))[-9:None]
            new_bc = f'104{ts}'

            ok2, _ = self.api_service._request('PUT', f"/items/{itm['id']}", json={'barcode': new_bc})

            if ok2:
                count += 1

            time.sleep(0.002)

        QMessageBox.information(self, 'تم', f'تم توليد باركود لـ {count} صنف.')
        self._load_barcode_tab()

    CODE128_PATTERNS = [
        '11011001100', '11001101100', '11001100110', '10010011000', '10010001100', '10001001100',
        '10011001000', '10011000100', '10001100100', '11001001000', '11001000100', '11000100100',
        '10110011100', '10011011100', '10011001110', '10111001100', '10011101100', '10011100110',
        '11001110010', '11001011100', '11001001110', '11011100100', '11001110100', '11100101100',
        '11100100110', '11101100100', '11100110100', '11100110010', '11011011000', '11011000110',
        '11000110110', '10100011000', '10001011000', '10001000110', '10110001000', '10001101000',
        '10001100010', '11010001000', '11000101000', '11000100010', '10110111000', '10110001110',
        '10001101110', '10111011000', '10111000110', '10001110110', '11101110110', '11010001110',
        '11000101110', '11011101000', '11011100010', '11011101110', '11101011000', '11101000110',
        '11100010110', '11101101000', '11101100010', '11100011010', '11101111010', '11001000010',
        '11110001010', '10100110000', '10100001100', '10010110000', '10010000110', '10000101100',
        '10000100110', '10110010000', '10110000100', '10011010000', '10011000010', '10000110100',
        '10000110010', '11000010010', '11001010000', '11110111010', '11000010100', '10001111010',
        '10100111100', '10010111100', '10010011110', '10111100100', '10011110100', '10011110010',
        '11110100100', '11110010100', '11110010010', '11011011110', '11011110110', '11110110110',
        '10101111000', '10100011110', '10001011110', '10111101000', '10111100010', '11110101000',
        '11110100010', '10111011110', '10111101110', '11101011110', '11110101110', '11010000100',
        '11010010000', '11010000100', '11010010000', '11010011100', '1100011101011',
    ]

    def _encode_code128(self, text):
        values = []
        checksum = 104
        values.append(104)

        for i, ch in enumerate(text):
            v = ord(ch) - 32
            values.append(v)
            checksum += v * (i + 1)

        values.append(checksum % 103)
        values.append(106)

        bars = ''
        for v in values:
            bars += self.CODE128_PATTERNS[v]

        return bars

    def _generate_barcode_qimage(self, bc_value):
        from PyQt6.QtGui import QImage, QPainter, QColor, QFont
        from PyQt6.QtCore import Qt, QRect

        bars = self._encode_code128(str(bc_value))

        bar_width = 2
        bar_height = 70
        text_height = 18
        quiet_zone = 20

        img_w = len(bars) * bar_width + quiet_zone * 2
        img_h = bar_height + text_height + 6

        img = QImage(img_w, img_h, QImage.Format.Format_RGB32)
        img.fill(QColor(255, 255, 255))

        painter = QPainter(img)

        x = quiet_zone
        for bit in bars:
            if bit == '1':
                painter.fillRect(x, 2, bar_width, bar_height, QColor(0, 0, 0))
            x += bar_width

        font = QFont('Arial', 10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(0, 0, 0))

        text_rect = QRect(0, bar_height + 2, img_w, text_height)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(bc_value))

        painter.end()

        return img

    def _print_selected_barcodes(self):
        from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
        from PyQt6.QtGui import QTextDocument, QImage
        from PyQt6.QtCore import QUrl

        copies = self.sp_bc_copies.value()

        selected = []
        for row in range(self.tbl_barcode.rowCount()):
            w = self.tbl_barcode.cellWidget(row, 0)
            if not w:
                continue
            chk = w.findChild(QCheckBox)
            if not chk:
                continue
            if not chk.isChecked():
                continue

            code = self.tbl_barcode.item(row, 1).text() if self.tbl_barcode.item(row, 1) else ''
            name = self.tbl_barcode.item(row, 2).text() if self.tbl_barcode.item(row, 2) else ''
            bc_val = self.tbl_barcode.item(row, 3).text() if self.tbl_barcode.item(row, 3) else ''

            if not bc_val:
                continue

            selected.append({'code': code, 'name': name, 'barcode': bc_val})

        if not selected:
            QMessageBox.warning(self, 'تنبيه', 'لم يتم تحديد أصناف لها باركود للطباعة.')
            return

        bc_images = {}
        for item in selected:
            bv = item['barcode']
            if bv not in bc_images:
                bc_images[bv] = self._generate_barcode_qimage(bv)

        expanded = []
        for item in selected:
            for _ in range(copies):
                expanded.append(item)

        cols = 3
        html = '<html><head><style>'
        html += '@page{margin:5mm;} body{font-family:Arial;}'
        html += '.g{width:100%;border-collapse:collapse;}'
        html += 'tr{page-break-inside:avoid;}'
        html += '.c{border:1px dashed #ccc;text-align:center;padding:8px 4px;width:33%;vertical-align:middle;}'
        html += '.n{font-size:10px;font-weight:bold;direction:rtl;margin-bottom:2px;}'
        html += '.k{font-size:8px;color:#666;margin-bottom:2px;}'
        html += '</style></head><body><table class="g">'

        for i, item in enumerate(expanded):
            if i % cols == 0:
                html += '<tr>'

            bv = item['barcode']
            img_key = f'bc_{bv}'

            if bc_images.get(bv) is not None:
                img_html = f'<img src="{img_key}" width="200" height="60" />'
            else:
                img_html = f'<div style="font-size:16px;font-weight:bold;letter-spacing:2px;">{bv}</div>'

            html += f'<td class="c"><div class="n">{item["name"]}</div><div class="k">كود: {item["code"]}</div><div>{img_html}</div></td>'

            if (i + 1) % cols == 0:
                html += '</tr>'

        rem = len(expanded) % cols
        if rem:
            for _ in range(cols - rem):
                html += '<td class="c"></td>'
            html += '</tr>'

        html += '</table></body></html>'

        registered_images = bc_images

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.setWindowTitle('معاينة طباعة الباركودات')

        def render(p):
            doc = QTextDocument()
            doc.setHtml(html)

            for bv, qimg in registered_images.items():
                if qimg is None:
                    continue
                doc.addResource(2, QUrl(f'bc_{bv}'), qimg)

            doc.setHtml(html)
            doc.setPageSize(p.pageRect(QPrinter.Unit.Point).size())
            doc.print(p)

        preview.paintRequested.connect(render)
        preview.exec()

