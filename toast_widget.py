"""Toast notification widget — slides in from top-right and auto-dismisses."""
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont

ACTION_STYLES = {
    'ISSUE': {'icon': '📦', 'label': 'عملية صرف بضاعة', 'color': '#C0392B'},
    'RECEIVE': {'icon': '📥', 'label': 'عملية استلام بضاعة', 'color': '#27AE60'},
    'TRANSFER': {'icon': '🔄', 'label': 'تحويل مخزني', 'color': '#2980B9'},
    'RETURN_IN': {'icon': '↩️', 'label': 'مرتجع للمورد', 'color': '#8E44AD'},
    'RETURN_OUT': {'icon': '↪️', 'label': 'مرتجع من وحدة', 'color': '#E67E22'},
    'LOGIN': {'icon': '👤', 'label': 'تسجيل دخول', 'color': '#34495E'},
    'CREATE_ITEM': {'icon': '✨', 'label': 'إضافة صنف', 'color': '#16A085'},
    'UPDATE_ITEM': {'icon': '📝', 'label': 'تعديل صنف', 'color': '#F39C12'},
}


class ToastNotification(QWidget):
    """Single toast notification that slides in and auto-dismisses."""

    closed = pyqtSignal(object)

    TOAST_WIDTH = 380
    TOAST_HEIGHT = 90
    DISPLAY_MS = 5000

    def __init__(self, activity_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.TOAST_WIDTH, self.TOAST_HEIGHT)

        action = activity_data.get('action', '')
        style = ACTION_STYLES.get(action, {'icon': '🔔', 'label': 'نشاط', 'color': '#2C3E50'})

        container = QWidget(self)
        container.setFixedSize(self.TOAST_WIDTH, self.TOAST_HEIGHT)
        container.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(25, 40, 20, 235);
                border: 2px solid {style['color']};
                border-radius: 10px;
                border-right: 5px solid {style['color']};
            }}
            QLabel {{
                background: transparent;
            }}
        """)

        main_lay = QHBoxLayout(container)
        main_lay.setContentsMargins(12, 8, 12, 8)
        main_lay.setSpacing(10)

        lbl_icon = QLabel(style['icon'])
        lbl_icon.setStyleSheet('font-size: 28px;')
        lbl_icon.setFixedWidth(36)
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_lay.addWidget(lbl_icon)

        text_lay = QVBoxLayout()
        text_lay.setSpacing(2)

        lbl_title = QLabel(f"🔔 {style['label']}")
        lbl_title.setStyleSheet(f"color: {style['color']}; font-weight: bold; font-size: 13px;")
        text_lay.addWidget(lbl_title)

        wh_name = activity_data.get('warehouse_name', '')
        user_name = activity_data.get('user_name', '')
        items_count = activity_data.get('items_count', 0)
        lbl_detail = QLabel(f"الفرع: {wh_name} | المستخدم: {user_name} | {items_count} أصناف")
        lbl_detail.setStyleSheet('color: #BDC3C7; font-size: 11px;')
        lbl_detail.setWordWrap(True)
        text_lay.addWidget(lbl_detail)

        desc = activity_data.get('description', '')
        if desc:
            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet('color: #95A5A6; font-size: 10px;')
            lbl_desc.setWordWrap(True)
            text_lay.addWidget(lbl_desc)

        main_lay.addLayout(text_lay, stretch=1)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._fade_out)

    def slide_in(self, target_y: int):
        """Animate sliding in from above."""
        screen_geo = self.screen().availableGeometry() if self.screen() else None
        if not screen_geo:
            self.move(100, target_y)
            self.show()
            return

        x = screen_geo.right() - self.TOAST_WIDTH - 20
        start_y = target_y - self.TOAST_HEIGHT
        end_y = target_y

        self.move(x, start_y)
        self.show()

        self._slide_anim = QPropertyAnimation(self, b'geometry')
        self._slide_anim.setDuration(350)
        self._slide_anim.setStartValue(QRect(x, start_y, self.TOAST_WIDTH, self.TOAST_HEIGHT))
        self._slide_anim.setEndValue(QRect(x, end_y, self.TOAST_WIDTH, self.TOAST_HEIGHT))
        self._slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._slide_anim.start()

        self._dismiss_timer.start(self.DISPLAY_MS)

    def _fade_out(self):
        """Animate fading out then close."""
        self._fade_anim = QPropertyAnimation(self.opacity_effect, b'opacity')
        self._fade_anim.setDuration(500)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_anim.finished.connect(self._on_done)
        self._fade_anim.start()

    def _on_done(self):
        self.closed.emit(self)
        self.close()
        self.deleteLater()

    def mousePressEvent(self, event):
        """Click to dismiss immediately."""
        self._dismiss_timer.stop()
        self._fade_out()


class ToastManager:
    """Manages multiple toast notifications, stacking them vertically."""

    def __init__(self):
        self._active_toasts = []
        self._base_y = 60

    def show_toast(self, activity_data: dict):
        """Show a new toast notification."""
        toast = ToastNotification(activity_data)
        toast.closed.connect(self._on_toast_closed)

        y = self._base_y + len(self._active_toasts) * (ToastNotification.TOAST_HEIGHT + 8)

        self._active_toasts.append(toast)
        toast.slide_in(y)

    def _on_toast_closed(self, toast):
        if toast in self._active_toasts:
            self._active_toasts.remove(toast)
