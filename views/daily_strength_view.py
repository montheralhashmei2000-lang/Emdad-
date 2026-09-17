# NOTE: هذا الملف أُعيد بناؤه يدوياً من ملف daily_strength_view.pyc
# الملف الأصلي مُصرَّف بصيغة Python 3.14 (RC) التي لا تدعمها أدوات فك التشفير
# الحالية. كما أن هذا الملف تحديداً يستخدم ميزة marshal الجديدة في 3.14
# (تخزين كائنات slice كقيم ثابتة) التي لم تكن مدعومة إطلاقاً حتى في وحدة
# marshal لبايثون 3.12 — احتجت لكتابة قارئ marshal مخصص لفك تشفيره.
# تم استخراج كل الأسماء والنصوص والـ docstrings والقيم الثابتة (بما فيها
# قيمة الـ slice نفسها) بدقة كاملة، وأُعيد بناء المنطق بالاعتماد عليها
# وعلى نمط الملفين السابقين من نفس المشروع (warehouses_view.py و
# beneficiary_units_view.py). الأجزاء الأقل يقيناً معلَّمة بتعليق "تقريبي".

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QHBoxLayout, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QLabel, QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt, QDate

from api_service import ApiService
from theme import make_header_label
from excel_helper import export_table_to_excel
import math


