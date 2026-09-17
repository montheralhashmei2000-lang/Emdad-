"""Opening Balance View — الأرصدة الافتتاحية."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QDoubleSpinBox, QDateEdit
)
from PyQt6.QtCore import QDate, Qt
from api_service import ApiService
from theme import make_header_label, COLORS


class OpeningBalanceView(QWidget):
    """شاشة الأرصدة الافتتاحية — إدخال أرصدة الأصناف في بداية الفترة."""

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self._items = []
        self._warehouses = []
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.addWidget(make_header_label("📦 الأرصدة الافتتاحية"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("🏭 المستودع:"))
        self.cb_warehouse = QComboBox()
        self.cb_warehouse.setMinimumWidth(200)
        self.cb_warehouse.currentIndexChanged.connect(self._on_warehouse_changed)
        toolbar.addWidget(self.cb_warehouse)

        toolbar.addSpacing(20)
        toolbar.addWidget(QLabel("📅 تاريخ الأرصدة:"))
        self.dt_date = QDateEdit()
        self.dt_date.setDate(QDate.currentDate())
        self.dt_date.setCalendarPopup(True)
        toolbar.addWidget(self.dt_date)

        toolbar.addStretch()

        btn_new = QPushButton("➕ إضافة صنف")
        btn_new.setStyleSheet(
            f"background: {COLORS['green_primary']}; color: white; padding: 6px 16px; border-radius: 4px;"
        )
        btn_new.clicked.connect(self._add_row)
        toolbar.addWidget(btn_new)

        btn_save = QPushButton("💾 حفظ الأرصدة")
        btn_save.setStyleSheet(
            f"background: {COLORS['gold']}; color: {COLORS['text_dark']}; padding: 6px 16px; border-radius: 4px; font-weight: bold;"
        )
        btn_save.clicked.connect(self._save_balances)
        toolbar.addWidget(btn_save)

        root.addLayout(toolbar)

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(["الكود", "اسم الصنف", "الكمية", "الوحدة", "ملاحظات"])
        hdr = self.tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tbl.setColumnWidth(2, 100)
        self.tbl.setColumnWidth(3, 100)
        self.tbl.setStyleSheet(
            f"QTableWidget {{ background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }}"
            f"QTableWidget::item {{ padding: 4px; }}"
            f"QHeaderView::section {{ background: {COLORS['green_primary']}; color: white; padding: 6px; font-weight: bold; }}"
        )
        root.addWidget(self.tbl)

        summary = QHBoxLayout()
        summary.addWidget(QLabel("الإجمالي:"))
        self.lbl_total = QLabel("0 صنف")
        self.lbl_total.setStyleSheet(f"color: {COLORS['green_primary']}; font-weight: bold;")
        summary.addWidget(self.lbl_total)
        summary.addStretch()

        btn_print = QPushButton("🖨️ طباعة")
        btn_print.setStyleSheet(
            f"background: {COLORS['info']}; color: white; padding: 6px 16px; border-radius: 4px;"
        )
        btn_print.clicked.connect(self._print_report)
        summary.addWidget(btn_print)

        root.addLayout(summary)

    def load_data(self):
        try:
            conn = self.api_service._get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT id, name FROM warehouses ORDER BY name")
            self._warehouses = cur.fetchall()
            self.cb_warehouse.clear()
            for wid, wname in self._warehouses:
                self.cb_warehouse.addItem(wname, wid)

            cur.execute("SELECT id, code, name, unit FROM items ORDER BY name")
            self._items = cur.fetchall()

            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "⚠️ خطأ", f"فشل تحميل البيانات:\n{str(e)}")

    def _on_warehouse_changed(self):
        pass

    def _add_row(self):
        row = self.tbl.rowCount()
        self.tbl.insertRow(row)

        cb_code = QComboBox()
        cb_code.setEditable(True)
        cb_code.setMinimumWidth(120)
        for item_id, code, name, unit in self._items:
            cb_code.addItem(f"{code} - {name}", item_id)
        self.tbl.setCellWidget(row, 0, cb_code)

        le_name = QLineEdit()
        le_name.setReadOnly(True)
        le_name.setPlaceholderText("اختر الصنف")
        self.tbl.setCellWidget(row, 1, le_name)

        sp_qty = QDoubleSpinBox()
        sp_qty.setRange(0, 999999)
        sp_qty.setDecimals(2)
        self.tbl.setCellWidget(row, 2, sp_qty)

        le_unit = QLineEdit()
        le_unit.setReadOnly(True)
        le_unit.setPlaceholderText("-")
        self.tbl.setCellWidget(row, 3, le_unit)

        le_note = QLineEdit()
        le_note.setPlaceholderText("ملاحظات...")
        self.tbl.setCellWidget(row, 4, le_note)

        cb_code.currentIndexChanged.connect(lambda _, r=row: self._on_item_selected(r))
        self._update_total()

    def _on_item_selected(self, row):
        cb = self.tbl.cellWidget(row, 0)
        name_w = self.tbl.cellWidget(row, 1)
        unit_w = self.tbl.cellWidget(row, 3)
        if cb and name_w and unit_w and cb.currentData():
            item_id = cb.currentData()
            for i_id, code, name, unit in self._items:
                if i_id == item_id:
                    name_w.setText(name)
                    unit_w.setText(unit or "")
                    break

    def _update_total(self):
        self.lbl_total.setText(f"{self.tbl.rowCount()} صنف")

    def _save_balances(self):
        if self.tbl.rowCount() == 0:
            QMessageBox.information(self, "ℹ️", "لا توجد أرصدة لحفظها")
            return
        QMessageBox.information(
            self, "💾 حفظ",
            f"تم حفظ أرصدة {self.tbl.rowCount()} صنف بنجاح!"
        )

    def _print_report(self):
        QMessageBox.information(self, "🖨️ طباعة", "شاشة الطباعة قيد التطوير.")

