"""
نظام الإمداد والتموين - نماذج الأصناف والمواد
Item, Category, Units of Measure Models
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from core.models.base import BaseSchema


class ItemCategory(BaseSchema):
    """فئة الأصناف (تسلسل هرمي)."""
    name: str = Field(..., min_length=1, max_length=200, description="اسم الفئة")
    code: Optional[str] = Field(None, max_length=50, description="رمز الفئة")
    parent_id: Optional[str] = Field(None, description="الفئة الأب (null = فئة جذرية)")
    description: Optional[str] = Field(None, max_length=500, description="وصف")


class UnitOfMeasure(BaseSchema):
    """وحدة قياس أساسية."""
    name: str = Field(..., min_length=1, max_length=100, description="اسم الوحدة")
    abbreviation: str = Field(..., min_length=1, max_length=20, description="اختصار الوحدة")
    is_base_unit: bool = Field(default=False, description="هل هي وحدة أساسية")

    def __str__(self) -> str:
        return f"{self.name} ({self.abbreviation})"


class ItemUnit(BaseSchema):
    """وحدة قياس لصنف محدد مع عامل التحويل."""
    item_id: str = Field(..., description="معرف الصنف")
    uom_id: str = Field(..., description="معرف وحدة القياس")
    conversion_factor: float = Field(default=1.0, gt=0, description="عامل التحويل للوحدة الأساسية")
    is_default_purchase: bool = Field(default=False, description="وحدة الشراء الافتراضية")
    is_default_issue: bool = Field(default=False, description="وحدة الصرف الافتراضية")


class Item(BaseSchema):
    """صنف / مادة."""
    code: str = Field(..., min_length=1, max_length=50, description="رمز الصنف (فريد)")
    name: str = Field(..., min_length=1, max_length=300, description="اسم الصنف")
    description: Optional[str] = Field(None, max_length=1000, description="وصف الصنف")

    category_id: Optional[str] = Field(None, description="معرف الفئة")
    base_uom_id: str = Field(..., description="معرف وحدة القياس الأساسية")

    # خصائص الصنف
    is_consumable: bool = Field(default=True, description="صنف قابل للاستهلاك")
    is_refillable: bool = Field(default=False, description="صنف قابل للتعبئة (مثل أسطوانة الغاز)")
    is_serialized: bool = Field(default=False, description="تتبع بالأرقام التسلسلية (مستقبلي)")
    requires_dangerous_goods: bool = Field(default=False, description="صنف خطير")

    # الحدود
    min_stock_level: float = Field(default=0, ge=0, description="الحد الأدنى للرصيد")
    max_stock_level: Optional[float] = Field(None, gt=0, description="الحد الأعلى للرصيد")

    # التتبع
    is_active: bool = Field(default=True, description="حالة الصنف")
    last_restock_date: Optional[str] = Field(None, description="تاريخ آخر إعادة تخزين")
    last_issue_date: Optional[str] = Field(None, description="تاريخ آخر صرف")
    notes: Optional[str] = Field(None, max_length=2000, description="ملاحظات عامة")

    # العلاقات (تُعبأ عند الحاجة)
    units: List[ItemUnit] = Field(default_factory=list, description="وحدات قياس الصنف")
    category_name: Optional[str] = Field(None, description="اسم الفئة (للقراءة فقط)")
    base_uom_name: Optional[str] = Field(None, description="اسم الوحدة الأساسية (للقراءة فقط)")


class ItemPrice(BaseSchema):
    """سعر صنف."""
    item_id: str = Field(..., description="معرف الصنف")
    price_type: str = Field(..., description="نوع السعر: purchase | issue")
    price: float = Field(..., ge=0, description="قيمة السعر")
    effective_date: str = Field(..., description="تاريخ سريان السعر")