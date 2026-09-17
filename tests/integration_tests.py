"""
اختبارات تكاملية لنظام الإمداد والتموين
"""
import unittest
from data.repositories_impl.repository_factory import RepositoryFactory
from core.security.authentication import authenticate_user, get_password_hash
from core.services.inventory_service import InventoryService
from core.services.transaction_service import TransactionService
from sync.sync_engine import SyncEngine

class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = RepositoryFactory()
        cls.setup_test_data()

    @classmethod
    def setup_test_data(cls):
        # إضافة مستخدم اختباري
        cls.test_user = cls.repo.users.create({
            "username": "test_user",
            "password_hash": get_password_hash("test123"),
            "full_name": "Test User",
            "role": "admin"
        })

        # إضافة صنف اختباري
        cls.test_item = cls.repo.items.create({
            "name": "Test Item",
            "code": "TEST001",
            "base_uom_id": "unit",
            "min_stock_level": 10
        })

        # إضافة مخزن اختباري
        cls.test_warehouse = cls.repo.warehouses.create({
            "name": "Test Warehouse",
            "code": "WH-TEST",
            "type": "main"
        })

    def test_authentication(self):
        # اختبار المصادقة الصحيحة
        user = authenticate_user("test_user", "test123", self.repo)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "test_user")

        # اختبار المصادقة الخاطئة
        user = authenticate_user("test_user", "wrong_pass", self.repo)
        self.assertIsNone(user)

    def test_inventory_operations(self):
        service = InventoryService(self.repo)
        
        # اختبار حساب الأرصدة
        balance = service.get_stock_balance(
            self.test_item.id,
            self.test_warehouse.id,
            "unit"
        )
        self.assertEqual(balance.quantity, 0)

    def test_transaction_processing(self):
        service = TransactionService(self.repo)
        
        # إنشاء سند استلام
        txn = service.create_transaction(
            transaction_type="receive",
            transaction_date="2026-08-21",
            warehouse_to_id=self.test_warehouse.id,
            items=[{
                "item_id": self.test_item.id,
                "uom_id": "unit",
                "quantity": 15
            }],
            user_id=self.test_user.id
        )
        self.assertIsNotNone(txn.id)
        self.assertEqual(txn.transaction_type, "receive")

if __name__ == "__main__":
    unittest.main()