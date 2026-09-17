# NOTE: هذا الملف أُعيد بناؤه يدوياً من ملف warehouses_view.pyc
# الملف الأصلي مُصرَّف بصيغة Python 3.14 (RC) التي لا تدعمها أدوات فك التشفير
# الحالية (decompyle3 / uncompyle6 وغيرها). تم استخراج كل الأسماء والنصوص
# والقيم الثابتة والبنية عبر وحدة marshal بدقة كاملة، وأُعيد بناء التسلسل
# المنطقي بالاعتماد عليها وعلى نمط الكود المعتاد في نفس المشروع.
# قد تختلف بعض التفاصيل الدقيقة جداً (مثل ترتيب استدعاءات فرعية بسيطة)
# عن الأصل، لكن الأسماء والنصوص والمنطق العام مطابقون لما استُخرج من البايتكود.

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QHBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
)
from PyQt6.QtCore import Qt

from api_service import ApiService
from theme import make_header_label
from excel_helper import export_table_to_excel, import_excel_to_dataframe, export_template


class WarehousesView(QWidget):

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self._editing_warehouse_id = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(make_header_label('إدارة المستودعات'))

        form_card = QWidget()
        form_card.setObjectName('card')
        form = QFormLayout(form_card)

        self.le_code = QLineEdit()
        self.le_name = QLineEdit()
        self.le_loc = QLineEdit()

        self.cb_type = QComboBox()
        self.cb_type.addItems(('GENERAL', 'FOOD', 'EQUIPMENT', 'MEDICAL'))

        self.cb_unit = QComboBox()

        form.addRow('كود المستودع:', self.le_code)
        form.addRow('اسم المستودع:', self.le_name)
        form.addRow('تصنيف المستودع:', self.cb_type)
        form.addRow('الجهة المستفيدة (المعسكر):', self.cb_unit)
        form.addRow('الموقع:', self.le_loc)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton('💾 تسجيل مستودع جديد')
        self.btn_save.clicked.connect(self.save_warehouse)
        self.btn_cancel = QPushButton('❌ إلغاء التعديل')
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._reset_form)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        layout.addWidget(form_card)
        layout.addLayout(btn_layout)

        toolbar = QHBoxLayout()
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText('بحث بالكود أو الاسم...')
        self.le_search.textChanged.connect(self._filter_table)
        toolbar.addWidget(self.le_search)

        btn_refresh = QPushButton('تحديث 🔄')
        btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(btn_refresh)

        btn_export = QPushButton('📥 تصدير إكسيل')
        btn_export.clicked.connect(lambda: export_table_to_excel(self.table, 'Warehouses.xlsx'))
        toolbar.addWidget(btn_export)

        user = getattr(self.parent(), 'current_user', None) or {}
        is_admin = user.get('role') == 'ADMIN'
        bp = user.get('permissions', {}).get('basic_data', {})

        if is_admin or bp.get('add') or bp.get('create'):
            btn_import = QPushButton('📤 استيراد من إكسل')
            btn_import.clicked.connect(self._import_warehouses_from_excel)
            toolbar.addWidget(btn_import)

        if is_admin or bp.get('export') or bp.get('print'):
            btn_template = QPushButton('📋 تحميل قالب')
            btn_template.clicked.connect(lambda: export_template(
                self, 'warehouses_template.xlsx',
                ('كود المستودع', 'اسم المستودع', 'النوع', 'الموقع', 'كود الجهة المستفيدة'),
                'كود المستودع'
            ))
            toolbar.addWidget(btn_template)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setHorizontalHeaderLabels(
            ('الكود', 'اسم المستودع', 'النوع', 'الموقع', 'المعسكر المربوط', 'إجراء')
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        self.cb_unit.clear()
        self.cb_unit.addItem('بدون (مستودع عام)', None)

        ok_u, units = self.api_service.get_units()
        units = units if ok_u else []
        for u in units:
            self.cb_unit.addItem(u.get('name'), u.get('id'))

        ok_w, data = self.api_service.get_warehouses()
        if not ok_w:
            return

        for idx, wh in enumerate(data):
            self.table.insertRow(idx)
            self.table.setItem(idx, 0, QTableWidgetItem(wh.get('code', '')))
            self.table.setItem(idx, 1, QTableWidgetItem(wh.get('name', '')))
            self.table.setItem(idx, 2, QTableWidgetItem(wh.get('w_type', '')))
            self.table.setItem(idx, 3, QTableWidgetItem(wh.get('location', '') or '-'))

            b_id = wh.get('beneficiary_unit_id')
            camp = next((u for u in units if u['id'] == b_id), None)
            camp_name = camp.get('name') if camp else '-'
            self.table.setItem(idx, 4, QTableWidgetItem(camp_name))

            btn_edit = QPushButton('✉️ تعديل')
            btn_edit.clicked.connect(lambda _, w=wh: self._start_edit(w))
            btn_del = QPushButton('🗑️ حذف')
            btn_del.clicked.connect(lambda _, w=wh: self._delete_warehouse(w))

            btn_box = QWidget()
            btn_lay = QHBoxLayout(btn_box)
            btn_lay.setContentsMargins(0, 0, 0, 0)
            btn_lay.addWidget(btn_edit)
            btn_lay.addWidget(btn_del)
            self.table.setCellWidget(idx, 5, btn_box)

    def _start_edit(self, wh):
        self._editing_warehouse_id = wh.get('id')
        self.le_code.setText(wh.get('code', ''))
        self.le_code.setReadOnly(True)
        self.le_name.setText(wh.get('name', ''))
        self.le_loc.setText(wh.get('location', ''))

        idx_type = self.cb_type.findText(wh.get('w_type', 'GENERAL'))
        self.cb_type.setCurrentIndex(idx_type)

        b_id = wh.get('beneficiary_unit_id')
        idx_unit = self.cb_unit.findData(b_id)
        self.cb_unit.setCurrentIndex(idx_unit)

        self.btn_save.setText('💾 حفظ التعديلات')
        self.btn_cancel.setVisible(True)

    def _reset_form(self):
        self._editing_warehouse_id = None
        self.le_code.clear()
        self.le_code.setReadOnly(False)
        self.le_name.clear()
        self.le_loc.clear()
        self.cb_type.setCurrentIndex(0)
        self.cb_unit.setCurrentIndex(0)
        self.btn_save.setText('💾 تسجيل مستودع جديد')
        self.btn_cancel.setVisible(False)

    def save_warehouse(self):
        payload = {
            'code': self.le_code.text().strip(),
            'name': self.le_name.text().strip(),
            'w_type': self.cb_type.currentText(),
            'location': self.le_loc.text().strip(),
            'beneficiary_unit_id': self.cb_unit.currentData(),
        }

        if not payload['code'] or not payload['name']:
            QMessageBox.warning(self, 'بيانات ناقصة', 'يجب إدخال كود المستودع واسم المستودع على الأقل.')
            return

        if self._editing_warehouse_id:
            ok, msg = self.api_service.update_warehouse(self._editing_warehouse_id, payload)
        else:
            ok, msg = self.api_service.create_warehouse(payload)

        if ok:
            QMessageBox.information(self, 'نجاح', 'تم الحفظ بنجاح.')
            self._reset_form()
            self.load_data()
        else:
            QMessageBox.critical(self, 'خطأ', str(msg))

    def _delete_warehouse(self, wh):
        reply = QMessageBox.question(
            self, 'تأكيد الحذف',
            'هل تريد حذف المستودع: ' + wh.get('name', '') + '\nهذا الإجراء لا يمكن التراجع عنه.'
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = self.api_service._request('DELETE', '/warehouses/' + str(wh.get('id')))
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم حذف المستودع.')
                self.load_data()
            else:
                QMessageBox.critical(self, 'خطأ', str(msg))

    def _filter_table(self, text):
        text = text.strip().lower()
        for r in range(self.table.rowCount()):
            match = False
            for c in range(self.table.columnCount()):
                it = self.table.item(r, c)
                if it and text in it.text().lower():
                    match = True
                    break
            self.table.setRowHidden(r, not match)

    def _import_warehouses_from_excel(self):
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
            code = str(row.get('كود المستودع', '')).strip()
            name = str(row.get('اسم المستودع', '')).strip()
            wtype = str(row.get('النوع', 'GENERAL')).strip().upper()
            loc = str(row.get('الموقع', '')).strip()
            b_code = str(row.get('كود الجهة المستفيدة', '')).strip()

            if b_code.endswith('.0'):
                b_code = b_code[:-2]
            if b_code == 'nan':
                b_code = ''

            b_id = unit_map.get(b_code)

            payload = {
                'code': code,
                'name': name,
                'warehouse_type': wtype,
                'location': loc,
                'beneficiary_unit_id': b_id,
            }

            ok, _ = self.api_service.create_warehouse(payload)
            if ok:
                success += 1
            else:
                fail += 1

        QMessageBox.information(
            self, 'نتيجة الاستيراد',
            'تم إضافة ' + str(success) + ' مستودع بنجاح.\nفشل: ' + str(fail)
        )
        self.load_data()
