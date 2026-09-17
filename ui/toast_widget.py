"""
نظام الإمداد والتموين - إدارة الإشعارات المنبثقة
Toast notification manager for the desktop UI.
"""
from __future__ import annotations

import time
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QFrame, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
)


class Toast(QFrame):
    """إشعار منبثق واحد"""

    def __init__(self, message: str, parent=None, duration_ms: int = 4000):
        super().__init__(parent)
        self.duration_ms = duration_ms
        self.setObjectName("toast")
        self.setStyleSheet(
            "QFrame#toast { background-color: #323232; color: white;"
            " border-radius: 6px; padding: 8px 12px; }"
            "QFrame#toast QLabel { color: white; font-size: 13px; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.lbl = QLabel(message)
        self.lbl.setWordWrap(True)
        layout.addWidget(self.lbl)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(20, 20)
        btn_close.setStyleSheet("background: transparent; color: white; border: none;")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        QTimer.singleShot(duration_ms, self.close)


class ToastManager:
    """مدير الإشعارات المنبثقة - يعرض توستات أعلى يمين الشاشة."""

    def __init__(self, parent=None):
        self.parent = parent
        self._toasts: list[Toast] = []

    def show_toast(self, activity: dict):
        """عرض إشعار بناءً على نشاط المستخدم."""
        try:
            message = self._format_activity(activity)
            self.show_message(message)
        except Exception:
            pass

    def show_message(self, message: str, duration_ms: int = 4000):
        """عرض إشعار نصي."""
        try:
            toast = Toast(message, parent=self.parent, duration_ms=duration_ms)
            toast.setWindowFlags(
                Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
            )
            toast.adjustSize()
            self._position_toast(toast)
            toast.show()
            self._toasts.append(toast)
        except Exception:
            pass

    def _format_activity(self, activity: dict) -> str:
        user = activity.get("user_name") or activity.get("username", "مستخدم")
        action = activity.get("action", "")
        entity = activity.get("entity_type", "")
        return f"{user}: {action} على {entity}"

    def _position_toast(self, toast: Toast):
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                return
            geo = screen.availableGeometry()
            w, h = toast.width(), toast.height()
            x = geo.right() - w - 20
            y = geo.top() + 20 + (len(self._toasts) * (h + 8))
            toast.move(QPoint(x, y))
        except Exception:
            pass
