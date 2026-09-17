"""
نظام الإمداد والتموين - الواجهات المجردة للمستودعات
Base Repository Interface (Abstract) - contracts for all repositories
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """
    الواجهة المجردة الأساسية لجميع المستودعات.
    تحدد العقود (Contracts) التي يجب أن تنفذها كل طبقة بيانات.
    هذا يسمح بتبديل طبقة قاعدة البيانات (SQLite → MySQL → REST) دون تغيير منطق العمل.
    """

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """الحصول على كيان بواسطة معرفه."""
        ...

    @abstractmethod
    def list_all(
        self,
        camp_id: Optional[str] = None,
        include_deleted: bool = False,
        limit: int = 100,
        offset: int = 0,
        **filters,
    ) -> list[T]:
        """قائمة بجميع الكيانات مع إمكانية الترشيح."""
        ...

    @abstractmethod
    def create(self, entity: T) -> T:
        """إنشاء كيان جديد."""
        ...

    @abstractmethod
    def update(self, entity: T) -> T:
        """تحديث كيان موجود."""
        ...

    @abstractmethod
    def delete(self, entity_id: str, soft: bool = True) -> bool:
        """حذف كيان (حذف ناعم أو فعلي)."""
        ...

    @abstractmethod
    def count(self, camp_id: Optional[str] = None, **filters) -> int:
        """عدد الكيانات المطابقة للفلتر."""
        ...

    @abstractmethod
    def get_pending_sync(self, camp_id: Optional[str] = None, limit: int = 50) -> list[T]:
        """الحصول على السجلات المعلقة للمزامنة."""
        ...

    @abstractmethod
    def mark_synced(self, entity_id: str) -> bool:
        """تحديث حالة المزامنة إلى Synced."""
        ...

    @abstractmethod
    def mark_failed(self, entity_id: str, error: Optional[str] = None) -> bool:
        """تحديث حالة المزامنة إلى Failed."""
        ...