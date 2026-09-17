"""
نظام الإمداد والتموين - رأس التطبيق
Application Header with User Info and Notifications
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, 
    QToolButton, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QAction

class AppHeader(QWidget):
    """رأس التطبيق"""
    logout_clicked = Signal()
    notification_clicked = Signal()
    settings_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.setObjectName("appHeader")
        self.setFixedHeight(60)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(15)
        
        # شعار التطبيق
        self.logo = QLabel()
        self.logo.setPixmap(QIcon(":/icons/logo").pixmap(40, 40))
        layout.addWidget(self.logo)
        
        # عنوان التطبيق
        self.title = QLabel("نظام الإمداد والتموين")
        self.title.setObjectName("appTitle")
        layout.addWidget(self.title)
        
        layout.addStretch(1)
        
        # زر الإشعارات
        self.notif_btn = QToolButton()
        self.notif_btn.setIcon(QIcon(":/icons/notifications"))
        self.notif_btn.setObjectName("notificationButton")
        self.notif_btn.clicked.connect(self.notification_clicked.emit)
        layout.addWidget(self.notif_btn)
        
        # زر الإعدادات
        self.settings_btn = QToolButton()
        self.settings_btn.setIcon(QIcon(":/icons/settings"))
        self.settings_btn.setObjectName("settingsButton")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)
        
        # معلومات المستخدم
        self.user_widget = QWidget()
        self.user_layout = QHBoxLayout(self.user_widget)
        self.user_layout.setContentsMargins(0, 0, 0, 0)
        self.user_layout.setSpacing(10)
        
        self.user_icon = QLabel()
        self.user_icon.setPixmap(QIcon(":/icons/user").pixmap(30, 30))
        self.user_layout.addWidget(self.user_icon)
        
        self.user_info = QLabel()
        self.user_info.setObjectName("userInfo")
        self.user_layout.addWidget(self.user_info)
        
        # قائمة المستخدم
        self.user_menu = QMenu()
        self.profile_action = QAction("الملف الشخصي", self)
        self.logout_action = QAction("تسجيل الخروج", self)
        
        self.user_menu.addAction(self.profile_action)
        self.user_menu.addSeparator()
        self.user_menu.addAction(self.logout_action)
        
        self.logout_action.triggered.connect(self.logout_clicked.emit)
        
        self.user_btn = QPushButton()
        self.user_btn.setMenu(self.user_menu)
        self.user_btn.setObjectName("userButton")
        self.user_layout.addWidget(self.user_btn)
        
        layout.addWidget(self.user_widget)
        
    def set_user_info(self, name: str, role: str, last_login: str = None):
        """تحديث معلومات المستخدم"""
        info_text = f"<b>{name}</b><br><small>{role}"
        if last_login:
            info_text += f"<br>آخر دخول: {last_login}</small>"
        else:
            info_text += "</small>"
            
        self.user_info.setText(info_text)