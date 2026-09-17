"""
اختبارات نماذج البيانات الأساسية
"""
import pytest
from core.models.sync import User
from core.models.item import Item
from core.models.warehouse import Warehouse

def test_user_model():
    user = User(
        username="testuser",
        full_name="اسم اختبار",
        password_hash="hashed_password",
        role="admin"
    )
    assert user.username == "testuser"
    assert user.role == "admin"

def test_item_model():
    item = Item(
        code="TEST001",
        name="صنف اختبار",
        base_uom_id="unit"
    )
    assert item.code == "TEST001"
    assert item.is_active == True  # القيمة الافتراضية

def test_warehouse_model():
    warehouse = Warehouse(
        camp_id="camp_test_01",
        name="مستودع اختبار",
        code="WH01"
    )
    assert warehouse.name == "مستودع اختبار"
    assert warehouse.camp_id == "camp_test_01"
    assert warehouse.is_active == True  # القيمة الافتراضية