"""Transfer View — inter-warehouse stock transfer (3 tabs: new, pending, history)."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDateEdit, QTabWidget, QSizePolicy, QInputDialog
)
from PyQt6.QtCore import Qt, QDate
from api_service import ApiService
from theme import make_header_label, COLORS


class TransferView(QWidget):

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._warehouses_data = []
        self._items_data = []
        self._stock_balance = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        layout.addWidget(make_header_label('تحويل مخزني بين المستودعات'))
        self.tabs = QTabWidget()
        self._tab_form = QWidget()
        self._tab_pending = QWidget()
        self._tab_history = QWidget()
        self.tabs.addTab(self._tab_form, 'سند تحويل جديد')
        self.tabs.addTab(self._tab_pending, 'التحويلات المعلقة')
        self.tabs.addTab(self._tab_history, 'سجل التحويلات')
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._build_form_tab()
        self._build_pending_tab()
        self._build_history_tab()
        layout.addWidget(self.tabs)

    def _build_form_tab(self):
        H = QHBoxLayout
        mv = QVBoxLayout(self._tab_form)
        mv.setContentsMargins(10, 10, 10, 10)
        mv.setSpacing(10)
        card = QWidget()
        card.setObjectName('card')
        card.setStyleSheet('QWidget#card { background: white; border-radius: 6px; border: 1px solid #ddd; }')
        g = QGridLayout(card)
        g.setColumnStretch(1, 1)
        g.setColumnStretch(3, 1)
        self.cb_src = QComboBox()
        self.cb_src.setFixedHeight(30)
        self.cb_src.currentIndexChanged.connect(self._on_src_changed)
        self.cb_dst = QComboBox()
        self.cb_dst.setFixedHeight(30)
        self.le_ref = QLineEdit()
        self.le_ref.setPlaceholderText('اختياري')
        self.dt_date = QDateEdit()
        self.dt_date.setCalendarPopup(True)
        self.dt_date.setDate(QDate.currentDate())
        self.le_notes = QLineEdit()
        g.addWidget(QLabel('من المستودع:'), 0, 0)
        g.addWidget(self.cb_src, 0, 1)
        g.addWidget(QLabel('إلى المستودع:'), 0, 2)
        g.addWidget(self.cb_dst, 0, 3)
        g.addWidget(QLabel('المرجع:'), 1, 0)
        g.addWidget(self.le_ref, 1, 1)
        g.addWidget(QLabel('التاريخ:'), 1, 2)
        g.addWidget(self.dt_date, 1, 3)
        g.addWidget(QLabel('ملاحظات:'), 2, 0)
        g.addWidget(self.le_notes, 2, 1, 1, 3)
        mv.addWidget(card)
        bb = H()
        bsave = QPushButton('💾 اعتماد التحويل')
        bsave.setStyleSheet('background-color: #C5A028; color: white; padding: 8px 16px; font-weight: bold; border-radius: 4px;')
        bsave.clicked.connect(lambda: self._save(False))
        bb.addWidget(bsave)
        bdraft = QPushButton('📝 حفظ كمسودة')
        bdraft.setStyleSheet('background-color: #f39c12; color: white; padding: 8px 16px;')
        bdraft.clicked.connect(lambda: self._save(True))
        bb.addWidget(bdraft)
        bnew = QPushButton('🔄 سند جديد')
        bnew.clicked.connect(self._reset_form)
        bb.addWidget(bnew)
        badd = QPushButton('+ إضافة صنف')
        badd.setStyleSheet('background-color: #2E6B35; color: white; padding: 8px 16px;')
        badd.clicked.connect(self._add_row)
        bb.addWidget(badd)
        bb.addStretch()
        mv.addLayout(bb)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ('كود الصنف', 'اسم الصنف', 'الوحدة', 'المتاح', 'الكمية', 'حذف'))
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(self._on_cell_changed)
        mv.addWidget(self.table)
        hint = QLabel('💡 أدخل كود الصنف في العمود الأول — سيظهر الاسم والوحدة تلقائياً.')
        hint.setStyleSheet('color: #888C7A; font-size: 11px;')
        mv.addWidget(hint)

    def _build_pending_tab(self):
        ly = QVBoxLayout(self._tab_pending)
        ly.setContentsMargins(10, 10, 10, 10)
        hb = QHBoxLayout()
        hb.addWidget(QLabel('مستودعي (الوارد):'))
        self.cb_pending_wh = QComboBox()
        self.cb_pending_wh.setFixedWidth(280)
        self.cb_pending_wh.currentIndexChanged.connect(self._load_pending)
        hb.addWidget(self.cb_pending_wh)
        bref = QPushButton('تحديث 🔄')
        bref.clicked.connect(self._load_pending)
        hb.addWidget(bref)
        hb.addStretch()
        ly.addLayout(hb)
        self.tbl_pending = QTableWidget()
        self.tbl_pending.setColumnCount(7)
        self.tbl_pending.setHorizontalHeaderLabels(
            ('التاريخ', 'المصدر', 'الكود', 'الصنف', 'الكمية', 'الحالة', 'إجراء'))
        self.tbl_pending.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_pending.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        ly.addWidget(self.tbl_pending)

    def _build_history_tab(self):
        ly = QVBoxLayout(self._tab_history)
        ly.setContentsMargins(10, 10, 10, 10)
        hb = QHBoxLayout()
        hb.addWidget(QLabel('من:'))
        self.dt_hist_from = QDateEdit()
        self.dt_hist_from.setCalendarPopup(True)
        self.dt_hist_from.setDate(QDate.currentDate().addMonths(-1))
        hb.addWidget(self.dt_hist_from)
        hb.addWidget(QLabel('إلى:'))
        self.dt_hist_to = QDateEdit()
        self.dt_hist_to.setCalendarPopup(True)
        self.dt_hist_to.setDate(QDate.currentDate())
        hb.addWidget(self.dt_hist_to)
        bshow = QPushButton('عرض 📋')
        bshow.clicked.connect(self._load_history)
        hb.addWidget(bshow)
        hb.addStretch()
        ly.addLayout(hb)
        self.tbl_hist = QTableWidget()
        self.tbl_hist.setColumnCount(6)
        self.tbl_hist.setHorizontalHeaderLabels(
            ('التاريخ', 'من', 'إلى', 'الصنف', 'الكمية', 'الحالة'))
        self.tbl_hist.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl_hist.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        ly.addWidget(self.tbl_hist)
        ly.addWidget(self.tbl_hist)

    # ──────────────────────────────────────────── data loading
    def load_data(self):
        ok, wh = self.api_service.get_warehouses(500)
        if ok:
            self._warehouses_data = wh or []
            for cb in (self.cb_src, self.cb_dst, self.cb_pending_wh):
                cb.blockSignals(True)
                cb.clear()
                for w in self._warehouses_data:
                    cb.addItem(f"{w.get('code','')} - {w.get('name','')}", w.get('id'))
                cb.blockSignals(False)
            if self.cb_dst.count() > 1:
                self.cb_dst.setCurrentIndex(1)
        ok2, it = self.api_service.get_items(500)
        if ok2:
            self._items_data = it or []
        if self.cb_src.currentIndex() >= 0:
            self._refresh_balance()

    def _on_tab_changed(self, idx):
        if idx == 1:
            self._load_pending()
        elif idx == 2:
            self._load_history()

    def _on_src_changed(self, _):
        self._refresh_balance()

    def _refresh_balance(self):
        wid = self.cb_src.currentData()
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

    def _find_item(self, code):
        for it in (self._items_data or []):
            if str(it.get('code', '')) == code:
                return it
        return None

    # ──────────────────────────────────────────── grid helpers
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
        del_btn = QPushButton('🗑️')
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

    def _reset_form(self):
        self.le_ref.clear()
        self.le_notes.clear()
        self.dt_date.setDate(QDate.currentDate())
        self.table.setRowCount(0)


    def _reset_form(self):
        self.le_ref.clear()
        self.le_notes.clear()
        self.dt_date.setDate(QDate.currentDate())
        self.table.setRowCount(0)

    # ──────────────────────────────────────────── save
    def _collect_lines(self):
        for r in range(self.table.rowCount()):
            code = (self.table.item(r, 0) or QTableWidgetItem()).text().strip()
            if not code:
                continue
            try:
                qty = float((self.table.item(r, 4) or QTableWidgetItem()).text() or 0)
            except ValueError:
                return [], f'الكمية في السطر {r+1} غير صحيحة.'
            if qty <= 0:
                return [], f'الكمية في السطر {r+1} يجب أن تكون أكبر من صفر.'
            avail = self._avail(code)
            if qty > avail:
                nm = (self.table.item(r, 1) or QTableWidgetItem()).text()
                return [], f'الكمية المطلوبة ({qty}) من "{nm}" أكبر من المتاح ({avail}).'
        lines = []
        for r in range(self.table.rowCount()):
            code = (self.table.item(r, 0) or QTableWidgetItem()).text().strip()
            if not code:
                continue
            qty = float((self.table.item(r, 4) or QTableWidgetItem()).text() or 0)
            lines.append({'item_code': code, 'quantity': qty})
        return lines, None

    def _save(self, is_draft):
        src = self.cb_src.currentData()
        dst = self.cb_dst.currentData()
        if not src or not dst:
            QMessageBox.warning(self, 'بيانات ناقصة', 'اختر المستودع المصدر والهدف.')
            return
        if src == dst:
            QMessageBox.warning(self, 'خطأ', 'لا يمكن التحويل إلى نفس المستودع.')
            return
        lines, err = self._collect_lines()
        if err:
            QMessageBox.warning(self, 'خطأ', err)
            return
        if not lines:
            QMessageBox.information(self, 'لا أصناف', 'أضف صنفاً واحداً على الأقل.')
            return
        payload = {
            'from_warehouse_id': src,
            'to_warehouse_id': dst,
            'reference': self.le_ref.text().strip(),
            'notes': self.le_notes.text().strip(),
            'movement_date': self.dt_date.date().toString('yyyy-MM-dd'),
            'is_draft': is_draft,
            'lines': lines,
        }
        try:
            if len(lines) == 1:
                ok, resp = self.api_service.transfer_stock(payload)
            else:
                ok, resp = self.api_service.transfer_stock_bulk(payload)
        except AttributeError:
            ok, resp = False, 'API method غير متوفر'
        if ok:
            QMessageBox.information(
                self, 'نجاح',
                'تم حفظ التحويل بنجاح.' + (' (مسودة)' if is_draft else ''))
            self._reset_form()
        else:
            QMessageBox.critical(self, 'فشل', str(resp))

    # ──────────────────────────────────────────── pending
    def _load_pending(self):
        wid = self.cb_pending_wh.currentData()
        if not wid:
            return
        ok, rows = self.api_service.get_pending_transfers(wid)
        self.tbl_pending.setRowCount(0)
        if not ok:
            return
        for idx, m in enumerate(rows or []):
            self.tbl_pending.insertRow(idx)
            self.tbl_pending.setItem(idx, 0, QTableWidgetItem(str(m.get('movement_date', ''))))
            self.tbl_pending.setItem(idx, 1, QTableWidgetItem(str(m.get('source_warehouse_name', ''))))
            self.tbl_pending.setItem(idx, 2, QTableWidgetItem(str(m.get('item_code', ''))))
            self.tbl_pending.setItem(idx, 3, QTableWidgetItem(str(m.get('item_name', ''))))
            self.tbl_pending.setItem(idx, 4, QTableWidgetItem(str(m.get('quantity', ''))))
            self.tbl_pending.setItem(idx, 5, QTableWidgetItem(str(m.get('status', 'PENDING'))))
            cell = QWidget()
            bl = QHBoxLayout(cell)
            bl.setContentsMargins(0, 0, 0, 0)
            ba = QPushButton('✅ قبول')
            ba.setStyleSheet('background-color: #27AE60; color: white;')
            ba.clicked.connect(lambda _, mv=m: self._accept(mv))
            br = QPushButton('❌ رفض')
            br.setStyleSheet('background-color: #C0392B; color: white;')
            br.clicked.connect(lambda _, mv=m: self._reject(mv))
            bl.addWidget(ba)
            bl.addWidget(br)
            self.tbl_pending.setCellWidget(idx, 6, cell)

    def _accept(self, m):
        reply = QMessageBox.question(
            self, 'تأكيد',
            'هل تقبل التحويل الوارد؟',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok, resp = self.api_service.accept_transfer({'movement_id': m.get('id')})
        if ok:
            QMessageBox.information(self, 'نجاح', 'تم قبول التحويل.')
            self._load_pending()
        else:
            QMessageBox.critical(self, 'فشل', str(resp))

    def _reject(self, m):
        reason, ok = QInputDialog.getMultiLineText(self, 'سبب الرفض', 'أدخل السبب:')
        if not ok or not reason.strip():
            return
        ok, resp = self.api_service.reject_draft(m.get('id'), reason.strip())
        if ok:
            QMessageBox.information(self, 'تم', 'تم رفض التحويل.')
            self._load_pending()
        else:
            QMessageBox.critical(self, 'فشل', str(resp))

    # ──────────────────────────────────────────── history
    def _load_history(self):
        params = {
            'date_from': self.dt_hist_from.date().toString('yyyy-MM-dd'),
            'date_to': self.dt_hist_to.date().toString('yyyy-MM-dd'),
        }
        ok, rows = self.api_service.report_transfers_history(params)
        if not ok:
            ok2, all_m = self.api_service.get_movements(500)
            if not ok2:
                QMessageBox.warning(self, 'خطأ', str(all_m))
                return
            rows = [
                m for m in (all_m or [])
                if m.get('movement_type') == 'TRANSFER'
                and m.get('movement_date', '') >= params['date_from']
                and m.get('movement_date', '') <= params['date_to']
            ]
        self.tbl_hist.setRowCount(0)
        for idx, m in enumerate(rows or []):
            self.tbl_hist.insertRow(idx)
            self.tbl_hist.setItem(idx, 0, QTableWidgetItem(str(m.get('movement_date', ''))))
            self.tbl_hist.setItem(idx, 1, QTableWidgetItem(
                str(m.get('source_warehouse_name', m.get('warehouse_name', '')))))
            self.tbl_hist.setItem(idx, 2, QTableWidgetItem(str(m.get('dest_warehouse_name', ''))))
            self.tbl_hist.setItem(idx, 3, QTableWidgetItem(
                str(m.get('item_name', m.get('item_code', '')))))
            self.tbl_hist.setItem(idx, 4, QTableWidgetItem(str(m.get('quantity', ''))))
            self.tbl_hist.setItem(idx, 5, QTableWidgetItem(str(m.get('status', 'POSTED'))))

        if not ok or not reason.strip():
            return
        ok, resp = self.api_service.reject_draft(m.get('id'), reason.strip())
        if ok:
            QMessageBox.information(self, 'تم', 'تم رفض التحويل.')
            self._load_pending()
        else:
            QMessageBox.critical(self, 'فشل', str(resp))

