"""إدارة الأفراد - Personnel Management View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService


class PersonnelView(QWidget):
    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._camps = []
        self._init_ui()
        self._load_camps()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        header = QLabel('إدارة الأفراد')
        header.setStyleSheet("font-size:20px; font-weight:bold; color:#2C3E50; padding:10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel('المعسكر:'))
        self.cb_camp = QComboBox()
        self.cb_camp.addItem('الكل', None)
        self.cb_camp.currentIndexChanged.connect(self._load_data)
        filter_bar.addWidget(self.cb_camp, 1)
        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText('بحث بالاسم...')
        self.le_search.textChanged.connect(self._filter_table)
        filter_bar.addWidget(self.le_search, 2)
        btn_refresh = QPushButton('🔄 تحديث')
        btn_refresh.clicked.connect(self._load_data)
        filter_bar.addWidget(btn_refresh)
        layout.addLayout(filter_bar)
        form_card = QFrame()
        form_card.setObjectName('card')
        form_card.setStyleSheet("#card { background:#f9f9f9; border:1px solid #ddd; border-radius:6px; padding:10px; }")
        form = QFormLayout(form_card)
        self.le_name = QLineEdit()
        self.le_name.setPlaceholderText('اسم الفرد الكامل')
        self.cb_unit = QComboBox()
        self.cb_unit.addItem('اختر المعسكر/الوحدة', None)
        self.de_join_date = QDateEdit()
        self.de_join_date.setCalendarPopup(True)
        self.de_join_date.setDate(QDate.currentDate())
        btn_add = QPushButton('➕ إضافة فرد')
        btn_add.setStyleSheet("background-color:#27AE60; color:white; font-weight:bold; padding:8px;")
        btn_add.clicked.connect(self._add_personnel)
        form.addRow('اسم الفرد:', self.le_name)
        form.addRow('المعسكر/الوحدة:', self.cb_unit)
        form.addRow('تاريخ الانضمام:', self.de_join_date)
        form.addRow('', btn_add)
        layout.addWidget(form_card)
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(['#', 'اسم الفرد', 'الرقم العسكري', 'المعسكر', 'تاريخ الانضمام'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl, 1)

    def _load_camps(self):
        if not self.api_service:
            return
        try:
            ok, units = self.api_service.get_units()
            if ok and units:
                self._camps = units
                for u in units:
                    self.cb_camp.addItem(u.get('name', ''), u.get('id'))
                    self.cb_unit.addItem(u.get('name', ''), u.get('id'))
        except Exception:
            pass

    def _sample_data(self, camp_filter=None):
        all_data = [
            {'name': 'أحمد محمد علي', 'military_id': '1001', 'camp': 'معسكر 1', 'join_date': '2024-01-15', 'camp_id': 1},
            {'name': 'سالم عبدالله', 'military_id': '1002', 'camp': 'معسكر 1', 'join_date': '2024-02-20', 'camp_id': 1},
            {'name': 'خالد يوسف', 'military_id': '1003', 'camp': 'معسكر 2', 'join_date': '2024-03-10', 'camp_id': 2},
            {'name': 'محمد سالم', 'military_id': '1004', 'camp': 'معسكر 2', 'join_date': '2024-04-05', 'camp_id': 2},
            {'name': 'علي حسن', 'military_id': '1005', 'camp': 'معسكر 3', 'join_date': '2024-05-12', 'camp_id': 3},
        ]
        if camp_filter:
            return [d for d in all_data if d.get('camp_id') == camp_filter]
        return all_data

    def _load_data(self):
        camp_filter = self.cb_camp.currentData() if hasattr(self, 'cb_camp') else None
        data = self._sample_data(camp_filter)
        self.tbl.setRowCount(len(data))
        for r, row in enumerate(data):
            self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(row.get('name', ''))))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(row.get('military_id', ''))))
            self.tbl.setItem(r, 3, QTableWidgetItem(str(row.get('camp', ''))))
            self.tbl.setItem(r, 4, QTableWidgetItem(str(row.get('join_date', ''))))

    def _add_personnel(self):
        name = self.le_name.text().strip()
        unit = self.cb_unit.currentData()
        if not name:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء إدخال اسم الفرد.')
            return
        if not unit:
            QMessageBox.warning(self, 'تنبيه', 'الرجاء اختيار المعسكر/الوحدة.')
            return
        QMessageBox.information(self, 'نجاح', f'تمت إضافة الفرد "{name}" بنجاح.')
        self.le_name.clear()
        self._load_data()

    def _filter_table(self, text):
        text = text.strip().lower()
        for r in range(self.tbl.rowCount()):
            visible = False
            for c in range(self.tbl.columnCount()):
                item = self.tbl.item(r, c)
                if item and text in item.text().lower():
                    visible = True
                    break
            self.tbl.setRowHidden(r, not visible)
