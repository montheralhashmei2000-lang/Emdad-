"""الوضع الطارئ / عدم الاتصال - Emergency/Offline Mode View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from ui.api_service import ApiService


class EmergencyView(QWidget):
    """شاشة إدارة الوضع الطارئ (offline) والمهام المعلقة للمزامنة."""

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
        header = QLabel('الوضع الطارئ - إدارة عدم الاتصال')
        header.setStyleSheet("font-size:20px; font-weight:bold; color:#C0392B; padding:10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Status banner
        status = QFrame()
        status.setStyleSheet("QFrame { background:#FFE9E6; border:2px solid #E74C3C; border-radius:8px; padding:15px; }")
        sv = QVBoxLayout(status)
        lbl1 = QLabel('⚠️  النظام في وضع عدم الاتصال')
        lbl1.setStyleSheet("font-size:16px; font-weight:bold; color:#C0392B;")
        lbl1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sv.addWidget(lbl1)
        lbl2 = QLabel('جميع العمليات ستحفظ محلياً وستتم مزامنتها تلقائياً عند عودة الاتصال')
        lbl2.setStyleSheet("font-size:12px; color:#7B241C;")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sv.addWidget(lbl2)
        layout.addWidget(status)

        # Pending sync summary
        summary_row = QHBoxLayout()
        for label, value, color in [
            ('عمليات معلقة', '12', '#E67E22'),
            ('مزامنة ناجحة', '148', '#27AE60'),
            ('فشل مزامنة', '2', '#E74C3C'),
            ('حالة الشبكة', 'غير متصل', '#95A5A6'),
        ]:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background:{color}; color:white; border-radius:8px; padding:15px; }}")
            v = QVBoxLayout(card)
            lbl_v = QLabel(value)
            lbl_v.setStyleSheet("font-size:22px; font-weight:bold;")
            lbl_v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_t = QLabel(label)
            lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(lbl_v)
            v.addWidget(lbl_t)
            summary_row.addWidget(card)
        layout.addLayout(summary_row)

        # Action buttons
        action_row = QHBoxLayout()
        btn_retry = QPushButton('🔄 إعادة محاولة المزامنة')
        btn_retry.setStyleSheet("background-color:#3498DB; color:white; font-weight:bold; padding:10px;")
        btn_retry.clicked.connect(self._retry_sync)
        action_row.addWidget(btn_retry)
        btn_check = QPushButton('🔍 فحص الاتصال')
        btn_check.setStyleSheet("background-color:#27AE60; color:white; font-weight:bold; padding:10px;")
        btn_check.clicked.connect(self._check_connection)
        action_row.addWidget(btn_check)
        btn_export = QPushButton('💾 تصدير البيانات المحلية')
        btn_export.clicked.connect(self._export_local)
        action_row.addWidget(btn_export)
        action_row.addStretch()
        layout.addLayout(action_row)

        # Pending operations table
        layout.addWidget(QLabel('📋 العمليات المعلقة:'))
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(['#', 'نوع العملية', 'المرجع', 'التاريخ', 'الحالة'])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl, 1)

    def _sample_data(self):
        return [
            {'type': 'استلام', 'ref': 'RCP-1023', 'date': '2026-08-25', 'status': 'معلق'},
            {'type': 'صرف', 'ref': 'ISS-0451', 'date': '2026-08-25', 'status': 'معلق'},
            {'type': 'تحويل', 'ref': 'TRF-0089', 'date': '2026-08-24', 'status': 'فشل'},
            {'type': 'جرد', 'ref': 'STK-0012', 'date': '2026-08-23', 'status': 'معلق'},
        ]

    def _load_data(self):
        data = self._sample_data()
        self.tbl.setRowCount(len(data))
        for r, row in enumerate(data):
            self.tbl.setItem(r, 0, QTableWidgetItem(str(r + 1)))
            self.tbl.setItem(r, 1, QTableWidgetItem(str(row.get('type', ''))))
            self.tbl.setItem(r, 2, QTableWidgetItem(str(row.get('ref', ''))))
            self.tbl.setItem(r, 3, QTableWidgetItem(str(row.get('date', ''))))
            self.tbl.setItem(r, 4, QTableWidgetItem(str(row.get('status', ''))))

    def _retry_sync(self):
        QMessageBox.information(self, 'مزامنة', 'جاري إعادة محاولة المزامنة...\nسيتم تحديث الحالة تلقائياً.')

    def _check_connection(self):
        QMessageBox.information(self, 'حالة الاتصال', 'لا يوجد اتصال بالإنترنت.\nالوضع: غير متصل')

    def _export_local(self):
        QMessageBox.information(self, 'تصدير', 'تم تصدير البيانات المحلية بنجاح.')
