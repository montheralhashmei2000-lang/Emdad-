"""الإشعارات - Notifications View."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QMessageBox, QScrollArea, QCheckBox
)
from PyQt6.QtCore import Qt
from datetime import datetime, timedelta


class NotificationView(QWidget):
    """شاشة عرض الإشعارات والتذكيرات."""

    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._init_ui()
        self._load_notifications()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header_row = QHBoxLayout()
        header = QLabel('🔔 الإشعارات')
        header.setStyleSheet("font-size:20px; font-weight:bold; color:#2C3E50; padding:10px;")
        header_row.addWidget(header)
        header_row.addStretch()
        btn_mark = QPushButton('✓ تعليم الكل كمقروء')
        btn_mark.clicked.connect(self._mark_all_read)
        header_row.addWidget(btn_mark)
        btn_clear = QPushButton('🗑️ مسح الكل')
        btn_clear.clicked.connect(self._clear_all)
        header_row.addWidget(btn_clear)
        layout.addLayout(header_row)

        # Scroll area for notifications
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; }")
        self.container = QWidget()
        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

    def _sample_notifications(self):
        return [
            {'type': 'warning', 'icon': '⚠️', 'title': 'مخزون منخفض', 'msg': 'الصنف "أرز بسمتي" وصل للحد الأدنى في مستودع 1', 'time': 'منذ 5 دقائق', 'read': False},
            {'type': 'info', 'icon': '📦', 'title': 'استلام جديد', 'msg': 'تم استلام شحنة جديدة برقم RCP-1023', 'time': 'منذ ساعة', 'read': False},
            {'type': 'success', 'icon': '✅', 'title': 'صرف مكتمل', 'msg': 'تم صرف الكمية المطلوبة لمعسكر 1', 'time': 'منذ 3 ساعات', 'read': True},
            {'type': 'error', 'icon': '❌', 'title': 'فشل تحويل', 'msg': 'فشل تحويل TRF-0089 بسبب عدم توفر الكمية', 'time': 'أمس', 'read': False},
            {'type': 'info', 'icon': '🔄', 'title': 'مزامنة', 'msg': 'تمت مزامنة 25 عملية بنجاح', 'time': 'منذ يومين', 'read': True},
        ]

    def _color_for_type(self, t):
        return {'warning': '#F39C12', 'error': '#E74C3C', 'success': '#27AE60', 'info': '#3498DB'}.get(t, '#95A5A6')

    def _load_notifications(self):
        # Clear existing
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        notifs = self._sample_notifications()
        if not notifs:
            lbl = QLabel('لا توجد إشعارات حالياً')
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color:#7F8C8D; padding:20px;")
            self.list_layout.addWidget(lbl)
            return
        for n in notifs:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: {'#FFFFFF' if n['read'] else '#EBF5FB'}; "
                f"border-left: 5px solid {self._color_for_type(n['type'])}; "
                f"border-radius:6px; padding:10px; margin:4px; }}"
            )
            h = QHBoxLayout(card)
            icon = QLabel(n['icon'])
            icon.setStyleSheet("font-size:28px;")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            h.addWidget(icon)
            body = QVBoxLayout()
            title_lbl = QLabel(f"<b>{n['title']}</b>")
            body.addWidget(title_lbl)
            msg_lbl = QLabel(n['msg'])
            msg_lbl.setStyleSheet("color:#555;")
            msg_lbl.setWordWrap(True)
            body.addWidget(msg_lbl)
            time_lbl = QLabel(f"<small>{n['time']}</small>")
            time_lbl.setStyleSheet("color:#999;")
            body.addWidget(time_lbl)
            h.addLayout(body, 1)
            h.addStretch()
            self.list_layout.addWidget(card)

    def _mark_all_read(self):
        QMessageBox.information(self, 'تم', 'تم تعليم جميع الإشعارات كمقروءة.')
        self._load_notifications()

    def _clear_all(self):
        r = QMessageBox.question(self, 'تأكيد', 'هل أنت متأكد من مسح جميع الإشعارات؟')
        if r == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, 'تم', 'تم مسح جميع الإشعارات.')
