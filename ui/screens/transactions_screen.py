"""
شاشة إدارة المعاملات المخزنية - واجهة المستخدم
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt
from core.enums import TransactionType
from core.models.transaction import Transaction

class TransactionsScreen(QWidget):
    """شاشة إدارة المعاملات المخزنية."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """تهيئة واجهة المستخدم."""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # نموذج إدخال البيانات
        self.form_layout = QFormLayout()
        self._setup_transaction_type_ui()
        self._setup_other_fields()
        self.layout.addLayout(self.form_layout)
        
        # زر الحفظ
        self.save_btn = QPushButton("حفظ المعاملة")
        self.save_btn.clicked.connect(self._save_transaction)
        self.layout.addWidget(self.save_btn)
        
        # جدول العرض
        self.transactions_table = QTableWidget()
        self.layout.addWidget(self.transactions_table)
        
    def _setup_transaction_type_ui(self):
        """إعداد واجهة نوع المعاملة."""
        self.transaction_type_combo = QComboBox()
        for t_type in TransactionType:
            self.transaction_type_combo.addItem(t_type.value, t_type.value)
        self.form_layout.addRow("نوع المعاملة:", self.transaction_type_combo)
        
        # حقل سبب الإرجاع (يظهر فقط عند اختيار نوع مرتجع)
        self.return_reason_edit = QLineEdit()
        self.return_reason_edit.setPlaceholderText("أدخل سبب الإرجاع")
        self.return_reason_edit.setVisible(False)
        self.form_layout.addRow("سبب الإرجاع:", self.return_reason_edit)
        
        # ربط حدث تغيير نوع المعاملة
        self.transaction_type_combo.currentTextChanged.connect(self._update_return_reason_visibility)
    
    def _setup_other_fields(self):
        """إعداد باقي حقول النموذج."""
        # يمكن إضافة باقي الحقول هنا
        pass
        
    def _update_return_reason_visibility(self, t_type):
        """تحديث ظهور حقل سبب الإرجاع حسب نوع المعاملة."""
        self.return_reason_edit.setVisible(t_type == TransactionType.RETURN.value)
        
    def _save_transaction(self):
        """حفظ المعاملة في قاعدة البيانات."""
        # جمع البيانات من النموذج
        transaction_data = {
            "transaction_type": self.transaction_type_combo.currentData(),
            "return_reason": self.return_reason_edit.text() if self.transaction_type_combo.currentData() == TransactionType.RETURN.value else None,
            # إضافة باقي الحقول
        }
        
        # التحقق من صحة البيانات
        if transaction_data["transaction_type"] == TransactionType.RETURN.value and not transaction_data["return_reason"]:
            print("خطأ: يجب إدخال سبب الإرجاع لمعاملات المرتجعات")
            return
            
        try:
            # استدعاء خدمة حفظ المعاملة
            from core.services.transaction_service import TransactionService
            from data.repositories_impl.repository_factory import RepositoryFactory
            
            service = TransactionService(RepositoryFactory())
            created_txn = service.create_transaction(
                transaction_type=transaction_data["transaction_type"],
                transaction_date="2026-08-21",  # سيتم استبدالها بتاريخ حقيقي
                return_reason=transaction_data["return_reason"],
                # إضافة باقي الحقول
            )
            
            print("تم حفظ المعاملة بنجاح:", created_txn.transaction_no)
            self.load_transactions()  # تحديث الجدول بعد الحفظ
            
        except Exception as e:
            print("حدث خطأ أثناء حفظ المعاملة:", str(e))
        
    def load_transactions(self):
        """تحميل المعاملات وعرضها في الجدول."""
        # تهيئة الجدول
        self.transactions_table.setColumnCount(6)
        self.transactions_table.setHorizontalHeaderLabels([
            "رقم السند", "النوع", "التاريخ", "الكمية", "الحالة", "سبب الإرجاع"
        ])
        
        # جلب البيانات من الخدمة
        try:
            from core.services.transaction_service import TransactionService
            from data.repositories_impl.repository_factory import RepositoryFactory
            
            service = TransactionService(RepositoryFactory())
            transactions = service.list_transactions(
                limit=100,
                transaction_type=None,
                status="posted"
            )
        except Exception as e:
            print("حدث خطأ أثناء جلب المعاملات:", str(e))
            transactions = []
        
        self.transactions_table.setRowCount(len(transactions))
        
        for row, txn in enumerate(transactions):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(txn.transaction_no))
            self.transactions_table.setItem(row, 1, QTableWidgetItem(txn.transaction_type))
            self.transactions_table.setItem(row, 2, QTableWidgetItem(txn.transaction_date))
            self.transactions_table.setItem(row, 3, QTableWidgetItem(str(txn.total_qty)))
            self.transactions_table.setItem(row, 4, QTableWidgetItem(txn.status))
            
            # عرض سبب الإرجاع فقط لمعاملات المرتجعات
            if txn.transaction_type == TransactionType.RETURN.value:
                self.transactions_table.setItem(row, 5, QTableWidgetItem(txn.return_reason or ""))
            else:
                self.transactions_table.setItem(row, 5, QTableWidgetItem(""))
        
        # ضبط أبعاد الأعمدة
        self.transactions_table.resizeColumnsToContents()
        
    def _highlight_return_transactions(self):
        """تمييز معاملات المرتجعات بلون مختلف."""
        for row in range(self.transactions_table.rowCount()):
            if self.transactions_table.item(row, 1).text() == TransactionType.RETURN.value:
                for col in range(self.transactions_table.columnCount()):
                    self.transactions_table.item(row, col).setBackground(Qt.yellow)
