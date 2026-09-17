"""
نظام الإمداد والتموين - النموذج الأساسي
Base Model with common fields for all domain models (UUID, timestamps, sync)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

from core.enums import SyncStatus


def generate_uuid() -> str:
    """توليد UUID v4 كمعرف فريد عالمي."""
    return str(uuid.uuid4())


def utc_now() -> str:
    """إرجاع الوقت الحالي بتنسيق ISO8601 UTC."""
    return datetime.now(timezone.utc).isoformat()


class BaseSchema(BaseModel):
    """
    النموذج الأساسي لجميع كيانات النظام.
    يحتوي على الحقول المشتركة للمزامنة والتتبع.
    """
    id: str = Field(default_factory=generate_uuid, description="المعرف الفريد UUID v4")
    camp_id: Optional[str] = Field(None, description="معرف المعسكر المالك للسجل")
    created_at: str = Field(default_factory=utc_now, description="تاريخ الإنشاء (ISO8601 UTC)")
    updated_at: str = Field(default_factory=utc_now, description="تاريخ آخر تحديث (ISO8601 UTC)")
    sync_status: SyncStatus = Field(default=SyncStatus.PENDING, description="حالة المزامنة")
    is_deleted: bool = Field(default=False, description="حذف ناعم (Soft Delete)")
    created_by: Optional[str] = Field(None, description="معرف المستخدم المنشئ")
    updated_by: Optional[str] = Field(None, description="معرف المستخدم المعدل")
    version: int = Field(default=1, description="رقم إصدار السجل")

    @field_validator("id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        """التحقق من صحة UUID v4."""
        try:
            uuid.UUID(v, version=4)
        except ValueError:
            raise ValueError(f"معرف غير صالح: {v} يجب أن يكون UUID v4")
        return v

    def mark_updated(self) -> None:
        """تحديث حقل updated_at إلى الوقت الحالي."""
        self.updated_at = utc_now()

    def mark_synced(self) -> None:
        """تحديث حالة المزامنة إلى Synced."""
        self.sync_status = SyncStatus.SYNCED
        self.mark_updated()

    def mark_failed(self) -> None:
        """تحديث حالة المزامنة إلى Failed."""
        self.sync_status = SyncStatus.FAILED
        self.mark_updated()

    def soft_delete(self) -> None:
        """حذف ناعم (وضع علامة محذوف)."""
        self.is_deleted = True
        self.mark_updated()

        model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        populate_by_name=True,
    )