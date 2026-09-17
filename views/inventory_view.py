"""
Inventory View — Shows actual current stock with complex units data.
Accurately reconstructed from original old_client.exe bytecode.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QHBoxLayout, QPushButton, QLabel, QComboBox, QFrame, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt

import api_service
from api_service import ApiService
import theme
from theme import make_header_label, COLORS
import excel_helper
from excel_helper import export_table_to_excel
import print_helper
from print_helper import print_inventory_report


class InventoryView(QWidget):

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        layout.addWidget(make_header_label("جرد المخزون الفعلي"))

        stats_bar = QHBoxLayout()
        self.lbl_total = self._make_stat("إجمالي الأصناف", "0", COLORS["green_primary"])
        self.lbl_low = self._make_stat("أصناف منخفضة", "0", COLORS["warning"])
        self.lbl_empty = self._make_stat("أصناف فارغة", "0", COLORS["danger"])
        stats_bar.addWidget(self.lbl_total)
        stats_bar.addWidget(self.lbl_low)
        stats_bar.addWidget(self.lbl_empty)
        layout.addLayout(stats_bar)

        top_bar = QHBoxLayout()

        top_bar.addWidget(QLabel("المستودع:"))
        self.cb_warehouse = QComboBox()
        self.cb_warehouse.setMinimumWidth(150)
        self.cb_warehouse.currentIndexChanged.connect(self.load_data)
        top_bar.addWidget(self.cb_warehouse)

        top_bar.addWidget(QLabel("🔍 بحث:"))
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText("ابحث بالكود أو اسم الصنف...")
        self.le_search.textChanged.connect(self._filter_table)
        top_bar.addWidget(self.le_search)

        top_bar.addWidget(QLabel("الحالة:"))
        self.cb_status = QComboBox()
        self.cb_status.addItems(["الكل", "جيد ✅", "منخفض ⚠️", "فارغ ❌"])
        self.cb_status.currentIndexChanged.connect(self._filter_table)
        top_bar.addWidget(self.cb_status)

        btn_refresh = QPushButton("تحديث البيانات 🔄")
        btn_refresh.clicked.connect(self.load_data)
        top_bar.addWidget(btn_refresh)

        btn_export = QPushButton("📥 تصدير إكسيل")
        btn_export.clicked.connect(lambda: export_table_to_excel(self.table, "Inventory_Export.xlsx"))
        top_bar.addWidget(btn_export)

        btn_print = QPushButton("🖨️ طباعة كشف الجرد")
        btn_print.clicked.connect(self._print_report)
        top_bar.addWidget(btn_print)

        top_bar.addStretch()
        layout.addLayout(top_bar)

        user = getattr(self.parent(), "current_user", None) or {}
        is_admin = user.get("role", "") == "ADMIN"
        can_print = user.get("permissions", {}).get("stocktake", {}).get("print", False)
        btn_print.setVisible(is_admin or can_print)

        self.table = QTableWidget()
        self.table.setHorizontalHeaderLabels([
            "كود الصنف", "الاسم", "الوحدة الأولى (الكبرى)", "الوحدة الثانية",
            "الوحدة الثالثة (الصغرى)", "رصيد فارغ", "المستودع", "الحالة",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _make_stat(self, title, value, color):
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMinimumHeight(70)

        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 10, 10, 10)

        t = QLabel(title)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(f"font-size: 11px; color: {COLORS['text_medium']};")
        lay.addWidget(t)

        v = QLabel(value)
        v.setObjectName("stat_" + title)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
        lay.addWidget(v)

        return frame

    def load_data(self):
        if self.cb_warehouse.count() == 1:
            ok, warehouses = self.api_service.get_warehouses()
            if ok:
                allowed = None
                if hasattr(self.parent(), "current_user"):
                    allowed = self.parent().current_user.get("allowed_warehouses")

                self.cb_warehouse.blockSignals(True)
                self.cb_warehouse.clear()
                self.cb_warehouse.addItem("الكل", None)
                for w in warehouses:
                    if allowed is None or w["id"] in allowed:
                        self.cb_warehouse.addItem(w["name"], w["id"])
                self.cb_warehouse.blockSignals(False)

        wh_id = self.cb_warehouse.currentData()
        ok, data = self.api_service._request(
            "GET", "/reports/current-stock",
            params={"warehouse_id": wh_id},
        )
        if not ok:
            return

        self.table.setRowCount(0)

        grouped = {}
        for row in data:
            key = (row["item_code"], row.get("warehouse_name", ""))
            grouped.setdefault(key, []).append(row)

        total_items = 0
        low_items = 0
        empty_items = 0

        for idx, item_data in enumerate(grouped.values()):
            total_items += 1
            self.table.insertRow(idx)

            units = item_data[0].get("units", [])
            units.sort(key=lambda u: u["cf"], reverse=True)

            unit_1 = unit_2 = unit_3 = "-"
            if len(units) > 0:
                unit_1 = f"{units[0]['quantity']} {units[0]['unit_name']}"
            if len(units) > 1:
                unit_2 = f"{units[1]['quantity']} {units[1]['unit_name']}"
            if len(units) > 2:
                unit_3 = f"{units[2]['quantity']} {units[2]['unit_name']}"

            total_qty = sum(u.get("quantity", None) for u in units)
            min_limit = item_data[0].get("min_limit")

            if total_qty == 0:
                status_text = "فارغ ❌"
                empty_items += 1
            elif min_limit is not None and total_qty <= min_limit:
                status_text = "منخفض ⚠️"
                low_items += 1
            else:
                status_text = "جيد ✅"

            self.table.setItem(idx, 0, QTableWidgetItem(item_data[0]["item_code"]))
            self.table.setItem(idx, 1, QTableWidgetItem(item_data[0]["item_name"]))
            self.table.setItem(idx, 2, QTableWidgetItem(unit_1))
            self.table.setItem(idx, 3, QTableWidgetItem(unit_2))
            self.table.setItem(idx, 4, QTableWidgetItem(unit_3))
            self.table.setItem(idx, 5, QTableWidgetItem(""))
            self.table.setItem(idx, 6, QTableWidgetItem(item_data[0].get("warehouse_name")))
            self.table.setItem(idx, 7, QTableWidgetItem(status_text))

        self.findChild(QLabel, "stat_إجمالي الأصناف").setText(str(total_items))
        self.findChild(QLabel, "stat_أصناف منخفضة").setText(str(low_items))
        self.findChild(QLabel, "stat_أصناف فارغة").setText(str(empty_items))

        self._filter_table()

    def _filter_table(self):
        """Filter inventory table by search text and status."""
        search_text = self.le_search.text().strip().lower()
        status_filter = self.cb_status.currentText()

        for r in range(self.table.rowCount()):
            show = True
            match = False
            for c in range(2):
                it = self.table.item(r, c)
                if it and search_text in it.text().lower():
                    match = True
            if search_text and not match:
                show = False

            if status_filter != "الكل":
                status_item = self.table.item(r, 7)
                if status_item and status_item.text() != status_filter:
                    show = False

            self.table.setRowHidden(r, not show)

    def _print_report(self):
        QMessageBox.information(self, "تحت التطوير", "خاصية الطباعة المفصلة قيد التطوير.")
