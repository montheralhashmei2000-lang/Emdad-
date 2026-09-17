"""
نظام الإمداد والتموين - خدمة إدارة المخزون
Inventory Service - calculates stock balances from transaction history (Event Sourcing)
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from core.enums import TransactionType, SyncStatus
from core.models.warehouse import StockBalance
from data.orm_models import (
    TransactionModel, TransactionItemModel, StockBalanceModel,
    ItemModel, WarehouseModel,
)
from data.repositories_impl.repository_factory import RepositoryFactory


class InventoryService:
    """
    خدمة إدارة المخزون.
    المبدأ الأساسي: الأرصدة تُحسَب من سجل الحركات (Event Sourcing).
    كل عملية معتمدة تُحدِث رصيد المخزون.
    """

    def __init__(self, repo_factory: RepositoryFactory):
        self.repo = repo_factory
        self.session = repo_factory.session

    def recalculate_balance(
        self,
        item_id: str,
        warehouse_id: str,
        uom_id: str,
        camp_id: Optional[str] = None,
    ) -> StockBalance:
        """
        إعادة حساب رصيد صنف في مخزن معين من جميع الحركات.
        يُستخدم عند:
        - إضافة معاملة جديدة
        - تعديل أو إلغاء معاملة
        - المزامنة من الخادم المركزي
        """
        from sqlalchemy import func

        # صافي كميات الاستلام
        receive_qty = (
            self.session.query(func.coalesce(func.sum(TransactionItemModel.quantity), 0))
            .join(TransactionModel)
            .filter(
                TransactionItemModel.item_id == item_id,
                TransactionItemModel.uom_id == uom_id,
                TransactionModel.warehouse_to_id == warehouse_id,
                TransactionModel.status == "posted",
                TransactionModel.is_deleted == 0,
                TransactionModel.transaction_type == TransactionType.RECEIVE.value,
            )
            .scalar()
            or 0.0
        )

        # صافي كميات الصرف (تطرح)
        issue_qty = (
            self.session.query(func.coalesce(func.sum(TransactionItemModel.quantity), 0))
            .join(TransactionModel)
            .filter(
                TransactionItemModel.item_id == item_id,
                TransactionItemModel.uom_id == uom_id,
                TransactionModel.warehouse_from_id == warehouse_id,
                TransactionModel.status == "posted",
                TransactionModel.is_deleted == 0,
                TransactionModel.transaction_type.in_([
                    TransactionType.ISSUE.value,
                    TransactionType.WRITEOFF.value,
                    TransactionType.CUSTODY_ISSUE.value,
                ]),
            )
            .scalar()
            or 0.0
        )

        # صافي كميات التحويل الخارج (من هذا المخزن)
        transfer_out_qty = (
            self.session.query(func.coalesce(func.sum(TransactionItemModel.quantity), 0))
            .join(TransactionModel)
            .filter(
                TransactionItemModel.item_id == item_id,
                TransactionItemModel.uom_id == uom_id,
                TransactionModel.warehouse_from_id == warehouse_id,
                TransactionModel.status == "posted",
                TransactionModel.is_deleted == 0,
                TransactionModel.transaction_type == TransactionType.TRANSFER.value,
            )
            .scalar()
            or 0.0
        )

        # صافي كميات التحويل الداخل (إلى هذا المخزن)
        transfer_in_qty = (
            self.session.query(func.coalesce(func.sum(TransactionItemModel.quantity), 0))
            .join(TransactionModel)
            .filter(
                TransactionItemModel.item_id == item_id,
                TransactionItemModel.uom_id == uom_id,
                TransactionModel.warehouse_to_id == warehouse_id,
                TransactionModel.status == "posted",
                TransactionModel.is_deleted == 0,
                TransactionModel.transaction_type == TransactionType.TRANSFER.value,
            )
            .scalar()
            or 0.0
        )

        # صافي كميات استرجاع العهد (ترجع للمخزن)
        custody_return_qty = (
            self.session.query(func.coalesce(func.sum(TransactionItemModel.quantity), 0))
            .join(TransactionModel)
            .filter(
                TransactionItemModel.item_id == item_id,
                TransactionItemModel.uom_id == uom_id,
                TransactionModel.warehouse_to_id == warehouse_id,
                TransactionModel.status == "posted",
                TransactionModel.is_deleted == 0,
                TransactionModel.transaction_type == TransactionType.CUSTODY_RETURN.value,
            )
            .scalar()
            or 0.0
        )

        # الرصيد = الوارد - الصادر + التحويلات الداخلة - التحويلات الخارجة + استرجاع العهد
        net_quantity = (
            receive_qty
            - issue_qty
            + transfer_in_qty
            - transfer_out_qty
            + custody_return_qty
        )

        # حفظ أو تحديث الرصيد
        existing = self.session.query(StockBalanceModel).filter(
            StockBalanceModel.item_id == item_id,
            StockBalanceModel.warehouse_id == warehouse_id,
            StockBalanceModel.uom_id == uom_id,
        ).first()

        now = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat()

        if existing:
            existing.quantity = net_quantity
            existing.last_movement_at = now
            existing.updated_at = now
            existing.sync_status = SyncStatus.PENDING.value
        else:
            import uuid
            balance = StockBalanceModel(
                id=str(uuid.uuid4()),
                item_id=item_id,
                warehouse_id=warehouse_id,
                uom_id=uom_id,
                quantity=net_quantity,
                last_movement_at=now,
                camp_id=camp_id,
                created_at=now,
                updated_at=now,
                sync_status=SyncStatus.PENDING.value,
            )
            self.session.add(balance)

        self.session.flush()

        # إعادة القراءة
        return self.repo.stock_balances.get_by_id(
            existing.id if existing else balance.id
        )

    def recalculate_all_balances(self, camp_id: Optional[str] = None) -> int:
        """
        إعادة حساب جميع الأرصدة في النظام.
        تُستخدم عند التهيئة أو بعد المزامنة الكبيرة.
        """
        from sqlalchemy import distinct

        # الحصول على جميع مجموعات (صنف, مخزن, وحدة قياس) الفريدة من الحركات
        query = (
            self.session.query(
                distinct(TransactionItemModel.item_id).label("item_id"),
                TransactionModel.warehouse_from_id.label("warehouse_id"),
                TransactionItemModel.uom_id,
            )
            .join(TransactionModel)
            .filter(TransactionModel.status == "posted", TransactionModel.is_deleted == 0)
        )

        if camp_id:
            query = query.filter(TransactionModel.camp_id == camp_id)

        # دمج مع المخازن الوجهة
        query_to = (
            self.session.query(
                distinct(TransactionItemModel.item_id).label("item_id"),
                TransactionModel.warehouse_to_id.label("warehouse_id"),
                TransactionItemModel.uom_id,
            )
            .join(TransactionModel)
            .filter(TransactionModel.status == "posted", TransactionModel.is_deleted == 0)
        )

        if camp_id:
            query_to = query_to.filter(TransactionModel.camp_id == camp_id)

        # دمج المجموعات
        all_combos = set()
        for row in query.all():
            if row.warehouse_id:
                all_combos.add((row.item_id, row.warehouse_id, row.uom_id))
        for row in query_to.all():
            if row.warehouse_id:
                all_combos.add((row.item_id, row.warehouse_id, row.uom_id))

        count = 0
        for item_id, warehouse_id, uom_id in all_combos:
            try:
                self.recalculate_balance(item_id, warehouse_id, uom_id, camp_id)
                count += 1
            except Exception:
                pass

        self.session.commit()
        return count

    def get_stock_balance(
        self,
        item_id: str,
        warehouse_id: str,
        uom_id: str,
    ) -> StockBalance:
        """الحصول على رصيد صنف في مخزن معين."""
        balance = self.repo.stock_balances.list_all(
            item_id=item_id,
            warehouse_id=warehouse_id,
            uom_id=uom_id,
            limit=1,
        )
        if balance:
            return balance[0]
        return StockBalance(
            item_id=item_id,
            warehouse_id=warehouse_id,
            uom_id=uom_id,
            quantity=0.0,
        )

    def get_warehouse_stock(
        self,
        warehouse_id: str,
        below_min_only: bool = False,
        camp_id: Optional[str] = None,
    ) -> list[StockBalance]:
        """الحصول على جميع أرصدة مخزن معين."""
        balances = self.repo.stock_balances.list_all(
            warehouse_id=warehouse_id,
            camp_id=camp_id,
            limit=1000,
        )

        # إثراء بأسماء الأصناف
        for bal in balances:
            item = self.repo.items.get_by_id(bal.item_id)
            if item:
                bal.item_name = item.name
                bal.item_code = item.code
                if item.min_stock_level > 0:
                    bal.is_below_min = bal.quantity < item.min_stock_level

        if below_min_only:
            balances = [b for b in balances if b.is_below_min]

        return balances

    def get_inventory_summary(self, camp_id: Optional[str] = None) -> list[dict]:
        """الحصول على ملخص المخزون شاملاً تفاصيل الأصناف والمخازن."""
        balances = self.repo.stock_balances.list_all(camp_id=camp_id, limit=1000)
        summary = []
        for bal in balances:
            item = self.repo.items.get_by_id(bal.item_id)
            warehouse = self.repo.warehouses.get_by_id(bal.warehouse_id)
            uom = self.repo.units_of_measure.get_by_id(bal.uom_id) if hasattr(self.repo, "units_of_measure") else None
            summary.append({
                "item_id": bal.item_id,
                "item_code": item.code if item else "",
                "item_name": item.name if item else "",
                "warehouse_id": bal.warehouse_id,
                "warehouse_name": warehouse.name if warehouse else "",
                "uom_name": uom.name if uom else "",
                "quantity": bal.quantity,
                "last_movement_at": bal.last_movement_at,
                "is_below_min": (bal.quantity < item.min_stock_level) if (item and item.min_stock_level > 0) else False,
            })
        return summary

    def get_items_below_min(self, camp_id: Optional[str] = None) -> list[StockBalance]:
        """الحصول على الأصناف التي وصلت للحد الأدنى."""
        items = self.repo.items.list_all(is_active=True, camp_id=camp_id, limit=1000)
        below_min = []

        for item in items:
            if item.min_stock_level <= 0:
                continue
            balances = self.repo.stock_balances.list_all(
                item_id=item.id,
                camp_id=camp_id,
                limit=100,
            )
            for bal in balances:
                if bal.quantity < item.min_stock_level:
                    bal.item_name = item.name
                    bal.item_code = item.code
                    bal.is_below_min = True
                    below_min.append(bal)

        return below_min