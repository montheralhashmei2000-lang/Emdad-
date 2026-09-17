"""Suppliers View - إدارة الموردين. Form + table layout."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame,
    QGridLayout, QTextEdit,
)
from PyQt6.QtCore import Qt
from api_service import ApiService
from theme import make_header_label


class SuppliersView(QWidget):
    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api_service = api_service
        self._suppliers = []
        self._editing_id = None
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()
        self._apply_permissions()
        self.load_data()

    def _apply_permissions(self):
        user = getattr(self.parent(), "current_user", None) or {}
        role = user.get("role", "")
        perms = user.get("permissions", {})
        self._can_add = role == "ADMIN" or perms.get("suppliers", {}).get("add", False)
        self._can_edit = role == "ADMIN" or perms.get("suppliers", {}).get("edit", False)
        self._can_delete = role == "ADMIN" or perms.get("suppliers", {}).get("delete", False)



    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)
        # Title
        title = make_header_label("إدارة الموردين")
        title.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #2E6B35; "
            "padding: 4px 0; border-bottom: 2px solid #C5A028;"
        )
        root.addWidget(title)

        form_card = QFrame()
        form_card.setStyleSheet(
            "QFrame { background-color: #F5F3EE; border-radius: 8px; "
            "border: 1px solid #C9C6B8; padding: 14px; }"
        )
        grid = QGridLayout(form_card)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        def lbl(text):
            w = QLabel(text)
            w.setStyleSheet(
                "color: #1C2B1C; font-weight: bold; font-size: 13px; "
                "background: transparent; border: none;"
            )
            return w

        def inp(placeholder):
            le = QLineEdit()
            le.setPlaceholderText(placeholder)
            le.setStyleSheet(
                "QLineEdit { background: #FFFFFF; border: 1px solid #C9C6B8; "
                "border-radius: 6px; padding: 8px 10px; color: #1C2B1C; "
                "font-size: 13px; } "
                "QLineEdit:focus { border-color: #2E6B35; }"
            )
            return le

        lbl_name = lbl("اسم المورد:")
        self.txt_name = inp("اسم المورد")
        grid.addWidget(lbl_name, 0, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.txt_name, 0, 1)

        lbl_phone = lbl("رقم الهاتف:")
        self.txt_phone = inp("رقم الهاتف")
        grid.addWidget(lbl_phone, 1, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.txt_phone, 1, 1)

        lbl_email = lbl("البريد الإلكتروني:")
        self.txt_email = inp("البريد الإلكتروني")
        grid.addWidget(lbl_email, 2, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.txt_email, 2, 1)

        lbl_address = lbl("العنوان:")
        self.txt_address = inp("العنوان")
        grid.addWidget(lbl_address, 3, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.txt_address, 3, 1)

        lbl_contact = lbl("جهة الاتصال:")
        self.txt_contact = inp("جهة الاتصال")
        grid.addWidget(lbl_contact, 4, 0, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.txt_contact, 4, 1)

        lbl_notes = lbl("ملاحظات:")
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("ملاحظات...")
        self.txt_notes.setMaximumHeight(80)
        self.txt_notes.setStyleSheet(
            "QTextEdit { background: #FFFFFF; border: 1px solid #C9C6B8; "
            "border-radius: 6px; padding: 8px 10px; color: #1C2B1C; "
            "font-size: 13px; } "
            "QTextEdit:focus { border-color: #2E6B35; }"
        )
        grid.addWidget(lbl_notes, 5, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        grid.addWidget(self.txt_notes, 5, 1)

        self.btn_save = QPushButton("💾 تسجيل مورد جديد")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setMinimumHeight(40)
        self.btn_save.setStyleSheet(
            "QPushButton { background-color: #2E6B35; color: #FFFFFF; "
            "border: none; padding: 10px 20px; font-size: 14px; "
            "font-weight: bold; border-radius: 6px; } "
            "QPushButton:hover { background-color: #3A8542; } "
            "QPushButton:disabled { background-color: #888; color: #ddd; }"
        )
        self.btn_save.clicked.connect(self._save)
        grid.addWidget(self.btn_save, 6, 0, 1, 2)
        root.addWidget(form_card)



        # Toolbar row
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        toolbar.addStretch()

        self.btn_refresh = QPushButton("🔄 تحديث")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet(
            "QPushButton { background-color: #2E6B35; color: #FFFFFF; "
            "border: none; padding: 8px 18px; font-size: 13px; "
            "font-weight: bold; border-radius: 6px; } "
            "QPushButton:hover { background-color: #3A8542; }"
        )
        self.btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(self.btn_refresh)

        self.btn_export = QPushButton("📊 تصدير إكسيل")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setStyleSheet(
            "QPushButton { background-color: #2E6B35; color: #FFFFFF; "
            "border: none; padding: 8px 18px; font-size: 13px; "
            "font-weight: bold; border-radius: 6px; } "
            "QPushButton:hover { background-color: #3A8542; }"
        )
        toolbar.addWidget(self.btn_export)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 16px;")
        toolbar.addWidget(search_icon)
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("بحث بالاسم أو الهاتف...")
        self.txt_search.setMaximumWidth(300)
        self.txt_search.setStyleSheet(
            "QLineEdit { background: #FFFFFF; border: 1px solid #C9C6B8; "
            "border-radius: 6px; padding: 8px 12px; font-size: 13px; }"
        )
        self.txt_search.textChanged.connect(self._on_search)
        toolbar.addWidget(self.txt_search)
        root.addLayout(toolbar)

        # Table
        headers = ["#", "الاسم", "الهاتف", "البريد", "العنوان", "جهة الاتصال", "ملاحظات", "إجراء"]
        self.tbl = QTableWidget(0, len(headers))
        self.tbl.setHorizontalHeaderLabels(headers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setStyleSheet(
            "QTableWidget { background-color: #FFFFFF; "
            "alternate-background-color: #F5F3EE; "
            "border: 1px solid #C9C6B8; gridline-color: #E8E4D8; "
            "font-size: 13px; } "
            "QHeaderView::section { background-color: #2E6B35; "
            "color: #FFFFFF; padding: 8px; font-weight: bold; "
            "font-size: 13px; border: 1px solid #2E6B35; }"
        )
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setColumnWidth(0, 40)
        self.tbl.setColumnWidth(7, 130)
        root.addWidget(self.tbl)



    def _suppliers_endpoint(self):
        return "/api/suppliers/"

    def load_data(self):
        self._suppliers = []
        if self.api_service:
            try:
                ok, data = self.api_service.get_suppliers(limit=500)
                if ok and isinstance(data, list):
                    self._suppliers = data
            except Exception:
                self._suppliers = []
        self._render_table(self._suppliers)

    def _on_search(self, text):
        text = (text or "").strip()
        if not text:
            self._render_table(self._suppliers)
            return
        filtered = [
            s for s in self._suppliers
            if text in str(s.get("name", ""))
            or text in str(s.get("phone", ""))
        ]
        self._render_table(filtered)

    def _render_table(self, items):
        self.tbl.setRowCount(0)
        for idx, item in enumerate(items, start=1):
            row = self.tbl.rowCount()
            self.tbl.insertRow(row)
            cell_num = QTableWidgetItem(str(idx))
            cell_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl.setItem(row, 0, cell_num)
            self.tbl.setItem(row, 1, QTableWidgetItem(str(item.get("name", ""))))
            self.tbl.setItem(row, 2, QTableWidgetItem(str(item.get("phone", ""))))
            self.tbl.setItem(row, 3, QTableWidgetItem(str(item.get("email", ""))))
            self.tbl.setItem(row, 4, QTableWidgetItem(str(item.get("address", ""))))
            self.tbl.setItem(row, 5, QTableWidgetItem(str(item.get("contact_person", ""))))
            self.tbl.setItem(row, 6, QTableWidgetItem(str(item.get("notes", ""))))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(4)

            btn_del = QPushButton("🗑 حذف")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet(
                "QPushButton { background-color: #B83A2A; color: #FFFFFF; "
                "border: none; padding: 4px 10px; font-size: 12px; "
                "font-weight: bold; border-radius: 4px; } "
                "QPushButton:hover { background-color: #D04A3A; } "
                "QPushButton:disabled { background-color: #aaa; }"
            )
            sid = item.get("id")
            btn_del.clicked.connect(lambda _checked, s=sid: self._delete(s))
            btn_del.setEnabled(self._can_delete)
            action_layout.addWidget(btn_del)

            btn_edit = QPushButton("✏️ تعديل")
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setStyleSheet(
                "QPushButton { background-color: #2E6B35; color: #FFFFFF; "
                "border: none; padding: 4px 10px; font-size: 12px; "
                "font-weight: bold; border-radius: 4px; } "
                "QPushButton:hover { background-color: #3A8542; } "
                "QPushButton:disabled { background-color: #aaa; }"
            )
            btn_edit.clicked.connect(lambda _checked, s=item: self._fill_form(s))
            btn_edit.setEnabled(self._can_edit)
            action_layout.addWidget(btn_edit)
            action_layout.addStretch()

            self.tbl.setCellWidget(row, 7, action_widget)
            self.tbl.setRowHeight(row, 44)

    def _fill_form(self, item):
        self._editing_id = item.get("id")
        self.txt_name.setText(str(item.get("name", "")))
        self.txt_phone.setText(str(item.get("phone", "")))
        self.txt_email.setText(str(item.get("email", "")))
        self.txt_address.setText(str(item.get("address", "")))
        self.txt_contact.setText(str(item.get("contact_person", "")))
        self.txt_notes.setPlainText(str(item.get("notes", "")))
        self.btn_save.setText("💾 تحديث البيانات")

    def _clear_form(self):
        self._editing_id = None
        self.txt_name.clear()
        self.txt_phone.clear()
        self.txt_email.clear()
        self.txt_address.clear()
        self.txt_contact.clear()
        self.txt_notes.clear()
        self.btn_save.setText("💾 تسجيل مورد جديد")

    def _save(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "يرجى إدخال اسم المورد.")
            return
        payload = {
            "name": name,
            "phone": self.txt_phone.text().strip(),
            "email": self.txt_email.text().strip(),
            "address": self.txt_address.text().strip(),
            "contact_person": self.txt_contact.text().strip(),
            "notes": self.txt_notes.toPlainText().strip(),
        }
        if not self.api_service:
            QMessageBox.warning(self, "تنبيه", "لا يوجد اتصال بالخادم.")
            return
        if self._editing_id is None:
            ok, resp = self.api_service.create_supplier(payload)
        else:
            ok, resp = self.api_service.update_supplier(self._editing_id, payload)
        if ok:
            QMessageBox.information(self, "نجاح", "تم الحفظ بنجاح.")
            self._clear_form()
            self.load_data()
        else:
            QMessageBox.critical(self, "خطأ", f"فشل الحفظ: {resp}")

    def _delete(self, sid):
        if sid is None:
            return
        confirm = QMessageBox.question(
            self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا المورد؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        if not self.api_service:
            return
        ok, resp = self.api_service.delete_supplier(sid)
        if ok:
            QMessageBox.information(self, "نجاح", "تم الحذف بنجاح.")
            self.load_data()
        else:
            QMessageBox.critical(self, "خطأ", f"فشل الحذف: {resp}")
