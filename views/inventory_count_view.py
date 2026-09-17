"""Inventory Count View - إدارة جرد المخزون."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDateEdit,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QGridLayout, QInputDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from api_service import ApiService
from theme import make_header_label, COLORS

class InventoryCountView(QWidget):
    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api_service = api_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._warehouses = []
        self._current_count_id = None
        self._init_ui()
        self._load_warehouses()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.addWidget(make_header_label("📦 جرد المخزون"))
        self.tabs = QFrame()
        bg = COLORS["bg_card"]
        self.tabs.setStyleSheet(f"QFrame {{ background: {bg}; border-radius: 8px; padding: 4px; }}")
        tabs_layout = QVBoxLayout(self.tabs)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        self.btn_tab_new = self._make_tab_btn("➕ جرد جديد", self._tab_new_clicked)
        self.btn_tab_list = self._make_tab_btn("📋 قائمة الجرد", self._tab_list_clicked)
        self.btn_tab_detail = self._make_tab_btn("🔍 تفاصيل الجرد", self._tab_detail_clicked)
        self._active_tab_btn = self.btn_tab_new
        self._set_active_tab(self.btn_tab_new)
        btn_row.addWidget(self.btn_tab_new)
        btn_row.addWidget(self.btn_tab_list)
        btn_row.addWidget(self.btn_tab_detail)
        btn_row.addStretch()
        tabs_layout.addLayout(btn_row)
        self.content_stack = QWidget()
        self.stack_layout = QVBoxLayout(self.content_stack)
        self.stack_layout.setContentsMargins(0, 8, 0, 0)
        self.stack_layout.addWidget(self._build_new_content())
        self.stack_layout.addWidget(self._build_list_content())
        self.stack_layout.addWidget(self._build_detail_content())
        tabs_layout.addWidget(self.content_stack)
        root.addWidget(self.tabs)

    def _make_card(self):
        card = QFrame()
        bg = COLORS["bg_card"]
        bd = COLORS["border"]
        card.setStyleSheet(f"QFrame {{ background: {bg}; border: 1px solid {bd}; border-radius: 8px; padding: 12px; }}")
        return card

    def _combo_style(self):
        bd = COLORS["border"]
        tp = COLORS["text_dark"]
        gp = COLORS["green_primary"]
        return f"QComboBox {{ background: white; border: 1px solid {bd}; border-radius: 4px; padding: 6px 10px; color: {tp}; min-width: 120px; }} QComboBox:hover {{ border-color: {gp}; }} QComboBox::drop-down {{ border: none; }} QComboBox QAbstractItemView {{ background: white; border: 1px solid {bd}; selection-background-color: rgba(27,107,58,0.2); }}"

    def _line_style(self):
        bd = COLORS["border"]
        tp = COLORS["text_dark"]
        gp = COLORS["green_primary"]
        return f"QLineEdit {{ background: white; border: 1px solid {bd}; border-radius: 4px; padding: 6px 10px; color: {tp}; }} QLineEdit:hover {{ border-color: {gp}; }} QLineEdit:focus {{ border-color: {gp}; background: #f0fff4; }}"

    def _date_style(self):
        bd = COLORS["border"]
        tp = COLORS["text_dark"]
        gp = COLORS["green_primary"]
        return f"QDateEdit {{ background: white; border: 1px solid {bd}; border-radius: 4px; padding: 6px 10px; color: {tp}; }} QDateEdit:hover {{ border-color: {gp}; }}"

    def _status_color(self, status):
        colors = {"DRAFT": "#888", "مسودة": "#888", "PENDING_APPROVAL": "#e67e22", "قيد المراجعة": "#e67e22", "APPROVED": COLORS["green_primary"], "معتمد": COLORS["green_primary"], "CANCELLED": COLORS["danger"], "ملغي": COLORS["danger"]}
        return colors.get(status, "#888")

    def _load_warehouses(self):
        for c in [self.cb_wh, self.cb_wh_filter]:
            c.clear()
            c.addItem("— اختيار المستودع —", None)
        if self.api_service:
            try:
                ok, whs = self.api_service.get_warehouses()
                if ok:
                    self._warehouses = whs or []
                    for w in self._warehouses:
                        name = w.get("name", "")
                        wid = w.get("id")
                        for cb in [self.cb_wh, self.cb_wh_filter]:
                            cb.addItem(name, wid)
            except (TypeError, AttributeError):
                pass

    def _create_count(self):
        wh_id = self.cb_wh.currentData()
        if not wh_id:
            QMessageBox.warning(self, "⚠️", "يرجى اختيار المستودع")
            return
        if not self.api_service:
            QMessageBox.warning(self, "⚠️", "لا يوجد اتصال بالخادم")
            return
        payload = {
            "warehouse_id": wh_id,
            "count_date": self.dt_count.date().toString("yyyy-MM-dd"),
            "notes": self.txt_notes.text().strip(),
        }
        try:
            ok, data = self.api_service.create_inventory_count(payload)
        except (TypeError, AttributeError):
            ok, data = False, None
        if ok and data:
            cid = data.get("id") if isinstance(data, dict) else None
            if cid:
                self._current_count_id = cid
            QMessageBox.information(self, "✅", "تم إنشاء الجرد بنجاح")
            self._tab_list_clicked()
        else:
            msg = "فشل إنشاء الجرد"
            if isinstance(data, dict) and data.get("message"):
                msg = data["message"]
            QMessageBox.warning(self, "⚠️", msg)

    def _load_list(self):
        if not self.api_service:
            return
        wh_id = self.cb_wh_filter.currentData()
        status = self.cb_status_filter.currentText()
        status_val = status if status and not status.startswith("—") else None
        try:
            ok, data = self.api_service.get_inventory_counts(wh_id, status_val)
        except (TypeError, AttributeError):
            ok, data = False, []
        if not ok:
            return
        rows = data if isinstance(data, list) else data.get("results", [])
        self.tbl_list.setRowCount(0)
        for idx, r in enumerate(rows):
            self.tbl_list.insertRow(idx)
            self.tbl_list.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            self.tbl_list.setItem(idx, 1, QTableWidgetItem(str(r.get("count_number", r.get("id", "")))))
            self.tbl_list.setItem(idx, 2, QTableWidgetItem(str(r.get("warehouse_name", "—"))))
            self.tbl_list.setItem(idx, 3, QTableWidgetItem(str(r.get("count_date", "—"))))
            self.tbl_list.setItem(idx, 4, QTableWidgetItem(str(r.get("items_count", 0))))
            st = r.get("status", "—")
            st_item = QTableWidgetItem(str(st))
            st_item.setForeground(QColor(self._status_color(str(st))))
            self.tbl_list.setItem(idx, 5, st_item)
            cid = r.get("id")
            btn = QPushButton("🔍 فتح")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"QPushButton {{ background: {COLORS['green_primary']}; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }} QPushButton:hover {{ background: {COLORS['green_hover']}; }}")
            btn.clicked.connect(lambda _, c=cid: self._open_detail(c))
            cell = QWidget()
            cell_lay = QHBoxLayout(cell)
            cell_lay.setContentsMargins(4, 4, 4, 4)
            cell_lay.addWidget(btn)
            self.tbl_list.setCellWidget(idx, 6, cell)

    def _open_detail(self, count_id):
        self._current_count_id = count_id
        self._tab_detail_clicked()
        if not self.api_service:
            return
        try:
            ok, data = self.api_service.get_inventory_count_detail(count_id)
        except (TypeError, AttributeError):
            ok, data = False, {}
        if ok and data:
            wh = data.get("warehouse_name", "—")
            dt = data.get("count_date", "—")
            st = data.get("status", "—")
            items = data.get("items", [])
            self.lbl_wh_info.setText(f"🏭 المستودع: {wh}")
            self.lbl_date_info.setText(f"📅 التاريخ: {dt}")
            self.lbl_status_info.setText(f"🏷️ الحالة: {st}")
            self.lbl_items_count_info.setText(f"📦 الأصناف: {len(items)}")
            self.tbl_detail.setRowCount(0)
            for idx, item in enumerate(items):
                self.tbl_detail.insertRow(idx)
                n = QTableWidgetItem(str(idx + 1))
                n.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_detail.setItem(idx, 0, n)
                self.tbl_detail.setItem(idx, 1, QTableWidgetItem(str(item.get("item_code", ""))))
                self.tbl_detail.setItem(idx, 2, QTableWidgetItem(str(item.get("item_name", ""))))
                self.tbl_detail.setItem(idx, 3, QTableWidgetItem(str(item.get("unit", ""))))
                rec_qty = str(item.get("recorded_qty", item.get("system_qty", 0)))
                rq_item = QTableWidgetItem(rec_qty)
                rq_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_detail.setItem(idx, 4, rq_item)
                act_qty = str(item.get("actual_qty", ""))
                aq_item = QTableWidgetItem(act_qty)
                aq_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_detail.setItem(idx, 5, aq_item)
                try:
                    diff = int(item.get("actual_qty", 0)) - int(item.get("recorded_qty", 0))
                    diff_text = f"{diff:+d}"
                    diff_item = QTableWidgetItem(diff_text)
                    diff_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if diff > 0:
                        diff_item.setForeground(QColor(COLORS["green_primary"]))
                    elif diff < 0:
                        diff_item.setForeground(QColor(COLORS["danger"]))
                except (ValueError, TypeError):
                    diff_item = QTableWidgetItem("—")
                self.tbl_detail.setItem(idx, 6, diff_item)
        else:
            QMessageBox.warning(self, "⚠️", "تعذر تحميل تفاصيل الجرد")

    def _open_detail_from_list(self):
        row = self.tbl_list.currentRow()
        if row < 0:
            return
        btn = self.tbl_list.cellWidget(row, 6)
        if btn:
            btn.click()

    def _save_detail(self):
        if not self._current_count_id or not self.api_service:
            return
        items = []
        for i in range(self.tbl_detail.rowCount()):
            item_code = self.tbl_detail.item(i, 1).text()
            actual_qty_text = self.tbl_detail.item(i, 5).text()
            try:
                actual_qty = int(actual_qty_text)
            except (ValueError, TypeError):
                actual_qty = 0
            items.append({"item_code": item_code, "actual_qty": actual_qty})
        try:
            ok, data = self.api_service.update_inventory_count_items(self._current_count_id, {"items": items})
        except (TypeError, AttributeError):
            ok, data = False, None
        if ok:
            QMessageBox.information(self, "✅", "تم حفظ التعديلات بنجاح")
            self._open_detail(self._current_count_id)
        else:
            msg = "فشل حفظ التعديلات"
            if isinstance(data, dict) and data.get("message"):
                msg = data["message"]
            QMessageBox.warning(self, "⚠️", msg)

    def _approve(self):
        if not self._current_count_id:
            return
        st = self.lbl_status_info.text()
        if "معتمد" in st:
            QMessageBox.information(self, "ℹ️", "هذا الجرد معتمد بالفعل")
            return
        ok, pressed = QMessageBox.question(self, "✅", "هل تريد اعتماد هذا الجرد؟", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ok == QMessageBox.StandardButton.Yes:
            try:
                ok, data = self.api_service.approve_inventory_count(self._current_count_id)
            except (TypeError, AttributeError):
                ok, data = False, None
            if ok:
                QMessageBox.information(self, "✅", "تم اعتماد الجرد بنجاح")
                self._open_detail(self._current_count_id)
            else:
                QMessageBox.warning(self, "⚠️", "فشل اعتماد الجرد")

    def _cancel(self):
        if not self._current_count_id:
            return
        ok, pressed = QMessageBox.question(self, "❌", "هل تريد إلغاء هذا الجرد؟", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ok == QMessageBox.StandardButton.Yes:
            try:
                ok, data = self.api_service.cancel_inventory_count(self._current_count_id)
            except (TypeError, AttributeError):
                ok, data = False, None
            if ok:
                QMessageBox.information(self, "✅", "تم إلغاء الجرد بنجاح")
                self._open_detail(self._current_count_id)
            else:
                QMessageBox.warning(self, "⚠️", "فشل إلغاء الجرد")

    def _make_tab_btn(self, text, handler):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(handler)
        tm = COLORS["text_medium"]
        btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {tm}; border: none; padding: 10px 20px; font-size: 13px; font-weight: bold; border-radius: 6px; }} QPushButton:hover {{ background: rgba(255,255,255,0.1); }}")
        return btn

    def _set_active_tab(self, btn):
        tm = COLORS["text_medium"]
        gp = COLORS["green_primary"]
        if self._active_tab_btn:
            self._active_tab_btn.setStyleSheet(f"QPushButton {{ background: transparent; color: {tm}; border: none; padding: 10px 20px; font-size: 13px; font-weight: bold; border-radius: 6px; }}")
        self._active_tab_btn = btn
        btn.setStyleSheet(f"QPushButton {{ background: {gp}; color: white; border: none; padding: 10px 20px; font-size: 13px; font-weight: bold; border-radius: 6px; }}")

    def _show_content(self, index):
        for i in range(self.stack_layout.count()):
            w = self.stack_layout.itemAt(i).widget()
            if w:
                w.setVisible(i == index)

    def _tab_new_clicked(self):
        self._set_active_tab(self.btn_tab_new)
        self._show_content(0)

    def _tab_list_clicked(self):
        self._set_active_tab(self.btn_tab_list)
        self._show_content(1)
        self._load_list()

    def _tab_detail_clicked(self):
        self._set_active_tab(self.btn_tab_detail)
        self._show_content(2)

    def _build_new_content(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        card = self._make_card()
        card_lay = QGridLayout(card)
        card_lay.setSpacing(10)
        row = 0
        lbl_wh = QLabel("🏭 المستودع:")
        lbl_wh.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 13px;")
        self.cb_wh = QComboBox()
        self.cb_wh.setStyleSheet(self._combo_style())
        self.cb_wh.addItem("— اختيار المستودع —", None)
        card_lay.addWidget(lbl_wh, row, 0)
        card_lay.addWidget(self.cb_wh, row, 1)
        row += 1
        lbl_date = QLabel("📅 تاريخ الجرد:")
        lbl_date.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 13px;")
        self.dt_count = QDateEdit()
        self.dt_count.setStyleSheet(self._date_style())
        self.dt_count.setDate(QDate.currentDate())
        self.dt_count.setCalendarPopup(True)
        card_lay.addWidget(lbl_date, row, 0)
        card_lay.addWidget(self.dt_count, row, 1)
        row += 1
        lbl_notes = QLabel("📝 ملاحظات:")
        lbl_notes.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 13px;")
        self.txt_notes = QLineEdit()
        self.txt_notes.setStyleSheet(self._line_style())
        self.txt_notes.setPlaceholderText("أدخل ملاحظات اختيارية...")
        card_lay.addWidget(lbl_notes, row, 0)
        card_lay.addWidget(self.txt_notes, row, 1)
        card_lay.setColumnStretch(0, 0)
        card_lay.setColumnStretch(1, 1)
        lay.addWidget(card)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_create = QPushButton("✅ إنشاء جرد")
        btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_create.setStyleSheet(f"QPushButton {{ background: {COLORS['green_primary']}; color: white; border: none; padding: 12px 30px; font-size: 14px; font-weight: bold; border-radius: 8px; }} QPushButton:hover {{ background: {COLORS['green_hover']}; }}")
        btn_create.clicked.connect(self._create_count)
        btn_row.addWidget(btn_create)
        lay.addLayout(btn_row)
        return w

    def _build_list_content(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        card = self._make_card()
        card_lay = QGridLayout(card)
        card_lay.setSpacing(10)
        r = 0
        lbl_wh = QLabel("🏭 المستودع:")
        lbl_wh.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 13px;")
        self.cb_wh_filter = QComboBox()
        self.cb_wh_filter.setStyleSheet(self._combo_style())
        self.cb_wh_filter.addItem("— جميع المستودعات —", None)
        self.cb_wh_filter.currentIndexChanged.connect(self._load_list)
        lbl_status = QLabel("🏷️ الحالة:")
        lbl_status.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 13px;")
        self.cb_status_filter = QComboBox()
        self.cb_status_filter.setStyleSheet(self._combo_style())
        self.cb_status_filter.addItems(["— جميع الحالات —", "مسودة", "قيد المراجعة", "معتمد", "ملغي"])
        self.cb_status_filter.currentIndexChanged.connect(self._load_list)
        card_lay.addWidget(lbl_wh, r, 0)
        card_lay.addWidget(self.cb_wh_filter, r, 1)
        card_lay.addWidget(lbl_status, r, 2)
        card_lay.addWidget(self.cb_status_filter, r, 3)
        r += 1
        btn_refresh = QPushButton("🔄 تحديث")
        btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_refresh.setStyleSheet(f"QPushButton {{ background: {COLORS['bg_card']}; color: {COLORS['text_dark']}; border: 1px solid {COLORS['border']}; padding: 6px 16px; border-radius: 6px; font-weight: bold; }} QPushButton:hover {{ border-color: {COLORS['green_primary']}; color: {COLORS['green_primary']}; }}")
        btn_refresh.clicked.connect(self._load_list)
        card_lay.addWidget(btn_refresh, r, 0, 1, 4, Qt.AlignmentFlag.AlignRight)
        lay.addWidget(card)
        self.tbl_list = QTableWidget()
        self.tbl_list.setStyleSheet(f"QTableWidget {{ background: white; border: 1px solid {COLORS['border']}; border-radius: 8px; gridline-color: {COLORS['border']}; alternate-background-color: #f8f9fa; }} QTableWidget::item {{ padding: 8px; }} QTableWidget::item:selected {{ background: rgba(27,107,58,0.2); }}")
        self.tbl_list.setColumnCount(7)
        self.tbl_list.setHorizontalHeaderLabels(["#", "رقم الجرد", "المستودع", "التاريخ", "عدد الأصناف", "الحالة", "الإجراءات"])
        self.tbl_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_list.doubleClicked.connect(lambda: self._open_detail_from_list())
        hdr = self.tbl_list.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.tbl_list)
        return w

    def _build_detail_content(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        self.info_card = self._make_card()
        info_lay = QGridLayout(self.info_card)
        info_lay.setSpacing(10)
        self.lbl_wh_info = QLabel("🏭 المستودع: —")
        self.lbl_wh_info.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 13px;")
        self.lbl_date_info = QLabel("📅 التاريخ: —")
        self.lbl_date_info.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 13px;")
        self.lbl_status_info = QLabel("🏷️ الحالة: —")
        self.lbl_status_info.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 13px;")
        self.lbl_items_count_info = QLabel("📦 الأصناف: —")
        self.lbl_items_count_info.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold; font-size: 13px;")
        info_lay.addWidget(self.lbl_wh_info, 0, 0)
        info_lay.addWidget(self.lbl_date_info, 0, 1)
        info_lay.addWidget(self.lbl_status_info, 0, 2)
        info_lay.addWidget(self.lbl_items_count_info, 0, 3)
        lay.addWidget(self.info_card)
        self.tbl_detail = QTableWidget()
        self.tbl_detail.setStyleSheet(f"QTableWidget {{ background: white; border: 1px solid {COLORS['border']}; border-radius: 8px; gridline-color: {COLORS['border']}; alternate-background-color: #f8f9fa; }} QTableWidget::item {{ padding: 8px; }} QTableWidget::item:selected {{ background: rgba(27,107,58,0.2); }}")
        self.tbl_detail.setColumnCount(7)
        self.tbl_detail.setHorizontalHeaderLabels(["#", "رمز الصنف", "اسم الصنف", "الوحدة", "الكمية المسجلة", "الكمية الفعلية", "الفرق"])
        hdr = self.tbl_detail.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        lay.addWidget(self.tbl_detail)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_save_detail = QPushButton("💾 حفظ التعديلات")
        self.btn_save_detail.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_detail.setStyleSheet(f"QPushButton {{ background: {COLORS['green_primary']}; color: white; border: none; padding: 12px 30px; font-size: 14px; font-weight: bold; border-radius: 8px; }} QPushButton:hover {{ background: {COLORS['green_hover']}; }}")
        self.btn_save_detail.clicked.connect(self._save_detail)
        self.btn_approve = QPushButton("✅ اعتماد الجرد")
        self.btn_approve.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_approve.setStyleSheet(f"QPushButton {{ background: {COLORS['green_primary']}; color: white; border: none; padding: 12px 30px; font-size: 14px; font-weight: bold; border-radius: 8px; }} QPushButton:hover {{ background: {COLORS['green_hover']}; }}")
        self.btn_approve.clicked.connect(self._approve)
        self.btn_cancel = QPushButton("❌ إلغاء الجرد")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet(f"QPushButton {{ background: {COLORS['danger']}; color: white; border: none; padding: 12px 30px; font-size: 14px; font-weight: bold; border-radius: 8px; }} QPushButton:hover {{ opacity: 0.8; }}")
        self.btn_cancel.clicked.connect(self._cancel)
        btn_row.addWidget(self.btn_save_detail)
        btn_row.addWidget(self.btn_approve)
        btn_row.addWidget(self.btn_cancel)
        lay.addLayout(btn_row)
        return w
