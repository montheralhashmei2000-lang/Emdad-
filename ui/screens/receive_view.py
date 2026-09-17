"""
نظام الإمداد والتموين - شاشة استلام المخزون
Inventory Receiving Screen
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon

from core.models.transaction import Transaction, TransactionType
from core.models.item import Item
from core.models.warehouse import Warehouse
from core.services.transaction_service import TransactionService

class ReceiveView(QWidget):
    """شاشة استلام المخزون"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("سند استلام مخزني")
        self.setWindowIcon(QIcon(":/icons/receive"))
        
        self.transaction_service = TransactionService()
        self._setup_ui()
        
    def _setup_ui(self):
        """تهيئة واجهة المستخدم"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # معلومات السند الأساسية
        form_layout = QHBoxLayout()
        
        # تاريخ الاستلام
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addWidget(QLabel("تاريخ الاستلام:"))
        form_layout.addWidget(self.date_edit)
        
        # المستودع
        self.warehouse_combo = QComboBox()
        form_layout.addWidget(QLabel("المستودع:"))
        form_layout.addWidget(self.warehouse_combo)
        
        # المورد
        self.supplier_combo = QComboBox()
        form_layout.addWidget(QLabel("المورد:"))
        form_layout.addWidget(self.supplier_combo)
        
        main_layout.addLayout(form_layout)
        
        # جدول بنود الاستلام
        self.items_table = QTableView()
        self.items_table.setSelectionBehavior(QTableView.SelectRows)
        main_layout.addWidget(self.items_table, stretch=1)
        
        # شريط أدوات البنود
        items_toolbar = QHBoxLayout()
        
        add_item_btn = QPushButton("إضافة صنف")
        add_item_btn.setIcon(QIcon(":/icons/add"))
        add_item_btn.clicked.connect(self._add_item_row)
        items_toolbar.addWidget(add_item_btn)
        
        remove_item_btn = QPushButton("حذف صنف")
        remove_item_btn.setIcon(QIcon(":/icons/remove"))
        remove_item_btn.clicked.connect(self._remove_item_row)
        items_toolbar.addWidget(remove_item_btn)
        
        items_toolbar.addStretch()
        main_layout.addLayout(items_toolbar)
        
        # زر الحفظ
        save_btn = QPushButton("حفظ السند")
        save_btn.setIcon(QIcon(":/icons/save"))
        save_btn.clicked.connect(self._save_receipt)
        main_layout.addWidget(save_btn)
        
        # تحميل البيانات الأولية
        self._load_init_data()
        
    def _load_init_data(self):
        """تحميل البيانات الأولية"""
        try:
            # تحميل المستودعات
            warehouses = self.transaction_service.get_warehouses()
            self.warehouse_combo.clear()
            for wh in warehouses:
                self.warehouse_combo.addItem(wh.name, wh.id)
                
            # TODO: تحميل الموردين
            # TODO: تحميل الأصناف
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل البيانات: {str(e)}")
            
    def _add_item_row(self):
        """إضافة صف جديد لصنف"""
        # TODO: تنفيذ إضافة صف جديد
        pass
        
    def _remove_item_row(self):
        """حذف الصف المحدد"""
        # TODO: تنفيذ حذف الصف
        pass
        
    def _save_receipt(self):
        """حفظ سند الاستلام"""
        try:
            receipt = Transaction(
                transaction_type=TransactionType.RECEIVE,
                transaction_date=self.date_edit.date().toString(Qt.ISODate),
                warehouse_id=self.warehouse_combo.currentData(),
                # TODO: إضافة باقي الحقول
            )
            
            # TODO: إضافة البنود
            
            saved = self.transaction_service.create_transaction(receipt)
            QMessageBox.information(self, "تم", f"تم حفظ السند رقم {saved.transaction_no}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ السند: {str(e)}")