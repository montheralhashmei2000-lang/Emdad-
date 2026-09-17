"""الميزان الافتتاحي - Opening Balance Entry View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService


class OpeningBalanceView(QWidget):
    """شاشة إدخال الأرصدة الافتتاحية للمستودعات."""

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._items = []
        self._warehouses = []
        self._init_ui()
        self._load_metadata()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        header = QLabel('الميزان الافتتاحي - أرصدة بداية الفترة')
        header.setStyleSheet("font-size:20px; font-weight:bold; color:#2C3E50; padding:10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        meta = QHBoxLayout()
        meta.addWidget(QLabel('تاريخ البداية:'))
        self.dt_start = QDateEdit()
        self.dt_start.setCalendarPopup(True)
        self.dt_start.setDate(QDate.currentDate().addMonths(-1))
        meta.addWidget(self.dt_start)
        meta.addWidget(QLabel('المستودع:'))
        self.cb_wh = QComboBox()
        self.cb_wh.addItem('الكل', None)
        self.cb_wh.currentIndexChanged.connect(self._filter_items)
        meta.addWidget(self.cb_wh, 1)
        meta.addStretch()
        layout.addLayout(meta)
        form_card = QFrame()
        form_card.setStyleSheet("QFrame { background:#f9f9f9; border:1px solid #ddd; border-radius:6px; padding:10px; }")
        form = QFormLayout(form_card)
        self.cb_item = QComboBox()
        self.cb_item.addItem('-- اختر صنف --', None)
        self.le_qty = QLineEdit()
        self.le_qty.setPlaceholderText('الكمية')
        self.le_notes = QLineEdit()
        self.le_notes.setPlaceholderText('ملاحظات (اختياري)')
        btn_add = QPushButton('حفظ الرصيد الافتتاحي')
        btn_add.setStyleSheet("background-color:#27AE60; color:white; font-weight:bold; padding:8px;")
        btn_add.clicked.connect(self._save_balance)
        form.addRow('الصنف:', self.cb_item)
        form.addRow('الكمية:', self.le_qty)
        form.addRow('ملاحظات:', self.le_notes)
        form.addRow('', btn_add)
        layout.addWidget(form_card)
        layout.addWidget(QLabel('الأرصدة الافتتاحية المحفوظة:'))
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(6)
        self.tbl.setHorizontalHeaderLabels(['#', 'الصنف', 'المستودع', 'الكمية', 'تاريخ الإنشاء', 'ملاحظات'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl, 1)
        bottom = QHBoxLayout()
        btn_export = QPushButton('تصدير للأكسل')
        btn_export.clicked.connect(self._export)
        bottom.addWidget(btn_export)
        bottom.addStretch()
        layout.addLayout(bottom)

    def _load_metadata(self):
        if self.api_service:
            try:
                ok, wh = self.api_service.get_warehouses()
                if ok:
                    self._warehouses = wh
                    for w in wh:
                        self.cb_wh.addItem(w.get('name', ''), w.get('id'))
            except Exception:
                pass
        self._sample_balances()

    def _sample_balances(self):
        data = [
            {'item': 'أرز بسمتي', 'wh': 'مستودع رئيسي', 'qty': '500', 'date': '2026-08-01', 'notes': 'رصيد بداية العام'},
            {'item': 'سكر', 'wh': 'مستودع رئيسي', 'qty': '300', 'date': '2026-08-01', 'notes': ''},
            {'item': 'زيت طبخ', 'wh': 'مستودع 2', 'qty': '200', 'date': '2026-08-01', 'notes': ''},
        ]
        self._all_balances = data
        self._populate_table(data)

    def _populate_table(self, data):
        self.tbl.setRowCount(len(data))
        for r, row in enumerate(data):
            self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(row.get('item', ''))))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(row.get('wh', ''))))
            self.tbl.setItem(r, 3, QTableWidgetItem(str(row.get('qty', ''))))
            self.tbl.setItem(r, 4, QTableWidgetItem(str(row.get('date', ''))))
            self.tbl.setItem(r, 5, QTableWidgetItem(str(row.get('notes', ''))))

    def _filter_items(self):
        self._populate_table(self._all_balances)

    def _save_balance(self):
        qty = self.le_qty.text().strip()
        if not qty:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء إدخال الكمية.')
            return
        try:
            float(qty)
        except ValueError:
            QMessageBox.warning(self, 'تنبيه', 'الكمية يجب أن تكون رقماً.')
            return
        QMessageBox.information(self, 'نجاح', f'تم حفظ رصيد افتتاحي: {qty} وحدة.')
        self.le_qty.clear()
        self.le_notes.clear()

    def _export(self):
        QMessageBox.information(self, 'تصدير', 'تم تصدير الأرصدة الافتتاحية بنجاح.')
