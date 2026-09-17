"""
نظام الإمداد والتموين - نموذج سجل التدقيق
Audit Log Model
"""
from __future__ import annotations

from typing import Optional, Any

from pydantic import Field

from core.models.base import BaseSchema


class AuditLog(BaseSchema):
    """
    سجل العمليات والتدقيق.
    يُسجل كل عملية تحدث في النظام: من قام بها، ماذا فعل، ومتى.
    هذا السجل محلي بحت ولا تتم مزامنته (sync_status = syned دائماً).
    """
    user_id: Optional[str] = Field(None, description="معرف المستخدم الذي قام بالعملية")
    username: Optional[str] = Field(None, max_length=200, description="اسم المستخدم (للقراءة فقط)")
    action: str = Field(..., description="الفعل: create | update | delete | sync | login | print | export")
    entity_type: str = Field(..., description="نوع الكيان: items | transactions | custody | ...")
    entity_id: Optional[str] = Field(None, description="معرف الكيان الذي تمت عليه العملية")
    description: Optional[str] = Field(None, max_length=500, description="وصف العملية")
    old_values: Optional[str] = Field(None, description="القيم القديمة بصيغة JSON")
    new_values: Optional[str] = Field(None, description="القيم الجديدة بصيغة JSON")
    ip_address: Optional[str] = Field(None, max_length=50, description="عنوان IP (حسب الإمكانية)")