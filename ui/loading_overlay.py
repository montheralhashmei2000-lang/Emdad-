"""
نظام الإمداد والتموين - طبقة التحميل
Loading overlay widget shown on top of widgets during long operations.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication


class LoadingOverlay(QWidget):
    """طبقة شفافة تعرض 'جاري التحميل...' فوق الـ parent."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAutoFillBackground(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addStretch()

        self.label = QLabel("جاري التحميل...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            "QLabel { color: white; background-color: rgba(27, 94, 32, 220);"
            " font-size: 18px; font-weight: bold; padding: 20px 40px;"
            " border-radius: 8px; }"
        )
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_overlay(self, message: str = "جاري التحميل...", auto_hide_ms: int | None = None):
        """تظهر overlay مع رسالة تحميل"""
        return self.show_with_message(message, auto_hide_ms)

    def hide_overlay(self):
        """تخفي overlay"""
        self.hide()

    def show_with_message(self, message: str = "جاري التحميل...", auto_hide_ms: int | None = None):
        self.label.setText(message)
        try:
            if self.parent() is not None:
                self.resize(self.parent().size())
                self.move(0, 0)
        except Exception:
            pass
        self.show()
        self.raise_()
        if auto_hide_ms:
            self._hide_timer.start(auto_hide_ms)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        super().paintEvent(event)
