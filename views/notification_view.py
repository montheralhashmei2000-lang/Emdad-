"""Notification View — شاشة الإشعارات."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime
from api_service import ApiService
from theme import make_header_label, COLORS


class NotificationView(QWidget):
    """شاشة الإشعارات — عرض تنبيهات النظام."""

    def __init__(self, parent=None, api_service: ApiService = None):
        super().__init__(parent)
        self.api_service = api_service
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.addWidget(make_header_label("🔔 الإشعارات"))

        toolbar = QHBoxLayout()

        btn_refresh = QPushButton("🔄 تحديث")
        btn_refresh.setStyleSheet(
            f"background: {COLORS['info']}; color: white; padding: 6px 16px; border-radius: 4px;"
        )
        btn_refresh.clicked.connect(self.load_data)
        toolbar.addWidget(btn_refresh)

        btn_clear = QPushButton("🗑️ مسح الكل")
        btn_clear.setStyleSheet(
            f"background: {COLORS['danger']}; color: white; padding: 6px 16px; border-radius: 4px;"
        )
        btn_clear.clicked.connect(self._clear_all)
        toolbar.addWidget(btn_clear)

        toolbar.addStretch()

        self.lbl_count = QLabel("0 إشعار")
        self.lbl_count.setStyleSheet(
            f"color: {COLORS['green_primary']}; font-weight: bold; font-size: 14px;"
        )
        toolbar.addWidget(self.lbl_count)

        root.addLayout(toolbar)

        self.lst = QListWidget()
        self.lst.setStyleSheet(
            f"QListWidget {{ background: {COLORS['bg_card']}; border: 1px solid {COLORS['border']}; border-radius: 6px; }}"
            f"QListWidget::item {{ padding: 12px; border-bottom: 1px solid {COLORS['border']}; }}"
            f"QListWidget::item:selected {{ background: {COLORS['bg_table_alt']}; }}"
        )
        self.lst.itemDoubleClicked.connect(self._show_details)
        root.addWidget(self.lst)

    def load_data(self):
        self.lst.clear()
        # إشعارات النظام الأساسية
        notifications = [
            ("ℹ️", "مرحباً بك في نظام الإمداد والتموين", "info"),
            ("📦", "يوجد 3 أصناف منخفضة في المخزون", "warning"),
            ("📥", "تم استلام طلب تحويل رقم #1234 من المستودع الرئيسي", "success"),
            ("⏰", "تذكير: جرد دوري نهاية الشهر", "warning"),
            ("🔄", "المزامنة التلقائية ستتم بعد 5 دقائق", "info"),
            ("✅", "تم حفظ بيانات المستفيد الجديد بنجاح", "success"),
            ("⚠️", "يرجى مراجعة طلبات التحويل المعلقة", "warning"),
        ]

        for icon, text, ntype in notifications:
            item = QListWidgetItem(f"{icon}  {text}")
            if ntype == "warning":
                item.setForeground(Qt.GlobalColor.darkYellow)
            elif ntype == "success":
                item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                item.setForeground(Qt.GlobalColor.darkBlue)
            self.lst.addItem(item)

        self.lbl_count.setText(f"{self.lst.count()} إشعار")

    def _clear_all(self):
        if self.lst.count() == 0:
            return
        confirm = QMessageBox.question(
            self, "🗑️ تأكيد",
            "هل تريد مسح جميع الإشعارات؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.lst.clear()
            self.lbl_count.setText("0 إشعار")

    def _show_details(self, item):
        QMessageBox.information(
            self, "📋 تفاصيل الإشعار",
            f"الإشعار: {item.text()}\n\nالوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
