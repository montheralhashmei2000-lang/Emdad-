"""
اختبارات خدمات النظام
"""
import pytest
from core.services.inventory_service import InventoryService
from data.repositories_impl.repository_factory import RepositoryFactory

@pytest.fixture
def inventory_service():
    return InventoryService(RepositoryFactory())

def test_get_inventory_summary(inventory_service):
    # اختبار جلب ملخص المخزون
    result = inventory_service.get_inventory_summary()
    assert isinstance(result, list)
    # يمكن إضافة المزيد من التحققات حسب منطق العمل