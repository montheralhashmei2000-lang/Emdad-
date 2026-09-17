"""إشعارات التحويل - Transfer Notifications View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from ui.api_service import ApiService


class TransferNotificationsView(QWidget):
    """شاشة عرض إشعارات التحويلات الواردة والصادرة."""

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
        header = QLabel('إشعارات التحويلات')
        header.setStyleSheet("font-size:20px; font-weight:bold; color:#2C3E50; padding:10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Tab buttons
        tabs = QHBoxLayout()
        self.btn_incoming = QPushButton('الواردة')
        self.btn_incoming.setCheckable(True)
        self.btn_incoming.setChecked(True)
        self.btn_incoming.clicked.connect(lambda: self._switch_tab('incoming'))
        tabs.addWidget(self.btn_incoming)
        self.btn_outgoing = QPushButton('الصادرة')
        self.btn_outgoing.setCheckable(True)
        self.btn_outgoing.clicked.connect(lambda: self._switch_tab('outgoing'))
        tabs.addWidget(self.btn_outgoing)
        self.btn_completed = QPushButton('المكتملة')
        self.btn_completed.setCheckable(True)
        self.btn_completed.clicked.connect(lambda: self._switch_tab('completed'))
        tabs.addWidget(self.btn_completed)
        tabs.addStretch()
        btn_refresh = QPushButton('تحديث')
        btn_refresh.clicked.connect(self._load_data)
        tabs.addWidget(btn_refresh)
        layout.addLayout(tabs)

        # Table
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(6)
        self.tbl.setHorizontalHeaderLabels(['#', 'رقم التحويل', 'من', 'إلى', 'التاريخ', 'الحالة'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl, 1)

    def _sample_data(self, tab):
        if tab == 'incoming':
            return [
                {'ref': 'TRF-0090', 'from': 'مستودع 1', 'to': 'مستودع 2', 'date': '2026-08-25', 'status': 'بانتظار الاستلام'},
                {'ref': 'TRF-0091', 'from': 'مستودع 3', 'to': 'مستودع 1', 'date': '2026-08-24', 'status': 'بانتظار الموافقة'},
            ]
        elif tab == 'outgoing':
            return [
                {'ref': 'TRF-0089', 'from': 'مستودع 1', 'to': 'معسكر 1', 'date': '2026-08-24', 'status': 'في الطريق'},
            ]
        else:
            return [
                {'ref': 'TRF-0080', 'from': 'مستودع 2', 'to': 'مستودع 1', 'date': '2026-08-20', 'status': 'مكتمل'},
                {'ref': 'TRF-0081', 'from': 'مستودع 1', 'to': 'مستودع 3', 'date': '2026-08-19', 'status': 'مكتمل'},
            ]

    def _load_data(self):
        self._current_tab = 'incoming'
        self._populate(self._sample_data('incoming'))

    def _switch_tab(self, tab):
        self.btn_incoming.setChecked(tab == 'incoming')
        self.btn_outgoing.setChecked(tab == 'outgoing')
        self.btn_completed.setChecked(tab == 'completed')
        self._current_tab = tab
        self._populate(self._sample_data(tab))

    def _populate(self, data):
        self.tbl.setRowCount(len(data))
        for r, row in enumerate(data):
            self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(row.get('ref', ''))))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(row.get('from', ''))))
            self.tbl.setItem(r, 3, QTableWidgetItem(str(row.get('to', ''))))
            self.tbl.setItem(r, 4, QTableWidgetItem(str(row.get('date', ''))))
            self.tbl.setItem(r, 5, QTableWidgetItem(str(row.get('status', ''))))
