"""التقارير - Reports View."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QDateEdit, QMessageBox,
    QGroupBox, QFrame, QGridLayout, QFormLayout, QStackedWidget)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from ui.api_service import ApiService
from ui.theme import make_header_label


class ReportsView(QWidget):
    """شاشة التقارير المتنوعة."""

    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label('مركز التقارير'))
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel('التاريخ من:'))
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-30))
        toolbar.addWidget(self.dt_from)
        toolbar.addWidget(QLabel('إلى:'))
        self.dt_to = QDateEdit()
        self.dt_to.setCalendarPopup(True)
        self.dt_to.setDate(QDate.currentDate())
        toolbar.addWidget(self.dt_to)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        cards = QGridLayout()
        cards.setSpacing(15)
        self._reports = [
            ('📦', 'تقرير المخزون', 'حالة المخزون الحالية', 'stock'),
            ('📥', 'تقرير الاستلامات', 'إذونات الاستلام', 'receive'),
            ('📤', 'تقرير الصرف', 'إذونات الصرف للوحدات', 'issue'),
            ('↩️', 'تقرير المرتجعات', 'واردة وصادرة', 'returns'),
            ('📊', 'تقرير الحركة', 'حركة المخزون', 'movements'),
            ('💰', 'تقرير القيمة', 'قيمة المخزون', 'valuation'),
            ('👥', 'تقرير الموردين', 'الموردين النشطين', 'suppliers'),
            ('⚠️', 'تقرير النواقص', 'الأصناف تحت الحد الأدنى', 'low_stock'),
            ('📋', 'الجرد التفصيلي', 'كميات حسب المخزن', 'inventory'),
            ('📑', 'تقرير مخصص', 'تصميم استعلام خاص', 'custom'),
        ]
        for i, (icon, title, desc, key) in enumerate(self._reports):
            card = self._make_card(icon, title, desc, key)
            cards.addWidget(card, i // 4, i % 4)
        layout.addLayout(cards)
        result_box = QGroupBox('نتائج التقرير')
        result_lay = QVBoxLayout(result_box)
        self.stack = QStackedWidget()
        self.lbl_default = QLabel('اختر تقريراً لعرض النتائج')
        self.lbl_default.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_default.setStyleSheet('color:#999; font-size:14pt; padding:30px;')
        self.stack.addWidget(self.lbl_default)
        self.tbl_result = QTableWidget()
        self.stack.addWidget(self.tbl_result)
        result_lay.addWidget(self.stack)
        self.lbl_summary = QLabel('')
        self.lbl_summary.setStyleSheet('color:#1565C0; font-weight:bold;')
        result_lay.addWidget(self.lbl_summary)
        layout.addWidget(result_box, 1)
        action_bar = QHBoxLayout()
        btn_print = QPushButton('🖨️ طباعة')
        btn_print.clicked.connect(self._print)
        action_bar.addWidget(btn_print)
        btn_export = QPushButton('📤 تصدير Excel')
        btn_export.clicked.connect(self._export_excel)
        action_bar.addWidget(btn_export)
        btn_pdf = QPushButton('📄 PDF')
        btn_pdf.clicked.connect(self._export_pdf)
        action_bar.addWidget(btn_pdf)
        layout.addLayout(action_bar)

    def _make_card(self, icon, title, desc, key):
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet('QFrame { background:#fff; border:1px solid #E0E0E0; border-radius:8px; padding:10px; }'
                          'QFrame:hover { background:#E3F2FD; border:1px solid #2196F3; }')
        lay = QVBoxLayout(card)
        lay.setSpacing(5)
        lbl = QLabel(f'{icon} {title}')
        lbl.setStyleSheet('font-size:13pt; font-weight:bold; color:#1565C0;')
        lay.addWidget(lbl)
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet('color:#666; font-size:9pt;')
        lay.addWidget(desc_lbl)
        lay.addStretch()
        card.mousePressEvent = lambda e, k=key, t=title: self._run_report(k, t)
        return card

    def _run_report(self, key, title):
        try:
            date_from = self.dt_from.date().toString('yyyy-MM-dd')
            date_to = self.dt_to.date().toString('yyyy-MM-dd')
            if key == 'stock':
                ok, data = self.api._request('GET', '/api/inventory', params={'limit': 500})
                self._show_table(data or [], ['item_code', 'item_name', 'warehouse', 'quantity', 'unit'])
            elif key == 'receive':
                ok, data = self.api.get_movements(limit=200)
                data = [d for d in (data or []) if d.get('movement_type') == 'RECEIVE']
                self._show_table(data, ['date', 'ref_number', 'warehouse_id', 'items'])
            elif key == 'issue':
                ok, data = self.api.get_movements(limit=200)
                data = [d for d in (data or []) if d.get('movement_type') == 'ISSUE']
                self._show_table(data, ['date', 'ref_number', 'unit_id', 'items'])
            elif key == 'returns':
                ok, data = self.api._request('GET', '/api/stock/returns', params={'limit': 200})
                self._show_table(data or [], ['return_date', 'return_type', 'ref_number', 'reason'])
            elif key == 'movements':
                ok, data = self.api.get_movements(limit=500)
                self._show_table(data or [], ['date', 'movement_type', 'ref_number', 'item_id', 'quantity'])
            elif key == 'valuation':
                ok, data = self.api._request('GET', '/api/inventory/valuation')
                self._show_table(data if isinstance(data, list) else [data] if data else [], ['item', 'quantity', 'unit_price', 'total'])
            elif key == 'suppliers':
                ok, data = self.api.get_suppliers()
                self._show_table(data or [], ['code', 'name', 'phone', 'is_active'])
            elif key == 'low_stock':
                ok, data = self.api._request('GET', '/api/inventory', params={'low_stock': 'true', 'limit': 500})
                self._show_table(data or [], ['item_code', 'item_name', 'quantity', 'min_quantity'])
            elif key == 'inventory':
                ok, data = self.api._request('GET', '/api/inventory', params={'limit': 500})
                self._show_table(data or [], ['item_code', 'item_name', 'warehouse', 'quantity', 'unit', 'batch'])
            elif key == 'custom':
                QMessageBox.information(self, 'تقرير مخصص',
                    'يمكنك استخدام API التالي:\nGET /api/reports/custom?from=...&to=...&fields=...')
                return
            self.stack.setCurrentIndex(1)
            self.lbl_summary.setText(f"✅ تقرير: {title} | الفترة: {date_from} إلى {date_to}")
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', str(e))

    def _show_table(self, data, fields):
        if not data:
            self.tbl_result.setColumnCount(len(fields))
            self.tbl_result.setHorizontalHeaderLabels(fields)
            self.tbl_result.setRowCount(0)
            return
        self.tbl_result.setColumnCount(len(fields) + 1)
        headers = ['#'] + [f for f in fields]
        self.tbl_result.setHorizontalHeaderLabels(headers)
        self.tbl_result.setRowCount(len(data))
        for r, row in enumerate(data):
            self.tbl_result.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            for c, f in enumerate(fields):
                val = row.get(f) if isinstance(row, dict) else '-'
                if isinstance(val, (list, dict)):
                    val = str(len(val)) if isinstance(val, list) else str(val)
                self.tbl_result.setItem(r, c + 1, QTableWidgetItem(str(val)))
        self.tbl_result.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _print(self):
        QMessageBox.information(self, 'طباعة', 'سيتم فتح نافذة الطباعة...')

    def _export_excel(self):
        try:
            from PyQt6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getSaveFileName(self, 'تصدير', '', 'Excel (*.xlsx)')
            if not path:
                return
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = 'تقرير'
                for c in range(self.tbl_result.columnCount()):
                    ws.cell(row=1, column=c + 1, value=self.tbl_result.horizontalHeaderItem(c).text())
                for r in range(self.tbl_result.rowCount()):
                    for c in range(self.tbl_result.columnCount()):
                        item = self.tbl_result.item(r, c)
                        ws.cell(row=r + 2, column=c + 1, value=item.text() if item else '')
                wb.save(path)
                QMessageBox.information(self, 'نجاح', f'تم التصدير إلى:\n{path}')
            except ImportError:
                QMessageBox.warning(self, 'تنبيه', 'openpyxl غير مثبت')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', str(e))

    def _export_pdf(self):
        QMessageBox.information(self, 'PDF', 'سيتم التصدير إلى PDF...')


    def _make_card(self, icon, title, desc, key):
        f = QFrame()
        f.setStyleSheet('''QFrame {
            background-color: white;
            border: 2px solid #E0E0E0;
            border-radius: 8px;
            padding: 10px;
        }
        QFrame:hover {
            border: 2px solid #1565C0;
            background-color: #F5F9FF;
        }''')
        f.setCursor(Qt.CursorShape.PointingHandCursor)
        v = QVBoxLayout(f)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet('font-size:32pt;')
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(icon_lbl)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet('font-size:11pt; font-weight:bold; color:#1A237E;')
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(title_lbl)
        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet('color:#666; font-size:9pt;')
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        v.addWidget(desc_lbl)
        f.mousePressEvent = lambda e, k=key, t=title: self._run_report(k, t)
        return f
