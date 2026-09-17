"""
نظام الإمداد والتموين - خدمة سجل التدقيق
Audit Service - logs all system actions
"""
from __future__ import annotations

from typing import Optional

from core.models.audit import AuditLog
from core.models.base import utc_now
from data.repositories_impl.repository_factory import RepositoryFactory


class AuditService:
    """تسجيل جميع عمليات النظام للتدقيق."""

    def __init__(self, repo_factory: RepositoryFactory):
        self.repo = repo_factory
        self.audit_repo = repo_factory.audit_logs

    def log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        camp_id: Optional[str] = None,
    ) -> AuditLog:
        """تسجيل حدث في سجل التدقيق."""
        import json

        entry = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            old_values=json.dumps(old_values, ensure_ascii=False) if old_values else None,
            new_values=json.dumps(new_values, ensure_ascii=False) if new_values else None,
            camp_id=camp_id,
            sync_status="synced",  # سجل محلي لا تتم مزامنته
        )
        return self.audit_repo.create(entry)

    def log_create(
        self,
        entity_type: str,
        entity_id: str,
        new_values: dict,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        camp_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AuditLog:
        """تسجيل عملية إنشاء."""
        return self.log(
            action="create",
            entity_type=entity_type,
            entity_id=entity_id,
            description=description or f"إنشاء {entity_type} جديد",
            user_id=user_id,
            username=username,
            new_values=new_values,
            camp_id=camp_id,
        )

    def log_update(
        self,
        entity_type: str,
        entity_id: str,
        old_values: dict,
        new_values: dict,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        camp_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AuditLog:
        """تسجيل عملية تحديث."""
        return self.log(
            action="update",
            entity_type=entity_type,
            entity_id=entity_id,
            description=description or f"تحديث {entity_type}",
            user_id=user_id,
            username=username,
            old_values=old_values,
            new_values=new_values,
            camp_id=camp_id,
        )

    def log_delete(
        self,
        entity_type: str,
        entity_id: str,
        old_values: dict,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        camp_id: Optional[str] = None,
    ) -> AuditLog:
        """تسجيل عملية حذف."""
        return self.log(
            action="delete",
            entity_type=entity_type,
            entity_id=entity_id,
            description=f"حذف {entity_type}",
            user_id=user_id,
            username=username,
            old_values=old_values,
            camp_id=camp_id,
        )

    def log_sync(
        self,
        description: str,
        user_id: Optional[str] = None,
        camp_id: Optional[str] = None,
    ) -> AuditLog:
        """تسجيل عملية مزامنة."""
        return self.log(
            action="sync",
            entity_type="sync",
            description=description,
            user_id=user_id,
            camp_id=camp_id,
        )

    def log_login(
        self,
        user_id: str,
        username: str,
        camp_id: Optional[str] = None,
    ) -> AuditLog:
        """تسجيل دخول مستخدم."""
        return self.log(
            action="login",
            entity_type="user",
            entity_id=user_id,
            description=f"تسجيل دخول المستخدم {username}",
            user_id=user_id,
            username=username,
            camp_id=camp_id,
        )

    def get_recent_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        camp_id: Optional[str] = None,
    ) -> list[AuditLog]:
        """الحصول على أحدث سجلات التدقيق."""
        return self.audit_repo.list_all(
            camp_id=camp_id,
            limit=limit,
            offset=offset,
            action=action,
            entity_type=entity_type,
        )