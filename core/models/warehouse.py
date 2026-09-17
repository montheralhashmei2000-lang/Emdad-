"""
نظام الإمداد والتموين - نماذج المخازن والأرصدة
Warehouse & Stock Balance Models
"""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from core.models.base import BaseSchema


class Camp(BaseSchema):
    """المعسكر."""
    name: str = Field(..., min_length=1, max_length=200, description="اسم المعسكر")
    code: str = Field(..., min_length=1, max_length=30, description="رمز المعسكر (فريد)")
    location: Optional[str] = Field(None, max_length=300, description="الموقع")
    contact_phone: Optional[str] = Field(None, max_length=30, description="هاتف التواصل")
    is_active: bool = Field(default=True, description="حالة المعسكر")

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Warehouse(BaseSchema):
    """المخزن / المستودع."""
    camp_id: str = Field(..., description="معرف المعسكر التابع له المخزن")
    name: str = Field(..., min_length=1, max_length=200, description="اسم المخزن")
    code: str = Field(..., min_length=1, max_length=30, description="رمز المخزن")
    type: str = Field(default="main", description="نوع المخزن: main | sub")
    location: Optional[str] = Field(None, max_length=300, description="الموقع")
    is_active: bool = Field(default=True, description="حالة المخزن")

    camp_name: Optional[str] = Field(None, description="اسم المعسكر (للقراءة فقط)")

    def __str__(self) -> str:
        return self.name


class StockBalance(BaseSchema):
    """
    رصيد المخزون الحالي.
    ملاحظة: هذا جدول مشتق (Derived) يعاد حسابه من سجل الحركات، لا يُكتب يدوياً.
    """
    item_id: str = Field(..., description="معرف الصنف")
    warehouse_id: str = Field(..., description="معرف المخزن")
    uom_id: str = Field(..., description="معرف وحدة القياس")
    quantity: float = Field(default=0.0, description="الكمية الحالية")
    last_movement_at: Optional[str] = Field(None, description="تاريخ آخر حركة")

    # حقول للقراءة فقط (تُعبأ عند العرض)
    item_name: Optional[str] = Field(None, description="اسم الصنف (للقراءة فقط)")
    item_code: Optional[str] = Field(None, description="رمز الصنف (للقراءة فقط)")
    warehouse_name: Optional[str] = Field(None, description="اسم المخزن (للقراءة فقط)")
    is_below_min: Optional[bool] = Field(None, description="هل الرصيد تحت الحد الأدنى")