from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, pyqtProperty, QPropertyAnimation
import qtawesome as qta

from theme import COLORS


class LoadingOverlay(QWidget):
    def __init__(self, parent=None, text='جاري التحميل...'):
        super().__init__(parent)
        self.text = text
        self._init_ui()

    def _init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setStyleSheet('background-color: rgba(0, 0, 0, 180); border-radius: 10px;')

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.spinner_lbl = QLabel()
        self.spinner_lbl.setStyleSheet('background: transparent; color: white;')
        self.spinner_icon = qta.icon('fa5s.spinner', color='white', animation=qta.Spin(self.spinner_lbl))
        self.spinner_lbl.setPixmap(self.spinner_icon.pixmap(64, 64))

        self.text_lbl = QLabel(self.text)
        self.text_lbl.setStyleSheet(f"color: {COLORS['gold']}; font-size: 18px; font-weight: bold; background: transparent;")
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(self.spinner_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.text_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

    def show_overlay(self, text=None):
        if text:
            self.text_lbl.setText(text)
        if self.parent():
            self.resize(self.parent().size())
        self.raise_()
        self.show()

    def hide_overlay(self):
        self.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.parent():
            self.resize(self.parent().size())
