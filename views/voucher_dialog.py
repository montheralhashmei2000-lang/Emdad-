"""Voucher Details Dialog — نافذة تفاصيل السند."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt


class VoucherDetailsDialog(QDialog):
    """نافذة عرض تفاصيل السند (وارد/صادر/تحويل).

    يمكن استدعاؤها بأشكال مختلفة:
    - VoucherDetailsDialog(type_, items, parent)
    - VoucherDetailsDialog(items, type_, parent)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(kwargs.get('parent') or None)
        # Normalise arguments
        type_ = None
        items = None
        for a in args:
            if isinstance(a, str) and a in ('IN', 'OUT', 'TRANSFER'):
                type_ = a
            elif isinstance(a, (list, tuple, dict)):
                items = a
        type_ = type_ or kwargs.get('type_', 'IN')
        items = items if items is not None else kwargs.get('items', [])

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui(type_, items)

    def _init_ui(self, type_, items):
        type_labels = {
            'IN': 'سند الوارد',
            'OUT': 'سند الصرف',
            'TRANSFER': 'سند التحويل'
        }
        self.setWindowTitle(f"📋 {type_labels.get(type_, type_)}")
        self.resize(700, 450)

        root = QVBoxLayout(self)
        root.setSpacing(10)

        summary_box = QGroupBox("📄 ملخص السند")
        summary_lay = QFormLayout(summary_box)
        lbl_type = QLabel(type_labels.get(type_, type_))
        lbl_type.setStyleSheet("color: #2E7D32; font-weight: bold; font-size: 14px;")
        summary_lay.addRow("نوع السند:", lbl_type)

        count = len(items) if hasattr(items, '__len__') else 0
        lbl_count = QLabel(str(count))
        lbl_count.setStyleSheet("color: #1565C0; font-weight: bold;")
        summary_lay.addRow("عدد الأصناف:", lbl_count)

        root.addWidget(summary_box)
        root.addWidget(QLabel("📦 تفاصيل الأصناف:"))

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(["#", "الكود", "اسم الصنف", "الكمية", "الوحدة"])
        hdr = self.tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tbl.setColumnWidth(0, 40)
        self.tbl.setColumnWidth(1, 100)
        self.tbl.setColumnWidth(3, 80)
        self.tbl.setColumnWidth(4, 80)
        self.tbl.setStyleSheet(
            "QTableWidget { background: #FAFAFA; border: 1px solid #D5C9B8; border-radius: 6px; }"
            "QHeaderView::section { background: #2E7D32; color: white; padding: 6px; font-weight: bold; }"
            "QTableWidget::item { padding: 4px; }"
        )
        root.addWidget(self.tbl)

        self._populate_table(items)

        btns = QHBoxLayout()
        btns.addStretch()

        btn_close = QPushButton("إغلاق")
        btn_close.setStyleSheet(
            "background: #666; color: white; padding: 8px 24px; border-radius: 4px; font-weight: bold;"
        )
        btn_close.clicked.connect(self.close)
        btns.addWidget(btn_close)

        root.addLayout(btns)

    def _populate_table(self, items):
        self.tbl.setRowCount(0)
        if not items:
            self.tbl.setRowCount(1)
            for col, val in enumerate(["—", "—", "(لا توجد أصناف)", "—", "—"]):
                self.tbl.setItem(0, col, QTableWidgetItem(val))
            return

        for idx, item in enumerate(items):
            row = self.tbl.rowCount()
            self.tbl.insertRow(row)
            self.tbl.setItem(row, 0, QTableWidgetItem(str(idx + 1)))

            if isinstance(item, dict):
                self.tbl.setItem(row, 1, QTableWidgetItem(str(item.get('code', item.get('item_code', '—')))))
                self.tbl.setItem(row, 2, QTableWidgetItem(str(item.get('name', item.get('item_name', '—')))))
                self.tbl.setItem(row, 3, QTableWidgetItem(str(item.get('qty', item.get('quantity', '—')))))
                self.tbl.setItem(row, 4, QTableWidgetItem(str(item.get('unit', '—'))))
            elif isinstance(item, (list, tuple)):
                for col, val in enumerate(item[:5]):
                    self.tbl.setItem(row, col, QTableWidgetItem(str(val)))
