from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit,
    QLabel,
)
from PyQt6.QtCore import Qt
from api_service import ApiService
from theme import make_header_label
from excel_helper import export_table_to_excel


class EntitlementsView(QWidget):
    """Panel for managing global item entitlements in an editable grid."""

    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api_service = api_service or ApiService()
        self._items_data = []
        self._entitlements_dict = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(
            make_header_label(
                "ضبط الاستحقاقات والمقررات (إدخال شبكي مباشر)"
            )
        )
        btn_box = QHBoxLayout()
        btn_save = QPushButton("حفظ جميع المقررات")
        btn_save.setObjectName("danger_btn")
        btn_save.clicked.connect(self.save_all)
        btn_export = QPushButton("تصدير للإكسيل")
        btn_export.clicked.connect(
            lambda: export_table_to_excel(self.table, "Entitlements.xlsx")
        )
        user = getattr(self.parent(), "current_user", None)
        if not isinstance(user, dict):
            user = {}
        is_admin = user.get("role", "") == "ADMIN"
        permissions = user.get("permissions") or {}
        dp = permissions.get("daily_ops") or {}
        can_create = (
            is_admin
            or dp.get("add", False)
            or dp.get("create", False)
            or dp.get("tafreeda", False)
        )
        can_export = (
            is_admin
            or dp.get("export", False)
            or dp.get("print", False)
        )
        btn_save.setVisible(can_create)
        btn_export.setVisible(can_export)
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_export)
        btn_box.addStretch()
        btn_box.addWidget(QLabel("🔍"))
        le_search = QLineEdit()
        le_search.setPlaceholderText("بحث باسم الصنف...")
        le_search.textChanged.connect(self._filter_table)
        btn_box.addWidget(le_search)
        layout.addLayout(btn_box)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            [
                "الصنف",
                "الاستحقاق الشهري للفرد",
                "وحدة القياس للمقرر",
                "ملاحظات",
            ]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        self.load_data()

    def load_data(self):
        ok, ents = self.api_service.get_entitlements()
        if not ok:
            return
        self._entitlements_dict = {}
        for e in ents or []:
            item_id = e.get("item_id", e.get("id"))
            if item_id is not None:
                self._entitlements_dict[item_id] = e
        ok, items = self.api_service.get_items()
        if not ok:
            return
        self.table.setRowCount(0)
        self._items_data = items or []
        for idx, itm in enumerate(self._items_data):
            item_id = itm.get("id")
            name_item = itm.get("name", "")
            row = self.table.rowCount()
            self.table.insertRow(row)
            item_text = (
                str(itm.get("item_code", "")) + " - " + str(name_item)
            )
            item_cell = QTableWidgetItem(item_text)
            item_cell.setData(Qt.ItemDataRole.UserRole, item_id)
            self.table.setItem(row, 0, item_cell)
            ex_ent = self._entitlements_dict.get(item_id) or {}
            le_qty = QLineEdit()
            le_qty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            le_qty.setPlaceholderText("صفر = لا استحقاق")
            qty_value = ex_ent.get("qty_per_person", 0)
            if qty_value is not None:
                le_qty.setText(str(qty_value))
            self.table.setCellWidget(row, 1, le_qty)
            cb_measure = QComboBox()
            units = itm.get("units") or []
            for mu in units:
                unit_id = mu.get("id")
                unit_name = mu.get("unit_name", "")
                cb_measure.addItem(unit_name, unit_id)
            measure_unit_id = ex_ent.get("measure_unit_id")
            if measure_unit_id is not None:
                idx_unit = cb_measure.findData(measure_unit_id)
                if idx_unit >= 0:
                    cb_measure.setCurrentIndex(idx_unit)
            self.table.setCellWidget(row, 2, cb_measure)
            le_notes = QLineEdit()
            notes = ex_ent.get("notes", "")
            if notes is None:
                notes = ""
            le_notes.setText(str(notes))
            self.table.setCellWidget(row, 3, le_notes)

    def save_all(self):
        payload_list = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item is None:
                continue
            item_data = item.data(Qt.ItemDataRole.UserRole)
            if item_data is None:
                continue
            le_qty = self.table.cellWidget(r, 1)
            cb_measure = self.table.cellWidget(r, 2)
            le_notes = self.table.cellWidget(r, 3)
            qty_text = ""
            if le_qty is not None:
                qty_text = le_qty.text().strip()
            if qty_text == "":
                qty_text = "0"
            try:
                qty = float(qty_text)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    "قيمة الاستحقاق غير صحيحة للصنف بالسطر " + str(r + 1),
                )
                return
            unit_id = None
            if cb_measure is not None:
                unit_id = cb_measure.currentData()
            if unit_id is None:
                QMessageBox.warning(
                    self,
                    "خطأ",
                    "يوجد صنف بلا وحدة قياس محددة بالسطر " + str(r + 1),
                )
                return
            notes = ""
            if le_notes is not None:
                notes = le_notes.text().strip()
            payload_list.append(
                {
                    "item_id": int(item_data),
                    "measure_unit_id": int(unit_id),
                    "qty_per_person": qty,
                    "notes": notes,
                }
            )
        if not payload_list:
            QMessageBox.information(
                self, "تنبيه", "لا يوجد بيانات استحقاق لحفظها."
            )
            return
        ok, msg = self.api_service.create_entitlements_bulk(payload_list)
        if ok:
            QMessageBox.information(
                self,
                "عملية ناجحة",
                "تم حفظ وتحديث جميع المقررات بنجاح.",
            )
            self.load_data()
        else:
            QMessageBox.critical(self, "خطأ", "فشل في الحفظ: " + str(msg))

    def _filter_table(self, text):
        text = text.strip().lower()
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 0)
            if it is None:
                continue
            show = not text or text in it.text().lower()
            self.table.setRowHidden(r, not show)
