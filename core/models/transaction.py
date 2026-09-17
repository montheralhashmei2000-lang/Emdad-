"""
نظام الإمداد والتموين - نماذج المعاملات المخزنية
Transaction, Transaction Items, Suppliers Models
"""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from core.models.base import BaseSchema
from core.enums import TransactionType

__all__ = ["Supplier", "TransactionItem", "Transaction", "TransactionType"]


class Supplier(BaseSchema):
    """المورد."""
    name: str = Field(..., min_length=1, max_length=200, description="اسم المورد")
    code: Optional[str] = Field(None, max_length=50, description="رمز المورد")
    phone: Optional[str] = Field(None, max_length=30, description="رقم الهاتف")
    address: Optional[str] = Field(None, max_length=500, description="العنوان")
    tax_number: Optional[str] = Field(None, max_length=50, description="الرقم الضريبي")
    contact_person: Optional[str] = Field(None, max_length=100, description="جهة الاتصال")
    is_active: bool = Field(default=True, description="حالة المورد")


class TransactionItem(BaseSchema):
    """بند المعاملة المخزنية."""
    transaction_id: str = Field(..., description="معرف المعاملة")
    item_id: str = Field(..., description="معرف الصنف")
    uom_id: str = Field(..., description="معرف وحدة القياس")
    quantity: float = Field(..., description="الكمية")
    unit_price: Optional[float] = Field(None, ge=0, description="سعر الوحدة")
    notes: Optional[str] = Field(None, max_length=500, description="ملاحظات")

    # حقول للقراءة فقط
    item_name: Optional[str] = Field(None, description="اسم الصنف (للقراءة فقط)")
    item_code: Optional[str] = Field(None, description="رمز الصنف (للقراءة فقط)")
    uom_name: Optional[str] = Field(None, description="اسم الوحدة (للقراءة فقط)")


class Transaction(BaseSchema):
    """سند معاملة مخزنية."""
    transaction_no: str = Field(..., description="رقم السند (فريد داخل المعسكر)")
    transaction_type: str = Field(..., description="نوع المعاملة")
    transaction_date: str = Field(..., description="تاريخ المعاملة")

    warehouse_from_id: Optional[str] = Field(None, description="المخزن المصدر")
    warehouse_to_id: Optional[str] = Field(None, description="المخزن الوجهة")

    supplier_id: Optional[str] = Field(None, description="معرف المورد")
    recipient_name: Optional[str] = Field(None, max_length=200, description="جهة الاستلام/الصرف")
    custody_id: Optional[str] = Field(None, description="معرف العهد المرتبط")
    user_id: Optional[str] = Field(None, description="معرف المستخدم")
    status: str = Field(default="posted", description="حالة المعاملة: draft | posted | cancelled")

    notes: Optional[str] = Field(None, max_length=1000, description="ملاحظات عامة")
    return_reason: Optional[str] = Field(None, max_length=500, description="سبب الإرجاع لمعاملات المرتجعات")

    # حقول للقراءة فقط
    warehouse_from_name: Optional[str] = Field(None, description="اسم المخزن المصدر (للقراءة فقط)")
    warehouse_to_name: Optional[str] = Field(None, description="اسم المخزن الوجهة (للقراءة فقط)")
    supplier_name: Optional[str] = Field(None, description="اسم المورد (للقراءة فقط)")
    user_name: Optional[str] = Field(None, description="اسم المستخدم (للقراءة فقط)")
    item_count: Optional[int] = Field(None, description="عدد الأصناف في السند (للقراءة فقط)")
    total_qty: Optional[float] = Field(None, description="إجمالي الكميات (للقراءة فقط)")

    # بنود المعاملة (تُعبأ عند الحاجة)
    items: list[TransactionItem] = Field(default_factory=list, description="بنود المعاملة")