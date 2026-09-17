# NOTE: هذا الملف أُعيد بناؤه يدوياً من ملف beneficiary_units_view.pyc
# الملف الأصلي مُصرَّف بصيغة Python 3.14 (RC) التي لا تدعمها أدوات فك التشفير
# الحالية. تم استخراج كل الأسماء والنصوص والقيم الثابتة (بما فيها الـ docstrings)
# بدقة كاملة عبر وحدة marshal، وأُعيد بناء التسلسل المنطقي بالاعتماد عليها
# وعلى نفس نمط ملف warehouses_view.py من نفس المشروع. الأجزاء الأقل يقيناً
# (خصوصاً منطق صلاحيات التبويبات في load_data، وتفصيل رسالة تنبيه الاستيراد)
# معلَّمة بتعليق "تقريبي" ويُفضّل مراجعتها يدوياً.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QHBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QDateEdit, QLabel, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, QDate

from ui.api_service import ApiService
from ui.theme import make_header_label
from excel_helper import export_table_to_excel, import_excel_to_dataframe, export_template


class BeneficiaryUnitsView(QWidget):

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(make_header_label('الوحدات المستفيدة (شجرة القوات)'))

        self.tabs = tabs = QTabWidget()

        tab_list = QWidget()
        lay_list = QVBoxLayout(tab_list)

        form_card = QWidget()
        form_card.setObjectName('card')
        form = QFormLayout(form_card)

        self.le_code = QLineEdit()
        self.le_name = QLineEdit()
        self.le_cat = QLineEdit()

        self.cb_parent = QComboBox()
        self.cb_parent.addItem('بدون (معسكر رئيسي)', None)

        form.addRow('رقم / كود الوحدة:', self.le_code)
        form.addRow('اسم الوحدة:', self.le_name)
        form.addRow('الاختصاص (مثال: مشاة):', self.le_cat)
        form.addRow('تبعية الوحدة لمعسكر:', self.cb_parent)

        btn_add = QPushButton('إضافة وحدة / معسكر')
        btn_add.clicked.connect(self.add_unit)
        form.addRow('', btn_add)

        lay_list.addWidget(form_card)

        search_bar = QHBoxLayout()
        search_bar.addWidget(QLabel('🔍 بحث:'))
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText('ابحث بالاسم أو الكود...')
        self.le_search.textChanged.connect(self._filter_tree)
        search_bar.addWidget(self.le_search)

        btn_export_tree = QPushButton('📥 تصدير إكسيل')
        btn_export_tree.clicked.connect(self._export_tree)
        search_bar.addWidget(btn_export_tree)

        user = getattr(self.parent(), 'current_user', None) or {}
        is_admin = user.get('role', '').strip().upper() == 'ADMIN'
        bp = user.get('permissions', {}).get('basic_data', {})

        # تقريبي: إخفاء نموذج الإضافة عن المستخدمين بدون صلاحية "add"
        if not (is_admin or bp.get('add', False)):
            form_card.setVisible(False)

        if is_admin or bp.get('add', False) or bp.get('create', False):
            btn_import = QPushButton('📤 استيراد من إكسل')
            btn_import.clicked.connect(self._import_units_from_excel)
            search_bar.addWidget(btn_import)

        if is_admin or bp.get('export', False) or bp.get('print', False):
            btn_template = QPushButton('📋 تحميل قالب')
            btn_template.clicked.connect(lambda: export_template(
                self, 'units_template.xlsx',
                ('كود الوحدة', 'اسم الوحدة', 'الاختصاص', 'كود المعسكر الأم'),
                'كود الوحدة'
            ))
            search_bar.addWidget(btn_template)

        lay_list.addLayout(search_bar)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(('الكود / الرقم', 'اسم المعسكر أو الوحدة', 'الاختصاص', 'إجراءات'))
        self.tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tree.setAlternatingRowColors(True)
        lay_list.addWidget(self.tree)

        tabs.addTab(tab_list, 'هيكلية المعسكرات والوحدات')

        tab_history = QWidget()
        lay_hist = QVBoxLayout(tab_history)

        top_h = QHBoxLayout()
        top_h.addWidget(QLabel('الوحدة:'))
        self.cb_hist_unit = QComboBox()
        top_h.addWidget(self.cb_hist_unit)

        top_h.addWidget(QLabel('من:'))
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addMonths(-1))
        top_h.addWidget(self.dt_from)

        top_h.addWidget(QLabel('إلى:'))
        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        top_h.addWidget(self.dt_to)

        btn_fetch = QPushButton('عرض سجل الصرف')
        btn_fetch.clicked.connect(self.load_history)
        top_h.addWidget(btn_fetch)

        btn_export_hist = QPushButton('📥 تصدير إكسيل')
        btn_export_hist.clicked.connect(lambda: export_table_to_excel(self.tbl_hist, 'Unit_History.xlsx'))
        top_h.addWidget(btn_export_hist)

        top_h.addStretch()
        lay_hist.addLayout(top_h)

        self.tbl_hist = QTableWidget()
        self.tbl_hist.setHorizontalHeaderLabels(('التاريخ', 'رقم الإذن', 'الصنف', 'الكمية', 'الوحدة المستودعية'))
        self.tbl_hist.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        lay_hist.addWidget(self.tbl_hist)

        tabs.addTab(tab_history, 'سجل الصرف الاستهلاكي')

        layout.addWidget(tabs)

    def load_data(self):
        # تقريبي: منطق إظهار/إخفاء التبويبات حسب صلاحيات المستخدم
        user = getattr(self.parent(), 'current_user', None) or {}
        is_admin = user.get('role', '').strip().upper() == 'ADMIN'
        perms = user.get('permissions', {})
        tabs_p = perms.get('beneficiaries', {}).get('tabs', {})
        has_explicit = isinstance(tabs_p, dict) and tabs_p

        if has_explicit:
            self.tabs.setTabVisible(0, is_admin or tabs_p.get('tab_list', {}).get('view', False))
            self.tabs.setTabVisible(1, is_admin or tabs_p.get('tab_history', {}).get('view', False))

        for i in range(self.tabs.count()):
            if self.tabs.isTabVisible(i):
                self.tabs.setCurrentIndex(i)
                break

        self.tree.clear()
        self.cb_parent.clear()
        self.cb_parent.addItem('بدون (معسكر رئيسي)', None)
        self.cb_hist_unit.clear()

        ok, data = self.api_service.get_units()
        if not ok:
            return

        for u in data:
            label = u.get('code', '') + ' - ' + u.get('name', '')
            self.cb_parent.addItem(label, u.get('id'))
            self.cb_hist_unit.addItem(label, u.get('id'))

        root_units = [u for u in data if not u.get('parent_id')]
        for root in root_units:
            root_node = QTreeWidgetItem(self.tree, [
                root.get('code', ''), root.get('name', ''), root.get('category', '')
            ])
            font = root_node.font(0)
            font.setBold(True)
            root_node.setFont(0, font)
            root_node.setData(0, Qt.ItemDataRole.UserRole, root.get('id'))
            self._build_children(root_node, root.get('id'), data)

        self.tree.expandAll()

    def _build_children(self, parent_node, parent_id, all_data):
        children = [u for u in all_data if u.get('parent_id') == parent_id]
        for child in children:
            child_node = QTreeWidgetItem(parent_node, [
                child.get('code', ''), child.get('name', ''), child.get('category', '')
            ])
            child_node.setData(0, Qt.ItemDataRole.UserRole, child.get('id'))
            self._build_children(child_node, child.get('id'), all_data)

    def add_unit(self):
        pid = self.cb_parent.currentData()
        payload = {
            'code': self.le_code.text().strip(),
            'name': self.le_name.text().strip(),
            'category': self.le_cat.text().strip(),
            'parent_id': pid,
        }

        if not payload['code'] or not payload['name']:
            QMessageBox.warning(self, 'بيانات ناقصة', 'يجب إدخال كود الوحدة واسم الوحدة على الأقل.')
            return

        ok, msg = self.api_service.create_unit(payload)
        if ok:
            self.le_code.clear()
            self.le_name.clear()
            self.le_cat.clear()
            self.load_data()
        else:
            QMessageBox.critical(self, 'خطأ', str(msg))

    def load_history(self):
        uid = self.cb_hist_unit.currentData()
        df = self.dt_from.date().toString(Qt.DateFormat.ISODate)
        dt = self.dt_to.date().toString(Qt.DateFormat.ISODate)

        ok, data = self.api_service.get_unit_history(uid, df, dt)
        self.tbl_hist.setRowCount(0)
        if not ok:
            return

        for idx, m in enumerate(data):
            self.tbl_hist.insertRow(idx)
            self.tbl_hist.setItem(idx, 0, QTableWidgetItem(str(m.get('movement_date', ''))))
            self.tbl_hist.setItem(idx, 1, QTableWidgetItem(str(m.get('reference_no', ''))))
            self.tbl_hist.setItem(idx, 2, QTableWidgetItem(str(m.get('item_name', ''))))
            self.tbl_hist.setItem(idx, 3, QTableWidgetItem(str(m.get('quantity', ''))))
            self.tbl_hist.setItem(idx, 4, QTableWidgetItem(str(m.get('unit_name', ''))))

    def _filter_tree(self, text):
        """Filter tree items by search text."""
        text = text.strip().lower()

        def filter_item(item):
            match = False
            for col in range(3):
                if text in item.text(col).lower():
                    match = True
                    break

            child_match = False
            for i in range(item.childCount()):
                if filter_item(item.child(i)):
                    child_match = True

            item.setHidden(not (match or child_match))
            if child_match and text != '':
                item.setExpanded(True)
            return match or child_match

        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))

    def _export_tree(self):
        """Export tree data to Excel via a temp table."""

        def collect(item, rows):
            rows.append((item.text(0), item.text(1), item.text(2)))
            for i in range(item.childCount()):
                collect(item.child(i), rows)

        all_rows = []
        for i in range(self.tree.topLevelItemCount()):
            collect(self.tree.topLevelItem(i), all_rows)

        tmp = QTableWidget()
        tmp.setColumnCount(3)
        tmp.setHorizontalHeaderLabels(('الكود', 'الاسم', 'الاختصاص'))
        for r, data in enumerate(all_rows):
            tmp.insertRow(r)
            for c, val in enumerate(data):
                tmp.setItem(r, c, QTableWidgetItem(val))

        export_table_to_excel(tmp, 'Units_Tree.xlsx')

    def _import_units_from_excel(self):
        df = import_excel_to_dataframe(self)
        if df is None:
            return

        ok_u, units_data = self.api_service.get_units()
        unit_map = {}
        if ok_u:
            for u in units_data:
                unit_map[str(u.get('code')).strip()] = u.get('id')

        success = 0
        fail = 0

        for _, row in df.iterrows():
            code = str(row.get('كود الوحدة', '')).strip()
            name = str(row.get('اسم الوحدة', '')).strip()
            cat = str(row.get('الاختصاص', '')).strip()
            p_code = str(row.get('كود المعسكر الأم', '')).strip()

            if p_code.endswith('.0'):
                p_code = p_code[:-2]
            if p_code == 'nan':
                p_code = ''

            p_id = unit_map.get(p_code)

            ok, res = self.api_service.create_unit({
                'code': code,
                'name': name,
                'category': cat,
                'parent_id': p_id,
            })
            if ok:
                success += 1
            else:
                fail += 1

        # تقريبي: تفصيل شرط ظهور رسالة التنبيه الإضافية غير مؤكد بدقة
        msg = 'تم إضافة ' + str(success) + ' وحدة بنجاح.\nفشل: ' + str(fail)
        if fail:
            msg += "\n\nتأكد أن عمود 'كود المعسكر الأم' يحتوي على كود الوحدة وليس الـ ID من قاعدة البيانات."

        QMessageBox.information(self, 'نتيجة الاستيراد', msg)
        self.load_data()
