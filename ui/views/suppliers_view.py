"""إدارة الموردين - Suppliers View."""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit,
    QMessageBox, QTabWidget, QFormLayout, QGroupBox, QAbstractItemView, QTextEdit)
from PyQt6.QtCore import Qt
from ui.api_service import ApiService
from ui.theme import make_header_label


class SuppliersView(QWidget):
    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api = api_service or ApiService()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._all_data = []
        self._init_ui()
        self._load_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.addWidget(make_header_label("إدارة الموردين"))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._tab_list = QWidget()
        self._tab_form = QWidget()
        self.tabs.addTab(self._tab_list, "قائمة الموردين")
        self.tabs.addTab(self._tab_form, "إضافة/تعديل")
        self._build_list_tab()
        self._build_form_tab()

    def _build_list_tab(self):
        layout = QVBoxLayout(self._tab_list)
        toolbar = QHBoxLayout()
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText("بحث...")
        self.le_search.textChanged.connect(self._filter_list)
        toolbar.addWidget(self.le_search)
        self.cb_filter_status = QComboBox()
        self.cb_filter_status.addItems(["الكل", "نشط", "موقوف"])
        self.cb_filter_status.currentIndexChanged.connect(self._filter_list)
        toolbar.addWidget(self.cb_filter_status)
        btn_refresh = QPushButton("🔄")
        btn_refresh.clicked.connect(self._load_list)
        toolbar.addWidget(btn_refresh)
        btn_add = QPushButton("➕ جديد")
        btn_add.setStyleSheet("background-color:#27AE60; color:white;")
        btn_add.clicked.connect(lambda: self.tabs.setCurrentWidget(self._tab_form))
        toolbar.addWidget(btn_add)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(6)
        self.tbl.setHorizontalHeaderLabels(["#", "الكود", "الاسم", "الهاتف", "الحالة", "إجراءات"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl, 1)

    def _build_form_tab(self):
        layout = QVBoxLayout(self._tab_form)
        card = QGroupBox("بيانات المورّد")
        form = QFormLayout(card)
        self.le_code = QLineEdit()
        self.le_name = QLineEdit()
        self.le_phone = QLineEdit()
        self.le_email = QLineEdit()
    def _load_list(self):
        try:
            ok, data = self.api.get_suppliers()
            if not ok:
                data = []
            self._all_data = data if isinstance(data, list) else []
            self._filter_list()
        except Exception as e:
            print(f"Error: {e}")

    def _filter_list(self):
        try:
            search = self.le_search.text().strip().lower()
            status = self.cb_filter_status.currentText()
            filtered = []
            for s in self._all_data:
                if search and search not in s.get('name', '').lower() and search not in str(s.get('code', '')).lower():
                    continue
                if status != 'الكل':
                    s_status = 'نشط' if s.get('is_active', True) else 'موقوف'
                    if s_status != status:
                        continue
                filtered.append(s)
            self.tbl.setRowCount(len(filtered))
            for r, s in enumerate(filtered):
                self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
                self.tbl.setItem(r, 1, QTableWidgetItem(str(s.get('code', '-'))))
                self.tbl.setItem(r, 2, QTableWidgetItem(s.get('name', '-')))
                self.tbl.setItem(r, 3, QTableWidgetItem(s.get('phone', '-')))
                self.tbl.setItem(r, 4, QTableWidgetItem('نشط' if s.get('is_active', True) else 'موقوف'))
                btn_edit = QPushButton('✏️')
                btn_edit.clicked.connect(lambda _, x=s: self._edit(x))
                btn_del = QPushButton('🗑️')
                btn_del.clicked.connect(lambda _, x=s: self._delete(x))
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(0, 0, 0, 0)
                l.addWidget(btn_edit)
                l.addWidget(btn_del)
                self.tbl.setCellWidget(r, 5, w)
        except Exception as e:
            print(f"Error: {e}")

    def _edit(self, s):
        self._current_id = s.get('id')
        self.le_code.setText(s.get('code', ''))
        self.le_name.setText(s.get('name', ''))
        self.le_phone.setText(s.get('phone', ''))
        self.le_email.setText(s.get('email', ''))
        self.le_address.setText(s.get('address', ''))
        self.cb_form_status.setCurrentText('نشط' if s.get('is_active', True) else 'موقوف')
        self.txt_notes.setText(s.get('notes', ''))
        self.tabs.setCurrentWidget(self._tab_form)

    def _clear(self):
        if hasattr(self, '_current_id'):
            delattr(self, '_current_id')
        self.le_code.clear()
        self.le_name.clear()
        self.le_phone.clear()
        self.le_email.clear()
        self.le_address.clear()
        self.cb_form_status.setCurrentIndex(0)
        self.txt_notes.clear()

    def _save(self):
        if not self.le_name.text().strip():
            QMessageBox.warning(self, 'تنبيه', 'أدخل اسم المورّد')
            return
        payload = {
            'code': self.le_code.text().strip(),
            'name': self.le_name.text().strip(),
            'phone': self.le_phone.text().strip(),
            'email': self.le_email.text().strip(),
            'address': self.le_address.text().strip(),
            'is_active': self.cb_form_status.currentText() == 'نشط',
            'notes': self.txt_notes.toPlainText().strip(),
        }
        try:
            if hasattr(self, '_current_id'):
                ok, _ = self.api._request('PUT', f'/api/suppliers/{self._current_id}', json=payload)
            else:
                ok, _ = self.api.create_supplier(payload)
            if ok:
                QMessageBox.information(self, 'نجاح', 'تم الحفظ')
                self._clear()
                self._load_list()
                self.tabs.setCurrentWidget(self._tab_list)
            else:
                QMessageBox.critical(self, 'خطأ', 'فشل الحفظ')
        except Exception as e:
            QMessageBox.critical(self, 'خطأ', str(e))

    def _delete(self, s):
        if QMessageBox.question(self, 'تأكيد', f'حذف "{s.get("name", "")}"؟',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                ok, _ = self.api._request('DELETE', f'/api/suppliers/{s.get("id")}')
                if ok:
                    self._load_list()
                    QMessageBox.information(self, 'نجاح', 'تم الحذف')
            except Exception as e:
                QMessageBox.critical(self, 'خطأ', str(e))

    def load_data(self):
        self._load_list()
