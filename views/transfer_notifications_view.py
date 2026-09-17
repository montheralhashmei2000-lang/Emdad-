"""Transfer Notifications View — أوامر التوجيه المعلقة."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox
)
from PyQt6.QtCore import Qt
from api_service import ApiService
from theme import make_header_label, COLORS


class TransferNotificationsView(QWidget):
    """شاشة أوامر التوجيه المعلقة — عرض ومتابعة طلبات التحويل."""

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self._transfers = []
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.addWidget(make_header_label("📬 أوامر التوجيه المعلقة"))

        # شريط الأدوات
        toolbar = QHBoxLayout()

        self.cb_filter = QComboBox()
        self.cb_filter.addItems(["الكل", "معلق", "معتمد", "مرفوض", "منجز"])
        toolbar.addWidget(QLabel("فلتر:"))
        toolbar.addWidget(self.cb_filter)

        toolbar.addStretch()

        self.lbl_count = QLabel("0 أمر")
        self.lbl_count.setStyleSheet(
            f"color: {COLORS['warning']}; font-weight: bold; font-size: 14px;"
        )
        toolbar.addWidget(self.lbl_count)

        btn_approve = QPushButton("✅ اعتماد المحدد")
        btn_approve.setStyleSheet(
            f"background: {COLORS['green_primary']}; color: white; padding: 6px 16px; border-radius: 4px;"
        )
        btn_approve.clicked.connect(self._approve_selected)
        toolbar.addWidget(btn_approve)

        btn_refresh = QPushButton("🔄 تحديث")
        btn_refresh.setStyleSheet(
            f"background: {COLORS['info']}; color: white; padding: 6px 16px; border-radius: 4px;"
        )
        btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(btn_refresh)

        root.addLayout(toolbar)

        # جدول التحويلات
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(7)
        self.tbl.setHorizontalHeaderLabels([
            "الرقم", "من مستودع", "إلى مستودع", "تاريخ الإنشاء", "الحالة", "أنشئ بواسطة", "ملاحظات"
        ])
        hdr = self.tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.tbl.setColumnWidth(0, 80)
        self.tbl.setColumnWidth(3, 120)
        self.tbl.setColumnWidth(4, 100)
        self.tbl.setColumnWidth(5, 130)
        self.tbl.setStyleSheet(
            f"QTableWidget {{ background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }}"
            f"QHeaderView::section {{ background: {COLORS['green_primary']}; color: white; padding: 6px; font-weight: bold; }}"
            f"QTableWidget::item {{ padding: 6px; }}"
        )
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self.tbl)

    def load_data(self):
        self._transfers = [
            ("T-001", "المستودع الرئيسي", "المستودع الشمالي", "2026-09-01", "معلق", "أحمد محمد", "عاجل"),
            ("T-002", "المستودع الرئيسي", "المستودع الجنوبي", "2026-09-02", "معتمد", "خالد عبدالله", ""),
            ("T-003", "المستودع الشمالي", "المستودع الرئيسي", "2026-09-03", "معلق", "محمد سالم", "مواد غذائية"),
            ("T-004", "المستودع الجنوبي", "المستودع الشمالي", "2026-09-04", "منجز", "سعيد ناصر", ""),
            ("T-005", "المستودع الرئيسي", "المستودع الشرقي", "2026-09-05", "معلق", "فهد عبدالله", "مستلزمات طبية"),
        ]
        self._render()
        self.lbl_count.setText(f"{len(self._transfers)} أمر")

    def _render(self):
        self.tbl.setRowCount(0)
        for row_data in self._transfers:
            row = self.tbl.rowCount()
            self.tbl.insertRow(row)
            for col, val in enumerate(row_data):
                item = QTableWidgetItem(str(val))
                if col == 4:  # الحالة
                    if val == "معلق":
                        item.setForeground(Qt.GlobalColor.darkYellow)
                    elif val == "معتمد":
                        item.setForeground(Qt.GlobalColor.darkGreen)
                    elif val == "مرفوض":
                        item.setForeground(Qt.GlobalColor.red)
                    elif val == "منجز":
                        item.setForeground(Qt.GlobalColor.darkCyan)
                self.tbl.setItem(row, col, item)

    def _approve_selected(self):
        rows = set(index.row() for index in self.tbl.selectedIndexes())
        if not rows:
            QMessageBox.warning(self, "⚠️", "يرجى تحديد صفوف للمعالجة")
            return
        QMessageBox.information(
            self, "✅ اعتماد",
            f"تم اعتماد {len(rows)} أمر توجيه بنجاح!"
        )
        self.load_data()
