"""
نظام الإمداد والتموين - شاشة المزامنة
Sync Screen (PyQt6)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt


class SyncScreen(QWidget):
    """شاشة المزامنة - PyQt6 placeholder."""

    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api_service = api_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("المزامنة مع الخادم المركزي")
        lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #1B5E20;")
        layout.addWidget(lbl)

        self.btn_sync = QPushButton("مزامنة الآن")
        self.btn_sync.clicked.connect(self._sync)
        layout.addWidget(self.btn_sync)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def _sync(self):
        try:
            if self.api_service:
                ok, data = self.api_service.sync_now()
                if ok:
                    self.log.append("✅ تمت المزامنة بنجاح")
                else:
                    self.log.append(f"⚠️ {data.get('error', 'خطأ غير معروف')}")
            else:
                self.log.append("⚠️ ApiService غير متاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل المزامنة: {e}")
