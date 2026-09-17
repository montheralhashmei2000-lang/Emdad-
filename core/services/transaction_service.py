"""
نظام الإمداد والتموين - خدمة المعاملات المخزنية
Transaction Service - create, post, cancel inventory transactions
"""
from __future__ import annotations

from typing import Optional

from core.enums import TransactionType, TransactionStatus, SyncStatus
from core.models.base import utc_now
from core.models.transaction import Transaction, TransactionItem, Supplier
from core.services.inventory_service import InventoryService
from core.services.audit_service import AuditService
from data.repositories_impl.repository_factory import RepositoryFactory


class TransactionService:
    """خدمة إدارة المعاملات المخزنية (سندات الاستلام والصرف والتحويل والإتلاف)."""

    def __init__(self, repo_factory: RepositoryFactory):
        self.repo = repo_factory
        self.inventory = InventoryService(repo_factory)
        self.audit = AuditService(repo_factory)

    def _generate_transaction_no(self, transaction_type: str, camp_id: str) -> str:
        """توليد رقم سند فريد حسب النوع."""
        prefix_map = {
            TransactionType.RECEIVE.value: "RCP",
            TransactionType.ISSUE.value: "ISS",
            TransactionType.TRANSFER.value: "TRF",
            TransactionType.STOCKTAKE.value: "STK",
            TransactionType.WRITEOFF.value: "WRT",
            TransactionType.CUSTODY_ISSUE.value: "CIS",
            TransactionType.CUSTODY_RETURN.value: "CRT",
            TransactionType.RETURN.value: "RTN",
        }
        prefix = prefix_map.get(transaction_type, "TXN")

        # الحصول على آخر رقم تسلسلي
        from sqlalchemy import func
        from data.orm_models import TransactionModel

        last_no = (
            self.repo.session.query(func.max(TransactionModel.transaction_no))
            .filter(
                TransactionModel.transaction_type == transaction_type,
                TransactionModel.camp_id == camp_id,
            )
            .scalar()
        )

        if last_no and last_no.startswith(prefix):
            try:
                last_seq = int(last_no.split("-")[-1])
                new_seq = last_seq + 1
            except (ValueError, IndexError):
                new_seq = 1
        else:
            new_seq = 1

        return f"{prefix}-{camp_id[:8]}-{new_seq:05d}"

    def create_transaction(
        self,
        transaction_type: str,
        transaction_date: str,
        warehouse_from_id: Optional[str] = None,
        warehouse_to_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        recipient_name: Optional[str] = None,
        custody_id: Optional[str] = None,
        user_id: Optional[str] = None,
        notes: Optional[str] = None,
        return_reason: Optional[str] = None,
        items: Optional[list[dict]] = None,
        camp_id: str = "",
    ) -> Transaction:
        """إنشاء معاملة مخزنية جديدة مع بنودها."""
        if not camp_id:
            from app.config import settings
            camp_id = settings.camp_id or ""

        # التحقق من صحة المعاملة حسب النوع
        self._validate_transaction(
            transaction_type, warehouse_from_id, warehouse_to_id, items or []
        )

        txn_no = self._generate_transaction_no(transaction_type, camp_id)

        txn = Transaction(
            transaction_no=txn_no,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            warehouse_from_id=warehouse_from_id,
            warehouse_to_id=warehouse_to_id,
            supplier_id=supplier_id,
            recipient_name=recipient_name,
            custody_id=custody_id,
            user_id=user_id,
            status=TransactionStatus.POSTED.value,
            notes=notes,
            return_reason=return_reason,
            camp_id=camp_id,
        )

        # حفظ المعاملة
        created_txn = self.repo.transactions.create(txn)

        # إضافة البنود
        if items:
            for item_data in items:
                txn_item = TransactionItem(
                    transaction_id=created_txn.id,
                    item_id=item_data["item_id"],
                    uom_id=item_data["uom_id"],
                    quantity=item_data["quantity"],
                    unit_price=item_data.get("unit_price"),
                    notes=item_data.get("notes"),
                    camp_id=camp_id,
                )
                self.repo.transaction_items.create(txn_item)

                # تحديث الرصيد
                wh_id = warehouse_to_id or warehouse_from_id
                if wh_id:
                    self.inventory.recalculate_balance(
                        item_id=item_data["item_id"],
                        warehouse_id=wh_id,
                        uom_id=item_data["uom_id"],
                        camp_id=camp_id,
                    )

        self.repo.commit()

        # تسجيل التدقيق
        self.audit.log_create(
            entity_type="transactions",
            entity_id=created_txn.id,
            new_values={"transaction_no": txn_no, "type": transaction_type, "items_count": len(items or [])},
            user_id=user_id,
            camp_id=camp_id,
        )

        return self.repo.transactions.get_by_id(created_txn.id)

    def cancel_transaction(
        self,
        transaction_id: str,
        user_id: Optional[str] = None,
        camp_id: Optional[str] = None,
    ) -> Transaction:
        """إلغاء معاملة (تغيير الحالة إلى cancelled)."""
        txn = self.repo.transactions.get_by_id(transaction_id)
        if txn is None:
            raise ValueError(f"المعاملة {transaction_id} غير موجودة")
        if txn.status == TransactionStatus.CANCELLED.value:
            raise ValueError("المعاملة ملغاة بالفعل")

        # حفظ القيم القديمة للتدقيق
        old_values = txn.model_dump()

        # تحديث الحالة
        txn.status = TransactionStatus.CANCELLED.value
        txn.mark_updated()
        self.repo.transactions.update(txn)

        # إعادة حساب الأرصدة المتأثرة
        txn_items = self.repo.transaction_items.list_all(transaction_id=transaction_id)
        for item in txn_items:
            wh_id = txn.warehouse_to_id or txn.warehouse_from_id
            if wh_id:
                self.inventory.recalculate_balance(
                    item_id=item.item_id,
                    warehouse_id=wh_id,
                    uom_id=item.uom_id,
                    camp_id=camp_id,
                )

        self.repo.commit()

        # تسجيل التدقيق
        self.audit.log_update(
            entity_type="transactions",
            entity_id=transaction_id,
            old_values=old_values,
            new_values={"status": "cancelled"},
            user_id=user_id,
            camp_id=camp_id,
        )

        return self.repo.transactions.get_by_id(transaction_id)

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """الحصول على معاملة مع بنودها."""
        txn = self.repo.transactions.get_by_id(transaction_id)
        if txn is None:
            return None

        # إضافة البنود
        txn.items = self.repo.transaction_items.list_all(transaction_id=transaction_id)

        # إثراء بالأسماء
        self._enrich_transaction(txn)
        return txn

    def list_transactions(
        self,
        transaction_type: Optional[str] = None,
        camp_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> list[Transaction]:
        """قائمة المعاملات مع إمكانية الترشيح."""
        txns = self.repo.transactions.list_all(
            camp_id=camp_id,
            limit=limit,
            offset=offset,
            transaction_type=transaction_type,
            status=status,
        )
        for txn in txns:
            self._enrich_transaction(txn)
        return txns

    def _enrich_transaction(self, txn: Transaction) -> None:
        """إثراء المعاملة بأسماء الكيانات المرتبطة."""
        if txn.warehouse_from_id:
            wh = self.repo.warehouses.get_by_id(txn.warehouse_from_id)
            txn.warehouse_from_name = wh.name if wh else None
        if txn.warehouse_to_id:
            wh = self.repo.warehouses.get_by_id(txn.warehouse_to_id)
            txn.warehouse_to_name = wh.name if wh else None
        if txn.supplier_id:
            sup = self.repo.suppliers.get_by_id(txn.supplier_id)
            txn.supplier_name = sup.name if sup else None
        if txn.user_id:
            usr = self.repo.users.get_by_id(txn.user_id)
            txn.user_name = usr.full_name if usr else None

        # إثراء بنود المعاملة
        if txn.items:
            txn.item_count = len(txn.items)
            txn.total_qty = sum(item.quantity for item in txn.items)
            for item in txn.items:
                itm = self.repo.items.get_by_id(item.item_id)
                if itm:
                    item.item_name = itm.name
                    item.item_code = itm.code
                uom = self.repo.units_of_measure.get_by_id(item.uom_id)
                if uom:
                    item.uom_name = uom.name

    @staticmethod
    def _validate_transaction(
        txn_type: str,
        warehouse_from: Optional[str],
        warehouse_to: Optional[str],
        items: list[dict],
    ) -> None:
        """التحقق من صحة المعاملة حسب النوع."""
        if not items:
            raise ValueError("يجب إضافة بند واحد على الأقل للمعاملة")

        if txn_type in (TransactionType.RECEIVE.value, TransactionType.CUSTODY_RETURN.value, TransactionType.RETURN.value):
            if not warehouse_to:
                raise ValueError("يجب تحديد المخزن الوجهة للاستلام")

        if txn_type in (TransactionType.ISSUE.value, TransactionType.WRITEOFF.value, TransactionType.CUSTODY_ISSUE.value):
            if not warehouse_from:
                raise ValueError("يجب تحديد المخزن المصدر للصرف")

        if txn_type == TransactionType.TRANSFER.value:
            if not warehouse_from or not warehouse_to:
                raise ValueError("يجب تحديد المخزن المصدر والوجهة للتحويل")
            if warehouse_from == warehouse_to:
                raise ValueError("المخزن المصدر والوجهة لا يمكن أن يكونا نفس المخزن")
