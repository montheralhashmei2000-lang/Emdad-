"""
نظام الإمداد والتموين - نماذج إدارة العهد
Custody Models (Issue, Return, Tracking)
"""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from core.models.base import BaseSchema


class Custody(BaseSchema):
    """عقد عهد."""
    custody_no: str = Field(..., description="رقم العهد (فريد داخل المعسكر)")
    employee_name: str = Field(..., min_length=1, max_length=200, description="اسم الموظف")
    employee_rank: Optional[str] = Field(None, max_length=100, description="الرتبة")
    unit_name: Optional[str] = Field(None, max_length=200, description="الوحدة / القسم")
    department: Optional[str] = Field(None, max_length=200, description="الإدارة")

    warehouse_id: str = Field(..., description="المخزن الذي صدرت منه العهدة")
    issue_date: str = Field(..., description="تاريخ الصرف")
    expected_return_date: Optional[str] = Field(None, description="تاريخ الاسترجاع المتوقع")

    status: str = Field(default="active", description="حالة العهد: active | partial | returned | overdue")
    user_id: Optional[str] = Field(None, description="معرف المستخدم الذي أصدر العهدة")
    notes: Optional[str] = Field(None, max_length=1000, description="ملاحظات")

    # حقول للقراءة فقط
    warehouse_name: Optional[str] = Field(None, description="اسم المخزن (للقراءة فقط)")
    user_name: Optional[str] = Field(None, description="اسم المستخدم (للقراءة فقط)")
    total_items: Optional[int] = Field(None, description="عدد الأصناف (للقراءة فقط)")
    remaining_qty: Optional[float] = Field(None, description="إجمالي الكمية المتبقية (للقراءة فقط)")


class CustodyItem(BaseSchema):
    """صنف ضمن عهدة."""
    custody_id: str = Field(..., description="معرف العهد")
    transaction_item_id: Optional[str] = Field(None, description="معرف بند المعاملة المرتبط")
    item_id: str = Field(..., description="معرف الصنف")
    uom_id: str = Field(..., description="معرف وحدة القياس")

    issued_qty: float = Field(..., ge=0, description="الكمية المصروفة")
    returned_qty: float = Field(default=0, ge=0, description="الكمية المسترجعة")
    current_qty: float = Field(default=0, ge=0, description="الكمية الحالية (issued - returned)")
    condition_issued: Optional[str] = Field(None, max_length=200, description="حالة الصنف عند الصرف")

    # حقول للقراءة فقط
    item_name: Optional[str] = Field(None, description="اسم الصنف (للقراءة فقط)")
    item_code: Optional[str] = Field(None, description="رمز الصنف (للقراءة فقط)")
    uom_name: Optional[str] = Field(None, description="اسم الوحدة (للقراءة فقط)")


class CustodyReturn(BaseSchema):
    """سند استرجاع عهد."""
    return_no: str = Field(..., description="رقم سند الاسترجاع (فريد داخل المعسكر)")
    custody_id: str = Field(..., description="معرف العهد")
    return_date: str = Field(..., description="تاريخ الاسترجاع")
    warehouse_id: str = Field(..., description="المخزن المستلم")
    user_id: Optional[str] = Field(None, description="معرف المستخدم")
    notes: Optional[str] = Field(None, max_length=1000, description="ملاحظات")

    # حقول للقراءة فقط
    custody_no: Optional[str] = Field(None, description="رقم العهد (للقراءة فقط)")
    employee_name: Optional[str] = Field(None, description="اسم الموظف (للقراءة فقط)")
    warehouse_name: Optional[str] = Field(None, description="اسم المخزن (للقراءة فقط)")


class CustodyReturnItem(BaseSchema):
    """بند استرجاع عهد."""
    return_id: str = Field(..., description="معرف سند الاسترجاع")
    custody_item_id: str = Field(..., description="معرف صنف العهد")
    item_id: str = Field(..., description="معرف الصنف")
    uom_id: str = Field(..., description="معرف وحدة القياس")
    quantity: float = Field(..., ge=0, description="الكمية المسترجعة")
    condition: str = Field(default="good", description="حالة الصنف: good | damaged | missing")
    damage_notes: Optional[str] = Field(None, max_length=500, description="ملاحظات التلف")

    # حقول للقراءة فقط
    item_name: Optional[str] = Field(None, description="اسم الصنف (للقراءة فقط)")
    item_code: Optional[str] = Field(None, description="رمز الصنف (للقراءة فقط)")
    uom_name: Optional[str] = Field(None, description="اسم الوحدة (للقراءة فقط)")