class DailyStrengthView(QWidget):
    """Panel for recording daily strength (Tafreeda) by Camp."""

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self._all_units = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(make_header_label('التفريدة اليومية (حصر القوة بالمعسكرات)'))

        self.tabs = tabs = QTabWidget()

        tab_form = QWidget()
        tab_archive = QWidget()
        tabs.addTab(tab_form, 'تسجيل التفريدة اليومية')
        tabs.addTab(tab_archive, 'أرشيف التفريدات')

        user = getattr(self.parent(), 'current_user', None) or {}
        is_admin = user.get('role', '') == 'ADMIN'
        self._is_admin = is_admin
        self._tabs_perms = user.get('permissions', {}).get('tafreeda', {}).get('tabs', {})
        has_explicit = isinstance(self._tabs_perms, dict) and self._tabs_perms

        form_p = self._tabs_perms.get('tab_form', {}).get('view', False)
        arch_p = self._tabs_perms.get('tab_list', {}).get('view', False)

        # تقريبي: منطق دقيق لشرط إظهار التبويبات
        if has_explicit and not is_admin:
            tabs.setTabVisible(0, form_p)
            tabs.setTabVisible(1, arch_p)

        for i in range(tabs.count()):
            if tabs.isTabVisible(i):
                tabs.setCurrentIndex(i)
                break

        # ---- تبويب تسجيل التفريدة ----
        lay_t = QVBoxLayout(tab_form)
        lay_t.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel('التاريخ:'))
        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.dt_date.dateChanged.connect(self._on_filter_changed)
        self.dt_date.setFixedWidth(120)
        top_row.addWidget(self.dt_date)

        top_row.addWidget(QLabel('المعسكر:'))
        self.cb_camp = QComboBox()
        self.cb_camp.setMinimumWidth(200)
        self.cb_camp.currentIndexChanged.connect(self._on_filter_changed)
        top_row.addWidget(self.cb_camp)

        top_row.addWidget(QLabel('الزيادة %:'))
        self.le_global_pct = QLineEdit('0')
        self.le_global_pct.textChanged.connect(self._recalc_all_rows)
        self.le_global_pct.setFixedWidth(60)
        top_row.addWidget(self.le_global_pct)

        self.btn_clone = QPushButton('📥 استنساخ تفريدة سابقة')
        self.btn_clone.clicked.connect(self._clone_yesterday)
        top_row.addWidget(self.btn_clone)

        top_row.addStretch()
        lay_t.addLayout(top_row)

        self.lbl_warning = QLabel('')
        self.lbl_warning.setStyleSheet('color: red; font-weight: bold; font-size: 13px;')
        self.lbl_warning.hide()
        lay_t.addWidget(self.lbl_warning)

        self.tbl_units = QTableWidget()
        self.tbl_units.setHorizontalHeaderLabels((
            'اسم الوحدة التابعة (الفرعية)', 'القوة الفعلية (أساسي)', 'عدد الزيادة', 'الإجمالي النهائي'
        ))
        self.tbl_units.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_units.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        lay_t.addWidget(self.tbl_units)

        foot_h = QHBoxLayout()
        self.lbl_camp_total = QLabel('إجمالي القوة لكل المعسكر: 0')
        self.lbl_camp_total.setStyleSheet('font-size: 16px; font-weight: bold; color: #C5A028;')
        foot_h.addWidget(self.lbl_camp_total)
        foot_h.addStretch()

        self.btn_print = QPushButton('🖨️ طباعة التفريدة')
        self.btn_print.clicked.connect(self._print_voucher)
        foot_h.addWidget(self.btn_print)

        self.btn_save_form = QPushButton('💾 حفظ تفريدة المعسكر')
        self.btn_save_form.setObjectName('primary_button')
        self.btn_save_form.clicked.connect(self.save_strength_bulk)
        foot_h.addWidget(self.btn_save_form)

        lay_t.addLayout(foot_h)

        # تقريبي: إخفاء أزرار الحفظ/الطباعة حسب صلاحيات تبويب النموذج
        if not is_admin:
            self.btn_save_form.setVisible(form_p and self._tabs_perms.get('tab_form', {}).get('create', False))
            self.btn_print.setVisible(form_p and self._tabs_perms.get('tab_form', {}).get('print', False))

        # ---- تبويب الأرشيف ----
        lay_b = QVBoxLayout(tab_archive)

        bot_head = QHBoxLayout()
        bot_head.addWidget(QLabel('تصفية بالتاريخ:'))
        self.dt_filter_date = QDateEdit()
        self.dt_filter_date.setCalendarPopup(True)
        self.dt_filter_date.dateChanged.connect(self._filter_history_table)
        bot_head.addWidget(self.dt_filter_date)

        bot_head.addWidget(QLabel('  المعسكر:'))
        self.le_filter_camp = QLineEdit()
        self.le_filter_camp.setPlaceholderText('بحث باسم المعسكر...')
        self.le_filter_camp.textChanged.connect(self._filter_history_table)
        bot_head.addWidget(self.le_filter_camp)

        btn_refresh = QPushButton('🔄 تحديث ورؤية الكل')
        btn_refresh.clicked.connect(self._reset_filters_and_fetch)
        bot_head.addWidget(btn_refresh)
        bot_head.addStretch()
        lay_b.addLayout(bot_head)

        self.tbl_history = QTableWidget()
        self.tbl_history.setHorizontalHeaderLabels((
            'التاريخ', 'المعسكر الرئيسي', 'عدد الوحدات الفرعية', 'الأساسي',
            'الزيادات', 'الإجمالي الكلي', 'العمليات'
        ))
        self.tbl_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_history.setAlternatingRowColors(True)
        lay_b.addWidget(self.tbl_history)

        layout.addWidget(tabs)

    def load_data(self):
        ok, units = self.api_service.get_units()
        self._all_units = units if ok else []

        self.cb_camp.blockSignals(True)
        self.cb_camp.clear()
        self.cb_camp.addItem('اختر المعسكر...', None)
        for u in self._all_units:
            if not u.get('parent_id'):
                self.cb_camp.addItem(u.get('code', '') + ' - ' + u.get('name', ''), u.get('id'))
        self.cb_camp.blockSignals(False)

        self.is_editing_mode = False
        self._on_filter_changed()
        self._fetch_summary()

    def _on_filter_changed(self):
        self.tbl_units.setRowCount(0)
        self.lbl_camp_total.setText('إجمالي القوة لكل المعسكر: 0')
        self.lbl_warning.hide()
        self.btn_save_form.setEnabled(True)
        self.btn_save_form.setText('💾 أضف جديد / حفظ')

        camp_id = self.cb_camp.currentData()
        if not camp_id:
            return

        sub_units = [u for u in self._all_units if u.get('parent_id') == camp_id]

        for idx, u in enumerate(sub_units):
            self.tbl_units.insertRow(idx)

            item_name = QTableWidgetItem('🔹 ' + u.get('name', ''))
            item_name.setData(Qt.ItemDataRole.UserRole, u.get('id'))
            item_name.setFlags(item_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tbl_units.setItem(idx, 0, item_name)

            le_count = QLineEdit()
            le_count.setPlaceholderText('القوة الفعلية')
            le_count.textChanged.connect(self._recalc_all_rows)
            self.tbl_units.setCellWidget(idx, 1, le_count)

            le_inc = QLineEdit('0')
            le_inc.setReadOnly(True)
            le_inc.setStyleSheet('background-color: #f0f0f0; color: #333;')
            self.tbl_units.setCellWidget(idx, 2, le_inc)

            lbl_tot = QLabel('0')
            lbl_tot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_units.setCellWidget(idx, 3, lbl_tot)

        target_date = self.dt_date.date().toString(Qt.DateFormat.ISODate)
        ok, db_strengths = self.api_service.get_strength_by_date(camp_id, target_date)

        has_existing = bool(ok and db_strengths)

        if has_existing:
            sub_unit_ids = [u.get('id') for u in sub_units]
            camp_strengths = {}
            for st in db_strengths:
                u_id = st.get('unit_id')
                if u_id in sub_unit_ids:
                    camp_strengths[u_id] = st

            for r in range(self.tbl_units.rowCount()):
                row_uid = self.tbl_units.item(r, 0).data(Qt.ItemDataRole.UserRole)
                st = camp_strengths.get(row_uid)
                if st:
                    le_count = self.tbl_units.cellWidget(r, 1)
                    le_count.blockSignals(True)
                    le_count.setText(str(st.get('soldier_count', '')))
                    le_count.blockSignals(False)

            saved_pct = getattr(self, '_saved_global_pct', '0')
            self.le_global_pct.blockSignals(True)
            self.le_global_pct.setText(str(saved_pct))
            self.le_global_pct.blockSignals(False)

            if self.is_editing_mode:
                self.lbl_warning.setText('✏️ وضع التعديل الفعال: جارٍ تحديث تفريدة موجودة')
                self.lbl_warning.setStyleSheet('color: blue; font-weight: bold; font-size: 14px;')
                self.lbl_warning.show()
                self.btn_save_form.setText('💾 تحديث وحفظ التعديلات')
            else:
                self.lbl_warning.setText(
                    '⚠️ يوجد تفريدة مسجلة مسبقاً لهذا المعسكر في هذا التاريخ. يرجى الذهاب للأرشيف للتعديل.'
                )
                self.lbl_warning.setStyleSheet('color: red; font-weight: bold; font-size: 14px;')
                self.lbl_warning.show()
                self.btn_save_form.setEnabled(False)

        self._recalc_all_rows()

    def _recalc_all_rows(self):
        pct_txt = self.le_global_pct.text().strip()
        try:
            global_pct = float(pct_txt)
        except ValueError:
            global_pct = 0.0

        grand_total = 0
        for r in range(self.tbl_units.rowCount()):
            le_count = self.tbl_units.cellWidget(r, 1)
            le_inc = self.tbl_units.cellWidget(r, 2)
            lbl_tot = self.tbl_units.cellWidget(r, 3)

            c_txt = le_count.text().strip()
            try:
                base_c = int(c_txt)
            except ValueError:
                base_c = 0

            inc = int(math.floor(base_c * global_pct / 100.0 + 0.5))
            le_inc.setText(str(inc))

            tot = base_c + inc
            lbl_tot.setText(str(tot))
            grand_total += tot

        self.lbl_camp_total.setText('إجمالي القوة لكل وحدات المعسكر: ' + str(grand_total))

    def save_strength_bulk(self):
        camp_id = self.cb_camp.currentData()
        if not camp_id:
            QMessageBox.warning(self, 'خطأ', 'يجب تحديد المعسكر أولاً.')
            return

        target_date = self.dt_date.date().toString(Qt.DateFormat.ISODate)

        try:
            gl_pct = float(self.le_global_pct.text().strip() or '0')
        except Exception:
            gl_pct = 0.0

        strengths = []
        for r in range(self.tbl_units.rowCount()):
            uid = self.tbl_units.item(r, 0).data(Qt.ItemDataRole.UserRole)
            le_count = self.tbl_units.cellWidget(r, 1)
            le_inc = self.tbl_units.cellWidget(r, 2)

            try:
                base_cnt = int(le_count.text().strip() or '0')
            except ValueError:
                base_cnt = 0
            try:
                inc_cnt = int(le_inc.text().strip() or '0')
            except ValueError:
                inc_cnt = 0

            strengths.append({
                'unit_id': uid,
                'strength_date': target_date,
                'officer_count': inc_cnt,
                'soldier_count': base_cnt,
                'notes': '',
            })

        if not strengths:
            QMessageBox.warning(self, 'خطأ', 'لا توجد قوة فعلية مدخلة للوحدات.')
            return

        payload = {
            'global_percentage': gl_pct,
            'strengths': strengths,
        }

        ok, msg = self.api_service.enter_daily_strength_bulk(camp_id, payload)
        if ok:
            QMessageBox.information(self, 'نجاح', 'تم حفظ وتحديث التفريدة اليومية بنجاح.')
            self._fetch_summary()
        else:
            QMessageBox.critical(self, 'خطأ', str(msg))

    def _filter_history_table(self):
        target_date = self.dt_filter_date.date().toString(Qt.DateFormat.ISODate)
        camp_text = self.le_filter_camp.text().strip().lower()

        for r in range(self.tbl_history.rowCount()):
            d_item = self.tbl_history.item(r, 0)
            c_item = self.tbl_history.item(r, 1)
            match_d = True
            match_c = True
            if d_item and target_date:
                match_d = target_date in d_item.text()
            if c_item and camp_text:
                match_c = camp_text in c_item.text().lower()
            self.tbl_history.setRowHidden(r, not (match_d and match_c))

    def _reset_filters_and_fetch(self):
        self.le_filter_camp.clear()
        self._fetch_summary()

    def _fetch_summary(self):
        ok, summary = self.api_service._request('GET', '/daily-strength/summary')
        self.tbl_history.setRowCount(0)
        if not ok or not summary:
            return

        summary = summary[:100]

        self.tbl_history.setUpdatesEnabled(False)
        arch_p = getattr(self, '_tabs_perms', {}).get('tab_list', {})

        for i, row in enumerate(summary):
            self.tbl_history.insertRow(i)

            d_str = str(row.get('strength_date', ''))
            self.tbl_history.setItem(i, 0, QTableWidgetItem(d_str))

            c_id = row.get('camp_id')
            camp_name = row.get('camp_name', 'غير محدد')
            self.tbl_history.setItem(i, 1, QTableWidgetItem(camp_name))

            self.tbl_history.setItem(i, 2, QTableWidgetItem(str(row.get('units_count', ''))))
            self.tbl_history.setItem(i, 3, QTableWidgetItem(str(row.get('total_base_count', ''))))
            self.tbl_history.setItem(i, 4, QTableWidgetItem(str(row.get('total_increase_count', ''))))

            t_item = QTableWidgetItem(str(row.get('final_total', '')))
            font = t_item.font()
            font.setBold(True)
            t_item.setFont(font)
            t_item.setForeground(Qt.GlobalColor.darkRed)
            self.tbl_history.setItem(i, 5, t_item)

            action_w = QWidget()
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(0, 0, 0, 0)
            action_l.setSpacing(4)

            btn_view = QPushButton('👁️ عرض')
            btn_view.setStyleSheet('background-color: #3498db; color: white;')
            btn_view.clicked.connect(
                lambda checked=False, c_id=c_id, dt=d_str: self._action_view_edit(c_id, dt, edit_mode=False)
            )
            action_l.addWidget(btn_view)

            btn_edit = QPushButton('✏️ تعديل')
            btn_edit.setStyleSheet('background-color: #f39c12; color: white;')
            btn_edit.clicked.connect(
                lambda checked=False, c_id=c_id, dt=d_str: self._action_view_edit(c_id, dt, edit_mode=True)
            )
            btn_edit.setVisible(self._is_admin or arch_p.get('edit', False))
            action_l.addWidget(btn_edit)

            btn_del = QPushButton('🗑️ حذف')
            btn_del.setStyleSheet('background-color: #e74c3c; color: white;')
            btn_del.clicked.connect(
                lambda checked=False, c_id=c_id, dt=d_str, c_name=camp_name: self._action_delete(c_id, dt, c_name)
            )
            btn_del.setVisible(self._is_admin or arch_p.get('delete', False))
            action_l.addWidget(btn_del)

            btn_ex = QPushButton('📑 إكسيل')
            btn_ex.setStyleSheet('background-color: #27ae60; color: white;')
            btn_ex.clicked.connect(
                lambda checked=False, c_id=c_id, dt=d_str, c_name=camp_name: self._action_export_excel(c_id, dt, c_name)
            )
            btn_ex.setVisible(self._is_admin or arch_p.get('print', False))
            action_l.addWidget(btn_ex)

            self.tbl_history.setCellWidget(i, 6, action_w)

        self.tbl_history.setUpdatesEnabled(True)
        self._filter_history_table()

    def _action_view_edit(self, camp_id, date_str, edit_mode=False):
        self.tabs.setCurrentIndex(0)
        self.dt_date.setDate(QDate.fromString(date_str, Qt.DateFormat.ISODate))
        idx = self.cb_camp.findData(camp_id)
        self.cb_camp.setCurrentIndex(idx)
        self.is_editing_mode = edit_mode
        self._on_filter_changed()

    def _action_delete(self, camp_id, date_str, camp_name):
        ans = QMessageBox.question(
            self, 'تأكيد الحذف',
            'هل أنت متأكد من حذف تفريدة المعسكر (' + camp_name + ') بتاريخ (' + date_str +
            ') بالكامل؟ لا يمكن التراجع عن هذا الإجراء.'
        )
        if ans == QMessageBox.StandardButton.Yes:
            ok, res = self.api_service._request(
                'DELETE', '/daily-strength/camp-strength/' + str(camp_id) + '/' + date_str
            )
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم الحذف بنجاح.')
                self._fetch_summary()
                curr_c = self.cb_camp.currentData()
                curr_d = self.dt_date.date().toString(Qt.DateFormat.ISODate)
                if curr_c == camp_id and curr_d == date_str:
                    self._on_filter_changed()
            else:
                QMessageBox.warning(self, 'خطأ', 'فشل الحذف: ' + str(res))

    def _action_export_excel(self, camp_id, date_str, camp_name):
        ok, db_strengths = self.api_service.get_strength_by_date(camp_id, date_str)
        if not ok or not db_strengths:
            QMessageBox.warning(self, 'تنبيه', 'لا توجد بيانات لهذه التفريدة لتصديرها.')
            return

        sub_unit_ids = [u.get('id') for u in self._all_units if u.get('parent_id') == camp_id]
        camp_strengths = [st for st in db_strengths if st.get('unit_id') in sub_unit_ids]

        if not camp_strengths:
            QMessageBox.warning(self, 'تنبيه', 'بيانات التفريدة فارغة أو لا تخص هذا المعسكر.')
            return

        temp_tbl = QTableWidget()
        temp_tbl.setHorizontalHeaderLabels(('اسم الوحدة', 'القوة الفعلية', 'الزيادة', 'الإجمالي'))
        temp_tbl.setRowCount(len(camp_strengths))

        for i, st in enumerate(camp_strengths):
            u = next((u for u in self._all_units if u.get('id') == st.get('unit_id')), None)
            u_name = u.get('name', 'غير معروف') if u else 'غير معروف'
            base = st.get('soldier_count', 0)
            inc = st.get('officer_count', 0)
            tot = base + inc

            temp_tbl.setItem(i, 0, QTableWidgetItem(u_name))
            temp_tbl.setItem(i, 1, QTableWidgetItem(str(base)))
            temp_tbl.setItem(i, 2, QTableWidgetItem(str(inc)))
            temp_tbl.setItem(i, 3, QTableWidgetItem(str(tot)))

        export_table_to_excel(temp_tbl, 'تفريدة_' + camp_name + '_' + date_str)

    def export_history(self):
        export_table_to_excel(self.tbl_history, 'أرشيف_التفريدات_اليومية')

    def _clone_yesterday(self):
        camp_id = self.cb_camp.currentData()
        if not camp_id:
            QMessageBox.warning(self, 'تنبيه', 'يجب تحديد المعسكر أولاً قبل استنساخ البيانات.')
            return

        prev_date = self.dt_date.date()
        found = False
        prev_str = ''

        for _ in range(30):
            prev_date = prev_date.addDays(-1)
            prev_str = prev_date.toString(Qt.DateFormat.ISODate)
            ok, db_strengths = self.api_service.get_strength_by_date(camp_id, prev_str)
            if ok and db_strengths:
                found = True
                break

        if not found:
            QMessageBox.warning(self, 'تنبيه', 'لم يتم العثور على تفريدات سابقة قريبة لهذا المعسكر لاستنساخها.')
            return

        sub_unit_ids = [u.get('id') for u in self._all_units if u.get('parent_id') == camp_id]
        camp_strengths = {st.get('unit_id'): st for st in db_strengths if st.get('unit_id') in sub_unit_ids}

        self.tbl_units.setUpdatesEnabled(False)
        for r in range(self.tbl_units.rowCount()):
            row_uid = self.tbl_units.item(r, 0).data(Qt.ItemDataRole.UserRole)
            st = camp_strengths.get(row_uid)
            le_count = self.tbl_units.cellWidget(r, 1)
            le_count.blockSignals(True)
            le_count.setText(str(st.get('soldier_count', '0')) if st else '0')
            le_count.blockSignals(False)
        self.tbl_units.setUpdatesEnabled(True)

        self._recalc_all_rows()

        QMessageBox.information(self, 'نجاح', 'تم استنساخ بيانات التفريدة الخاصة بتاريخ ' + prev_str + ' للمعسكر.')

    def _print_voucher(self):
        camp_id = self.cb_camp.currentData()
        if not camp_id:
            QMessageBox.warning(self, 'تنبيه', 'يجب تحديد المعسكر.')
            return

        camp_name = self.cb_camp.currentText().split(' - ')[-1]
        target_date = self.dt_date.date().toString(Qt.DateFormat.ISODate)

        rows_data = []
        tot_base = 0
        tot_inc = 0
        tot_all = 0
        units_count = 0

        for r in range(self.tbl_units.rowCount()):
            u_name = self.tbl_units.item(r, 0).text().replace('🔹 ', '')
            le_count = self.tbl_units.cellWidget(r, 1)
            le_inc = self.tbl_units.cellWidget(r, 2)

            try:
                b_val = int(le_count.text().strip() or '0')
            except ValueError:
                b_val = 0
            try:
                i_val = int(le_inc.text().strip() or '0')
            except ValueError:
                i_val = 0
            t_val = b_val + i_val

            rows_data.append((u_name, b_val, i_val, t_val))
            tot_base += b_val
            tot_inc += i_val
            tot_all += t_val
            units_count += 1

        if tot_all == 0:
            QMessageBox.warning(self, 'تنبيه', 'الجدول فارغ أو التفريدة صفرية! لا شيء لطباعته.')
            return

        from print_helper import print_daily_strength

        print_daily_strength(
            camp_name=camp_name,
            ref_date=target_date,
            global_pct=self.le_global_pct.text().strip(),
            rows_data=rows_data,
            totals={'units': units_count, 'base': tot_base, 'increase': tot_inc, 'grand': tot_all},
            parent=self,
        )
