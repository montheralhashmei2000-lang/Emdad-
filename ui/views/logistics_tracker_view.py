"""متعقب الإمداد اللوجستي - Logistics Tracker View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFormLayout, QLineEdit, QComboBox,
    QDateEdit, QMessageBox, QAbstractItemView, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QDate
from ui.api_service import ApiService


class LogisticsTrackerView(QWidget):
    """متعقب حركة الإمداد بين المستودعات والمعسكرات."""

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        header = QLabel('متعقب الإمداد - حركة الشحنات')
        header.setStyleSheet("font-size:20px; font-weight:bold; color:#2C3E50; padding:10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Status summary cards
        summary_row = QHBoxLayout()
        self._cards = {}
        for label, color in [
            ('قيد التحضير', '#F39C12'),
            ('في الطريق', '#3498DB'),
            ('تم التسليم', '#27AE60'),
            ('ملغي/مؤجل', '#E74C3C'),
        ]:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background:{color}; color:white; border-radius:8px; padding:15px; }}")
            v = QVBoxLayout(card)
            v.setContentsMargins(10, 10, 10, 10)
            lbl_count = QLabel('0')
            lbl_count.setStyleSheet("font-size:24px; font-weight:bold;")
            lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_title = QLabel(label)
            lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(lbl_count)
            v.addWidget(lbl_title)
            self._cards[label] = lbl_count
            summary_row.addWidget(card)
        layout.addLayout(summary_row)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel('حالة الشحنة:'))
        self.cb_status = QComboBox()
        self.cb_status.addItems(['الكل', 'قيد التحضير', 'في الطريق', 'تم التسليم', 'ملغي/مؤجل'])
        self.cb_status.currentIndexChanged.connect(self._filter_table)
        filter_bar.addWidget(self.cb_status)
        filter_bar.addWidget(QLabel('من تاريخ:'))
        self.dt_from = QDateEdit()
        self.dt_from.setCalendarPopup(True)
        self.dt_from.setDate(QDate.currentDate().addDays(-30))
        filter_bar.addWidget(self.dt_from)
        filter_bar.addStretch()
        btn_refresh = QPushButton('🔄 تحديث')
        btn_refresh.clicked.connect(self._load_data)
        filter_bar.addWidget(btn_refresh)
        layout.addLayout(filter_bar)

        # Table
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(6)
        self.tbl.setHorizontalHeaderLabels(['#', 'رقم الشحنة', 'من', 'إلى', 'الحالة', 'تاريخ الإرسال'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl, 1)

    def _sample_data(self):
        return [
            {'id': 'SHP-001', 'from': 'مستودع رئيسي', 'to': 'معسكر 1', 'status': 'قيد التحضير', 'date': '2026-08-20'},
            {'id': 'SHP-002', 'from': 'مستودع رئيسي', 'to': 'معسكر 2', 'status': 'في الطريق', 'date': '2026-08-22'},
            {'id': 'SHP-003', 'from': 'معسكر 1', 'to': 'معسكر 3', 'status': 'تم التسليم', 'date': '2026-08-18'},
            {'id': 'SHP-004', 'from': 'مستودع رئيسي', 'to': 'معسكر 2', 'status': 'ملغي/مؤجل', 'date': '2026-08-19'},
            {'id': 'SHP-005', 'from': 'مستودع رئيسي', 'to': 'معسكر 3', 'status': 'في الطريق', 'date': '2026-08-25'},
        ]

    def _load_data(self):
        data = self._sample_data()
        # Update cards
        for label, lbl in self._cards.items():
            lbl.setText(str(sum(1 for d in data if d['status'] == label)))
        self._all_data = data
        self._apply_filter()

    def _filter_table(self):
        self._apply_filter()

    def _apply_filter(self):
        sel = self.cb_status.currentText()
        data = self._all_data if sel == 'الكل' else [d for d in self._all_data if d['status'] == sel]
        self.tbl.setRowCount(len(data))
        for r, row in enumerate(data):
            self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(row.get('id', ''))))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(row.get('from', ''))))
            self.tbl.setItem(r, 3, QTableWidgetItem(str(row.get('to', ''))))
            self.tbl.setItem(r, 4, QTableWidgetItem(str(row.get('status', ''))))
            self.tbl.setItem(r, 5, QTableWidgetItem(str(row.get('date', ''))))
