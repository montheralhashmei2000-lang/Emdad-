from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class InventoryCountView(QWidget):
    """Inventory Count / Stocktake Screen - placeholder."""

    def __init__(self, parent=None, api_service=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        lbl = QLabel("جرد المخزون - قيد التطوير")
        lbl.setStyleSheet("font-size: 18px; color: #757575;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
