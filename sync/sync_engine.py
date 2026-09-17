"""
نظام الإمداد والتموين - محرك المزامنة
Sync Engine - coordinates push/pull sync operations with conflict resolution
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from core.enums import SyncStatus, SyncLogStatus
from core.models.sync import SyncLog, SyncOutbox
from data.database import get_session
from data.repositories_impl.repository_factory import RepositoryFactory
from sync.api_client import ApiClient
from sync.network_monitor import NetworkMonitor


class SyncEngine:
    """
    محرك المزامنة (Offline-First).
    يقوم بـ:
    1. Push: رفع السجلات المعلقة (pending) إلى الخادم المركزي
    2. Pull: سحب التحديثات من الخادم المركزي
    3. حل التعارضات (Conflict Resolution) باستخدام LWW
    4. تسجيل سجل المزامنة
    """

    def __init__(self, repo_factory: Optional[RepositoryFactory] = None):
        self.repo = repo_factory or RepositoryFactory()
        self._api_client: Optional[ApiClient] = None
        self._lock = threading.Lock()
        self._is_syncing = False

    @property
    def api_client(self) -> ApiClient:
        if self._api_client is None:
            self._api_client = ApiClient()
        return self._api_client

    @property
    def is_syncing(self) -> bool:
        return self._is_syncing

    # ==================== المزامنة الكاملة ====================

    def sync_all(self) -> SyncLog:
        """
        تشغيل مزامنة كاملة (Push + Pull).
        """
        with self._lock:
            if self._is_syncing:
                raise RuntimeError("المزامنة قيد التشغيل بالفعل")
            self._is_syncing = True

        sync_log = self._create_sync_log("both")

        try:
            # 1. Push السجلات المعلقة
            push_result = self._push_all()

            # 2. Pull التحديثات من الخادم
            pull_result = self._pull_all()

            # 3. تحديث سجل المزامنة
            sync_log.records_pushed = push_result
            sync_log.records_pulled = pull_result
            sync_log.status = SyncLogStatus.SUCCESS.value
            sync_log.finished_at = datetime.now(timezone.utc).isoformat()
            self.repo.sync_logs.update(sync_log)
            self.repo.commit()

        except Exception as e:
            sync_log.status = SyncLogStatus.FAILED.value
            sync_log.error_message = str(e)
            sync_log.finished_at = datetime.now(timezone.utc).isoformat()
            self.repo.sync_logs.update(sync_log)
            self.repo.commit()
            raise

        finally:
            self._is_syncing = False

        return self.repo.sync_logs.get_by_id(sync_log.id)

    # ==================== Push ====================

    def _push_all(self) -> int:
        """
        رفع جميع السجلات المعلقة (pending) إلى الخادم المركزي.
        """
        if not self.api_client.ping():
            raise ConnectionError("لا يمكن الاتصال بالخادم المركزي")

        # الحصول على سجلات المزامنة المعلقة
        pending_outbox = self.repo.sync_outbox.list_all(
            status="pending",
            limit=200,
        )

        if not pending_outbox:
            return 0

        # تحويل إلى قائمة JSON
        records = []
        for outbox in pending_outbox:
            try:
                payload = json.loads(outbox.payload_json)
                records.append({
                    "id": outbox.entity_id,
                    "entity_type": outbox.entity_type,
                    "operation": outbox.operation,
                    "data": payload,
                    "camp_id": outbox.camp_id,
                })
            except json.JSONDecodeError:
                continue

        # رفع إلى الخادم
        result = self.api_client.push_records(records)

        synced_ids = result.get("synced_ids", [])
        failed_ids = result.get("failed_ids", {})

        # تحديث حالة السجلات الناجحة
        for sid in synced_ids:
            self.repo.sync_outbox.mark_synced(sid)
            # تحديث حالة المزامنة للكيان الأصلي
            outbox = self.repo.sync_outbox.get_by_id(sid)
            if outbox:
                self._mark_entity_synced(outbox.entity_type, outbox.entity_id)

        # تحديث حالة السجلات الفاشلة
        for fid, error in failed_ids.items():
            self.repo.sync_outbox.mark_failed(fid, error)
            # تسجيل الخطأ
            outbox = self.repo.sync_outbox.get_by_id(fid)
            if outbox:
                self._mark_entity_failed(outbox.entity_type, outbox.entity_id, error)

        self.repo.commit()
        return len(synced_ids)

    # ==================== Pull ====================

    def _pull_all(self) -> int:
        """
        سحب التحديثات من الخادم المركزي.
        """
        if not self.api_client.ping():
            raise ConnectionError("لا يمكن الاتصال بالخادم المركزي")

        # الحصول على آخر مزامعة ناجحة
        last_sync = self.repo.sync_logs.list_all(
            status=SyncLogStatus.SUCCESS.value,
            limit=1,
        )
        since = last_sync[0].started_at if last_sync else None

        # سحب السجلات
        records = self.api_client.pull_records(since)
        if not records:
            return 0

        # معالجة كل سجل
        count = 0
        for record in records:
            try:
                self._apply_remote_record(record)
                count += 1
            except Exception as e:
                print(f"[Sync] فشل تطبيق سجل من الخادم: {e}")

        self.repo.commit()
        return count

    # ==================== تطبيق السجلات البعيدة ====================

    def _apply_remote_record(self, record: dict) -> None:
        """
        تطبيق سجل ورد من الخادم المركزي على قاعدة البيانات المحلية.
        """
        entity_type = record.get("entity_type", "")
        entity_id = record.get("id", "")
        operation = record.get("operation", "upsert")
        data = record.get("data", {})

        if operation == "delete":
            self._delete_entity(entity_type, entity_id)
            return

        # البحث عن السجل محلياً
        local_entity = self._get_entity(entity_type, entity_id)

        if local_entity is None:
            # إنشاء جديد
            self._create_entity(entity_type, data)
        else:
            # حل التعارض: Last-Write-Wins (LWW)
            remote_updated = data.get("updated_at", "")
            local_updated = getattr(local_entity, "updated_at", "")

            if remote_updated >= local_updated:
                self._update_entity(entity_type, data)

    # ==================== دوال مساعدة للكيانات ====================

    def _get_entity(self, entity_type: str, entity_id: str):
        """الحصول على كيان حسب نوعه."""
        repo_map = {
            "camps": self.repo.camps,
            "users": self.repo.users,
            "items": self.repo.items,
            "item_categories": self.repo.categories,
            "units_of_measure": self.repo.units_of_measure,
            "item_units": self.repo.item_units,
            "suppliers": self.repo.suppliers,
            "warehouses": self.repo.warehouses,
            "transactions": self.repo.transactions,
            "transaction_items": self.repo.transaction_items,
            "custodies": self.repo.custodies,
            "custody_items": self.repo.custody_items,
            "custody_returns": self.repo.custody_returns,
            "custody_return_items": self.repo.custody_return_items,
            "stocktakes": self.repo.stocktakes,
            "stocktake_items": self.repo.stocktake_items,
            "stock_balances": self.repo.stock_balances,
        }
        repo = repo_map.get(entity_type)
        if repo:
            return repo.get_by_id(entity_id)
        return None

    def _create_entity(self, entity_type: str, data: dict) -> None:
        """إنشاء كيان جديد من بيانات الخادم."""
        from core.models.base import BaseSchema

        # حقول المزامنة
        data["sync_status"] = SyncStatus.SYNCED.value
        if "id" not in data:
            data["id"] = str(uuid.uuid4())

        # إنشاء النموذج المناسب
        model_map = {
            "camps": "Camp",
            "users": "User",
            "items": "Item",
            "item_categories": "ItemCategory",
            "units_of_measure": "UnitOfMeasure",
            "item_units": "ItemUnit",
            "suppliers": "Supplier",
            "warehouses": "Warehouse",
            "transactions": "Transaction",
            "transaction_items": "TransactionItem",
            "custodies": "Custody",
            "custody_items": "CustodyItem",
            "custody_returns": "CustodyReturn",
            "custody_return_items": "CustodyReturnItem",
            "stocktakes": "Stocktake",
            "stocktake_items": "StocktakeItem",
        }

        model_name = model_map.get(entity_type)
        if model_name is None:
            return

        # استيراد النموذج وتطبيقه
        import importlib
        try:
            module = importlib.import_module("core.models")
            model_class = getattr(module, model_name, None)
            if model_class:
                # إنشاء النموذج
                entity = model_class(**data)
                self._save_entity(entity_type, entity)
        except (ImportError, AttributeError, Exception) as e:
            print(f"[Sync] فشل إنشاء {entity_type}: {e}")

    def _update_entity(self, entity_type: str, data: dict) -> None:
        """تحديث كيان موجود من بيانات الخادم."""
        data["sync_status"] = SyncStatus.SYNCED.value
        data.pop("id", None)

        # تحديث عبر الـ repo
        try:
            entity = self._get_entity(entity_type, data.get("id", ""))
            if entity:
                for key, value in data.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)
                self._save_entity(entity_type, entity)
        except Exception as e:
            print(f"[Sync] فشل تحديث {entity_type}: {e}")

    def _delete_entity(self, entity_type: str, entity_id: str) -> None:
        """حذف كيان (soft delete)."""
        repo_map = {
            "camps": self.repo.camps,
            "users": self.repo.users,
            "items": self.repo.items,
            "item_categories": self.repo.categories,
            "units_of_measure": self.repo.units_of_measure,
            "item_units": self.repo.item_units,
            "suppliers": self.repo.suppliers,
            "warehouses": self.repo.warehouses,
            "transactions": self.repo.transactions,
            "transaction_items": self.repo.transaction_items,
            "custodies": self.repo.custodies,
            "custody_items": self.repo.custody_items,
            "custody_returns": self.repo.custody_returns,
            "custody_return_items": self.repo.custody_return_items,
            "stocktakes": self.repo.stocktakes,
            "stocktake_items": self.repo.stocktake_items,
        }
        repo = repo_map.get(entity_type)
        if repo:
            repo.delete(entity_id, soft=True)

    def _save_entity(self, entity_type: str, entity) -> None:
        """حفظ كيان (إنشاء أو تحديث) باستخدام المستودع المناسب."""
        repo_map = {
            "camps": self.repo.camps,
            "users": self.repo.users,
            "items": self.repo.items,
            "item_categories": self.repo.categories,
            "units_of_measure": self.repo.units_of_measure,
            "item_units": self.repo.item_units,
            "suppliers": self.repo.suppliers,
            "warehouses": self.repo.warehouses,
            "transactions": self.repo.transactions,
            "transaction_items": self.repo.transaction_items,
            "custodies": self.repo.custodies,
            "custody_items": self.repo.custody_items,
            "custody_returns": self.repo.custody_returns,
            "custody_return_items": self.repo.custody_return_items,
            "stocktakes": self.repo.stocktakes,
            "stocktake_items": self.repo.stocktake_items,
        }
        repo = repo_map.get(entity_type)
        if repo:
            existing = repo.get_by_id(entity.id)
            if existing:
                repo.update(entity)
            else:
                repo.create(entity)

    # ==================== دوال مساعدة ====================

    def _create_sync_log(self, sync_type: str) -> SyncLog:
        """إنشاء سجل مزامنة جديد."""
        sync_log = SyncLog(
            sync_type=sync_type,
            status=SyncLogStatus.IN_PROGRESS.value,
            server_url=settings.server_url,
            camp_id=settings.camp_id,
        )
        return self.repo.sync_logs.create(sync_log)

    def _mark_entity_synced(self, entity_type: str, entity_id: str) -> None:
        """تحديث حالة الكيان الأصلي إلى Synced."""
        repo_map = {
            "camps": self.repo.camps,
            "users": self.repo.users,
            "items": self.repo.items,
            "item_categories": self.repo.categories,
            "units_of_measure": self.repo.units_of_measure,
            "item_units": self.repo.item_units,
            "suppliers": self.repo.suppliers,
            "warehouses": self.repo.warehouses,
            "transactions": self.repo.transactions,
            "transaction_items": self.repo.transaction_items,
            "custodies": self.repo.custodies,
            "custody_items": self.repo.custody_items,
            "custody_returns": self.repo.custody_returns,
            "custody_return_items": self.repo.custody_return_items,
            "stocktakes": self.repo.stocktakes,
            "stocktake_items": self.repo.stocktake_items,
        }
        repo = repo_map.get(entity_type)
        if repo:
            repo.mark_synced(entity_id)

    def _mark_entity_failed(self, entity_type: str, entity_id: str, error: str) -> None:
        """تحديث حالة الكيان الأصلي إلى Failed."""
        repo_map = {
            "camps": self.repo.camps,
            "users": self.repo.users,
            "items": self.repo.items,
            "item_categories": self.repo.categories,
            "units_of_measure": self.repo.units_of_measure,
            "item_units": self.repo.item_units,
            "suppliers": self.repo.suppliers,
            "warehouses": self.repo.warehouses,
            "transactions": self.repo.transactions,
            "transaction_items": self.repo.transaction_items,
            "custodies": self.repo.custodies,
            "custody_items": self.repo.custody_items,
            "custody_returns": self.repo.custody_returns,
            "custody_return_items": self.repo.custody_return_items,
            "stocktakes": self.repo.stocktakes,
            "stocktake_items": self.repo.stocktake_items,
        }
        repo = repo_map.get(entity_type)
        if repo:
            repo.mark_failed(entity_id, error)

    def get_sync_logs(self, limit: int = 20) -> list[SyncLog]:
        """الحصول على أحدث سجلات المزامنة."""
        return self.repo.sync_logs.list_all(limit=limit)

    def get_pending_count(self) -> int:
        """عدد السجلات المعلقة للمزامنة."""
        return self.repo.sync_outbox.count(status="pending")

    def close(self) -> None:
        """إغلاق المحرك."""
        if self._api_client:
            self._api_client.close()
        self.repo.close()