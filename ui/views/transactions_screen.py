"""
نظام الإمداد والتموين - شاشة المعاملات
Transactions Screen (PyQt6)
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class TransactionsScreen(QWidget):
    """شاشة المعاملات - PyQt6 placeholder."""

    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        self.api_service = api_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("سجل المعاملات - قيد التطوير")
        lbl.setStyleSheet("font-size: 18px; color: #757575;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
