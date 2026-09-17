"""
نظام الإمداد والتموين - الشريط الجانبي
Application Sidebar with Navigation Menu
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

class Sidebar(QFrame):
    """الشريط الجانبي للتطبيق"""
    menu_item_clicked = Signal(str)  # يرسل معرف العنصر عند النقر
    
    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(250)
        
        # قائمة العناصر
        self.menu_items = []
        self.active_item = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(5)
        
        # منطقة العنوان
        title_label = QLabel("نظام الإمداد")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("sidebarTitle")
        layout.addWidget(title_label)
        
        # منطقة القائمة
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.menu_widget = QWidget()
        self.menu_layout = QVBoxLayout(self.menu_widget)
        self.menu_layout.setContentsMargins(0, 10, 0, 10)
        self.menu_layout.setSpacing(5)
        
        self.scroll_area.setWidget(self.menu_widget)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # زر تسجيل الخروج
        self.logout_btn = QPushButton("تسجيل الخروج")
        self.logout_btn.setIcon(QIcon(":/icons/logout"))
        self.logout_btn.setObjectName("logoutButton")
        layout.addWidget(self.logout_btn)
        
    def add_menu_item(self, id: str, title: str, icon: QIcon = None):
        """إضافة عنصر جديد إلى القائمة"""
        btn = QPushButton(title)
        btn.setObjectName(f"menuItem_{id}")
        btn.setProperty("menu_item_id", id)
        btn.setCheckable(True)
        
        if icon:
            btn.setIcon(icon)
        
        btn.clicked.connect(lambda: self._on_item_clicked(id))
        self.menu_items.append(id)
        self.menu_layout.addWidget(btn)
        
    def _on_item_clicked(self, item_id: str):
        """عند النقر على عنصر في القائمة"""
        self.set_active_item(item_id)
        self.menu_item_clicked.emit(item_id)
        
    def set_active_item(self, item_id: str):
        """تحديد العنصر النشط"""
        if self.active_item:
            # إلغاء تنشيط العنصر السابق
            prev_btn = self.findChild(QPushButton, f"menuItem_{self.active_item}")
            if prev_btn:
                prev_btn.setChecked(False)
        
        # تنشيط العنصر الجديد
        new_btn = self.findChild(QPushButton, f"menuItem_{item_id}")
        if new_btn:
            new_btn.setChecked(True)
            self.active_item = item_id
            
    def get_menu_item_index(self, item_id: str) -> int:
        """الحصول على مؤشر العنصر في القائمة"""
        try:
            return self.menu_items.index(item_id)
        except ValueError:
            return -1
            
    def count(self) -> int:
        """عدد العناصر في القائمة"""
        return len(self.menu_items)