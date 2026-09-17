"""
نظام الإمداد والتموين - نماذج المزامنة
Sync Log, Sync Outbox, and User Models
"""
from __future__ import annotations

from typing import Optional

from pydantic import Field

from core.models.base import BaseSchema


class User(BaseSchema):
    """مستخدم النظام."""
    username: str = Field(..., min_length=3, max_length=100, description="اسم المستخدم (فريد)")
    full_name: str = Field(..., min_length=1, max_length=200, description="الاسم الكامل")
    password_hash: str = Field(..., description="هاش كلمة المرور")
    role: str = Field(default="viewer", description="الدور: admin | warehouse | accountant | viewer")
    is_active: bool = Field(default=True, description="حالة المستخدم")


class SyncLog(BaseSchema):
    """سجل جلسة المزامنة."""
    sync_type: str = Field(..., description="نوع المزامنة: push | pull | both")
    status: str = Field(default="in_progress", description="الحالة: in_progress | success | failed | partial")
    started_at: str = Field(default_factory=lambda: str(__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()), description="وقت البدء")
    finished_at: Optional[str] = Field(None, description="وقت الانتهاء")
    records_pushed: int = Field(default=0, description="عدد السجلات المرفوعة")
    records_pulled: int = Field(default=0, description="عدد السجلات المستوردة")
    error_message: Optional[str] = Field(None, max_length=2000, description="رسالة الخطأ (إن وجد)")
    server_url: Optional[str] = Field(None, description="عنوان الخادم المتصل به")


class SyncOutbox(BaseSchema):
    """طابور المزامنة للسجلات المعلقة."""
    entity_type: str = Field(..., description="نوع الكيان (اسم الجدول)")
    entity_id: str = Field(..., description="معرف السجل")
    operation: str = Field(default="upsert", description="نوع العملية: upsert | delete")
    payload_json: str = Field(..., description="لقطة JSON للسجل عند رفعه")
    status: str = Field(default="pending", description="الحالة: pending | failed")
    attempt_count: int = Field(default=0, description="عدد محاولات الرفع")
    last_error: Optional[str] = Field(None, max_length=1000, description="آخر خطأ")
    next_retry_at: Optional[str] = Field(None, description="موعد المحاولة التالية (في حال الفشل)")