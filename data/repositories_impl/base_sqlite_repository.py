"""
نظام الإمداد والتموين - التنفيذ العام للمستودعات (SQLite)
Generic SQLite Repository Implementation
"""
from __future__ import annotations

import json
from typing import Generic, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from data.database import get_session
from data.orm_models import BaseMixin, AuditLogModel, SyncOutboxModel
from core.enums import SyncStatus, AuditAction
from core.repositories.base_repository import BaseRepository

T = TypeVar("T", bound=BaseModel)


class BaseSQLiteRepository(BaseRepository[T]):
    """
    مستودع SQLite عام يعمل مع أي نموذج Pydantic ونموذج ORM مقابل.
    يستخدم SQLAlchemy للتعامل مع قاعدة البيانات.
    """

    def __init__(
        self,
        session: Session,
        orm_model_class: Type,
        pydantic_model_class: Type[T],
        entity_type_name: str,
    ):
        self.session = session
        self.orm_class = orm_model_class
        self.pydantic_class = pydantic_model_class
        self.entity_type = entity_type_name

    def _orm_to_pydantic(self, orm_obj) -> T:
        """تحويل كائن ORM إلى نموذج Pydantic.

        في Pydantic v2 يجب استخدام from_attributes=True لقبول كائنات ORM
        مثل SQLAlchemy. الافتراضي صارم ويتوقع dict أو instance من نفس النموذج.
        """
        if orm_obj is None:
            raise ValueError("ORM object is None")
        try:
            return self.pydantic_class.model_validate(orm_obj, from_attributes=True)
        except Exception:
            # Fallback: استخرج الأعمدة يدوياً وأمررها كقاموس
            if hasattr(orm_obj, "__table__"):
                data = {col.name: getattr(orm_obj, col.name, None) for col in orm_obj.__table__.columns}
                return self.pydantic_class.model_validate(data)
            raise

    def _apply_base_filters(self, query, camp_id=None, include_deleted=False, **filters):
        """تطبيق الفلاتر الأساسية على الاستعلام."""
        if not include_deleted:
            query = query.filter(self.orm_class.is_deleted == 0)
        if camp_id is not None:
            query = query.filter(self.orm_class.camp_id == camp_id)
        for key, value in filters.items():
            if value is not None and hasattr(self.orm_class, key):
                query = query.filter(getattr(self.orm_class, key) == value)
        return query

    def get_by_id(self, entity_id: str) -> Optional[T]:
        obj = self.session.query(self.orm_class).filter(
            self.orm_class.id == entity_id,
            self.orm_class.is_deleted == 0,
        ).first()
        if obj is None:
            return None
        return self._orm_to_pydantic(obj)

    def list_all(
        self,
        camp_id: Optional[str] = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> list[T]:
        query = self.session.query(self.orm_class)
        query = self._apply_base_filters(query, camp_id, include_deleted, **filters)
        query = query.order_by(self.orm_class.created_at.desc())
        query = query.limit(limit).offset(offset)
        return [self._orm_to_pydantic(obj) for obj in query.all()]

    def create(self, entity: T | dict) -> T:
        if isinstance(entity, dict):
            entity = self.pydantic_class(**entity)
        data = entity.model_dump()
        data.pop("id", None)  # سيتم توليده من النموذج
        # إزالة الحقول المشتقة (للقراءة فقط)
        for field in list(data.keys()):
            if field.endswith("_name") or field in ("item_count", "total_qty", "remaining_qty"):
                data.pop(field, None)

        orm_obj = self.orm_class(id=entity.id, **data)
        self.session.add(orm_obj)
        self.session.flush()
        return self._orm_to_pydantic(orm_obj)

    def update(self, entity: T | dict) -> T:
        if isinstance(entity, dict):
            entity = self.pydantic_class(**entity)
        orm_obj = self.session.query(self.orm_class).filter(
            self.orm_class.id == entity.id,
            self.orm_class.is_deleted == 0,
        ).first()
        if orm_obj is None:
            raise ValueError(f"الكيان {entity.id} غير موجود.")

        data = entity.model_dump()
        # إزالة الحقول المشتقة
        for field in list(data.keys()):
            if field.endswith("_name") or field in ("item_count", "total_qty", "remaining_qty"):
                data.pop(field, None)

        for key, value in data.items():
            if hasattr(orm_obj, key):
                setattr(orm_obj, key, value)

        self.session.flush()
        return self._orm_to_pydantic(orm_obj)

    def delete(self, entity_id: str, soft: bool = True) -> bool:
        orm_obj = self.session.query(self.orm_class).filter(
            self.orm_class.id == entity_id,
        ).first()
        if orm_obj is None:
            return False
        if soft:
            orm_obj.is_deleted = 1
            orm_obj.sync_status = SyncStatus.PENDING.value
        else:
            self.session.delete(orm_obj)
        self.session.flush()
        return True

    def count(self, camp_id: Optional[str] = None, **filters) -> int:
        from sqlalchemy import func
        query = self.session.query(func.count(self.orm_class.id))
        query = self._apply_base_filters(query, camp_id, **filters)
        return query.scalar() or 0

    def get_pending_sync(self, camp_id: Optional[str] = None, limit: int = 50) -> list[T]:
        query = self.session.query(self.orm_class).filter(
            self.orm_class.sync_status == SyncStatus.PENDING.value,
            self.orm_class.is_deleted == 0,
        )
        if camp_id:
            query = query.filter(self.orm_class.camp_id == camp_id)
        query = query.limit(limit)
        return [self._orm_to_pydantic(obj) for obj in query.all()]

    def mark_synced(self, entity_id: str) -> bool:
        orm_obj = self.session.query(self.orm_class).filter(
            self.orm_class.id == entity_id,
        ).first()
        if orm_obj is None:
            return False
        orm_obj.sync_status = SyncStatus.SYNCED.value
        orm_obj.updated_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat()
        self.session.flush()
        return True

    def mark_failed(self, entity_id: str, error: Optional[str] = None) -> bool:
        orm_obj = self.session.query(self.orm_class).filter(
            self.orm_class.id == entity_id,
        ).first()
        if orm_obj is None:
            return False
        orm_obj.sync_status = SyncStatus.FAILED.value
        orm_obj.updated_at = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat()
        self.session.flush()
        return True

    def add_to_sync_outbox(self, entity_id: str, operation: str = "upsert") -> None:
        """إضافة السجل إلى طابور المزامنة."""
        orm_obj = self.session.query(self.orm_class).filter(
            self.orm_class.id == entity_id,
        ).first()
        if orm_obj is None:
            return

        # تحويل إلى JSON
        import json as json_lib
        payload = {}
        for col in self.orm_class.__table__.columns:
            val = getattr(orm_obj, col.name, None)
            if isinstance(val, (bytes, bytearray)):
                val = None
            payload[col.name] = val

        outbox = SyncOutboxModel(
            id=__import__("uuid").uuid4().hex,
            entity_type=self.entity_type,
            entity_id=entity_id,
            operation=operation,
            payload_json=json_lib.dumps(payload, ensure_ascii=False, default=str),
            status="pending",
            attempt_count=0,
            camp_id=orm_obj.camp_id,
            created_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
            updated_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        )
        # تحديث sync_status إلى pending
        orm_obj.sync_status = SyncStatus.PENDING.value
        self.session.add(outbox)
        self.session.flush()