"""
نظام الإمداد والتموين - نماذج الجرد الدوري
Stocktake Models
"""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from core.models.base import BaseSchema


class Stocktake(BaseSchema):
    """دورة جرد دوري."""
    stocktake_no: str = Field(..., description="رقم الجرد (فريد داخل المعسكر)")
    warehouse_id: str = Field(..., description="معرف المخزن الذي يتم جرده")
    stocktake_date: str = Field(..., description="تاريخ الجرد")
    user_id: Optional[str] = Field(None, description="معرف المستخدم (المدقق)")
    status: str = Field(default="draft", description="حالة الجرد: draft | completed | cancelled")
    notes: Optional[str] = Field(None, max_length=1000, description="ملاحظات")

    # حقول للقراءة فقط
    warehouse_name: Optional[str] = Field(None, description="اسم المخزن (للقراءة فقط)")
    user_name: Optional[str] = Field(None, description="اسم المستخدم (للقراءة فقط)")
    total_items: Optional[int] = Field(None, description="عدد الأصناف المجردة (للقراءة فقط)")
    has_differences: Optional[bool] = Field(None, description="هل يوجد فروقات جرد (للقراءة فقط)")


class StocktakeItem(BaseSchema):
    """بند جرد - صنف واحد مع الفرق بين النظامي والفعلي."""
    stocktake_id: str = Field(..., description="معرف الجرد")
    item_id: str = Field(..., description="معرف الصنف")
    uom_id: str = Field(..., description="معرف وحدة القياس")

    system_qty: float = Field(default=0, description="الكمية النظامية (من رصيد المخزون)")
    counted_qty: float = Field(default=0, description="الكمية الفعلية المعدودة")
    difference_qty: float = Field(default=0, description="الفرق = counted - system")
    notes: Optional[str] = Field(None, max_length=500, description="ملاحظات حول الفرق")

    # حقول للقراءة فقط
    item_name: Optional[str] = Field(None, description="اسم الصنف (للقراءة فقط)")
    item_code: Optional[str] = Field(None, description="رمز الصنف (للقراءة فقط)")
    uom_name: Optional[str] = Field(None, description="اسم الوحدة (للقراءة فقط)")