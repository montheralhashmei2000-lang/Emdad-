"""
نظام الإمداد والتموين - مصنع المستودعات
Repository Factory - creates and returns repository instances
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from data.database import get_session
from data.orm_models import (
    CampModel, UserModel, ItemCategoryModel, UnitOfMeasureModel,
    ItemModel, ItemUnitModel, SupplierModel, WarehouseModel,
    TransactionModel, TransactionItemModel, CustodyModel, CustodyItemModel,
    CustodyReturnModel, CustodyReturnItemModel, StocktakeModel, StocktakeItemModel,
    StockBalanceModel, ItemPriceModel, AuditLogModel, SyncLogModel, SyncOutboxModel,
)
from core.models.item import Item, ItemCategory, UnitOfMeasure, ItemUnit, ItemPrice
from core.models.warehouse import Camp, Warehouse, StockBalance
from core.models.transaction import Transaction, TransactionItem, Supplier
from core.models.custody import Custody, CustodyItem, CustodyReturn, CustodyReturnItem
from core.models.stocktake import Stocktake, StocktakeItem
from core.models.audit import AuditLog
from core.models.sync import User, SyncLog, SyncOutbox
from data.repositories_impl.base_sqlite_repository import BaseSQLiteRepository


class RepositoryFactory:
    """مصنع يوفر كل المستودعات بجلسة قاعدة بيانات محددة."""

    def __init__(self, session: Session | None = None):
        self._session = session or get_session()

    @property
    def session(self) -> Session:
        return self._session

    def close(self) -> None:
        """إغلاق الجلسة."""
        self._session.close()

    def commit(self) -> None:
        """حفظ التغييرات."""
        self._session.commit()

    def rollback(self) -> None:
        """التراجع عن التغييرات."""
        self._session.rollback()

    # --- مستودعات الجداول الأساسية ---
    @property
    def camps(self) -> BaseSQLiteRepository[Camp]:
        return BaseSQLiteRepository(self._session, CampModel, Camp, "camps")

    @property
    def users(self) -> BaseSQLiteRepository[User]:
        return BaseSQLiteRepository(self._session, UserModel, User, "users")

    @property
    def categories(self) -> BaseSQLiteRepository[ItemCategory]:
        return BaseSQLiteRepository(self._session, ItemCategoryModel, ItemCategory, "item_categories")

    @property
    def units_of_measure(self) -> BaseSQLiteRepository[UnitOfMeasure]:
        return BaseSQLiteRepository(self._session, UnitOfMeasureModel, UnitOfMeasure, "units_of_measure")

    @property
    def items(self) -> BaseSQLiteRepository[Item]:
        return BaseSQLiteRepository(self._session, ItemModel, Item, "items")

    @property
    def item_units(self) -> BaseSQLiteRepository[ItemUnit]:
        return BaseSQLiteRepository(self._session, ItemUnitModel, ItemUnit, "item_units")

    @property
    def suppliers(self) -> BaseSQLiteRepository[Supplier]:
        return BaseSQLiteRepository(self._session, SupplierModel, Supplier, "suppliers")

    @property
    def warehouses(self) -> BaseSQLiteRepository[Warehouse]:
        return BaseSQLiteRepository(self._session, WarehouseModel, Warehouse, "warehouses")

    @property
    def item_prices(self) -> BaseSQLiteRepository[ItemPrice]:
        return BaseSQLiteRepository(self._session, ItemPriceModel, ItemPrice, "item_prices")

    # --- مستودعات المعاملات ---
    @property
    def transactions(self) -> BaseSQLiteRepository[Transaction]:
        return BaseSQLiteRepository(self._session, TransactionModel, Transaction, "transactions")

    @property
    def transaction_items(self) -> BaseSQLiteRepository[TransactionItem]:
        return BaseSQLiteRepository(self._session, TransactionItemModel, TransactionItem, "transaction_items")

    # --- مستودعات العهد ---
    @property
    def custodies(self) -> BaseSQLiteRepository[Custody]:
        return BaseSQLiteRepository(self._session, CustodyModel, Custody, "custodies")

    @property
    def custody_items(self) -> BaseSQLiteRepository[CustodyItem]:
        return BaseSQLiteRepository(self._session, CustodyItemModel, CustodyItem, "custody_items")

    @property
    def custody_returns(self) -> BaseSQLiteRepository[CustodyReturn]:
        return BaseSQLiteRepository(self._session, CustodyReturnModel, CustodyReturn, "custody_returns")

    @property
    def custody_return_items(self) -> BaseSQLiteRepository[CustodyReturnItem]:
        return BaseSQLiteRepository(self._session, CustodyReturnItemModel, CustodyReturnItem, "custody_return_items")

    # --- مستودعات الجرد ---
    @property
    def stocktakes(self) -> BaseSQLiteRepository[Stocktake]:
        return BaseSQLiteRepository(self._session, StocktakeModel, Stocktake, "stocktakes")

    @property
    def stocktake_items(self) -> BaseSQLiteRepository[StocktakeItem]:
        return BaseSQLiteRepository(self._session, StocktakeItemModel, StocktakeItem, "stocktake_items")

    # --- مستودع الأرصدة ---
    @property
    def stock_balances(self) -> BaseSQLiteRepository[StockBalance]:
        return BaseSQLiteRepository(self._session, StockBalanceModel, StockBalance, "stock_balances")

    # --- مستودع التدقيق والمزامنة ---
    @property
    def audit_logs(self) -> BaseSQLiteRepository[AuditLog]:
        return BaseSQLiteRepository(self._session, AuditLogModel, AuditLog, "audit_logs")

    @property
    def sync_logs(self) -> BaseSQLiteRepository[SyncLog]:
        return BaseSQLiteRepository(self._session, SyncLogModel, SyncLog, "sync_logs")

    @property
    def sync_outbox(self) -> BaseSQLiteRepository[SyncOutbox]:
        return BaseSQLiteRepository(self._session, SyncOutboxModel, SyncOutbox, "sync_outbox")