"""
نظام الإمداد والتموين - نماذج ORM لجداول قاعدة البيانات
SQLAlchemy ORM Models - تعكس جميع جداول قاعدة البيانات المحلية
"""
from __future__ import annotations

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, Text, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

from data.database import Base


class BaseMixin:
    """حقول مشتركة لجميع النماذج."""

    id = Column(String(36), primary_key=True)
    camp_id = Column(String(36), nullable=True, index=True)
    created_at = Column(String(27), nullable=False, index=True)  # ISO8601: 2024-01-01T00:00:00.000Z
    updated_at = Column(String(27), nullable=False)
    sync_status = Column(String(10), nullable=False, default="pending", index=True)
    is_deleted = Column(Integer, default=0)


# ==================== الجداول الأساسية ====================

class CampModel(Base, BaseMixin):
    __tablename__ = "camps"

    name = Column(String(200), nullable=False)
    code = Column(String(30), nullable=False, unique=True)
    location = Column(String(300), nullable=True)
    contact_phone = Column(String(30), nullable=True)
    is_active = Column(Integer, default=1)

    __table_args__ = (
        Index("idx_camps_sync", "camp_id", "updated_at"),
    )


class UserModel(Base, BaseMixin):
    __tablename__ = "users"

    username = Column(String(100), nullable=False, unique=True)
    full_name = Column(String(200), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")
    is_active = Column(Integer, default=1)

    __table_args__ = (
        Index("idx_users_sync", "camp_id", "updated_at"),
    )


class ItemCategoryModel(Base, BaseMixin):
    __tablename__ = "item_categories"

    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=True)
    parent_id = Column(String(36), ForeignKey("item_categories.id"), nullable=True)
    description = Column(String(500), nullable=True)

    # العلاقة الهرمية
    parent = relationship("ItemCategoryModel", remote_side="ItemCategoryModel.id", backref="children")

    __table_args__ = (
        Index("idx_categories_sync", "camp_id", "updated_at"),
    )


class UnitOfMeasureModel(Base, BaseMixin):
    __tablename__ = "units_of_measure"

    name = Column(String(100), nullable=False)
    abbreviation = Column(String(20), nullable=False)
    is_base_unit = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_uom_sync", "camp_id", "updated_at"),
    )


class ItemModel(Base, BaseMixin):
    __tablename__ = "items"

    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(300), nullable=False)
    description = Column(String(1000), nullable=True)
    category_id = Column(String(36), ForeignKey("item_categories.id"), nullable=True)
    base_uom_id = Column(String(36), ForeignKey("units_of_measure.id"), nullable=False)
    is_consumable = Column(Integer, default=1)
    is_refillable = Column(Integer, default=0)
    is_serialized = Column(Integer, default=0)
    requires_dangerous_goods = Column(Integer, default=0)
    min_stock_level = Column(Float, default=0)
    max_stock_level = Column(Float, nullable=True)
    is_active = Column(Integer, default=1)

    # العلاقات
    category = relationship("ItemCategoryModel", backref="items")
    base_uom = relationship("UnitOfMeasureModel", backref="items")
    units = relationship("ItemUnitModel", backref="item", lazy="selectin")

    __table_args__ = (
        Index("idx_items_sync", "camp_id", "updated_at"),
        Index("idx_items_code", "code"),
    )


class ItemUnitModel(Base, BaseMixin):
    __tablename__ = "item_units"

    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    uom_id = Column(String(36), ForeignKey("units_of_measure.id"), nullable=False)
    conversion_factor = Column(Float, default=1.0)
    is_default_purchase = Column(Integer, default=0)
    is_default_issue = Column(Integer, default=0)

    # العلاقات
    uom = relationship("UnitOfMeasureModel", backref="item_units")

    __table_args__ = (
        UniqueConstraint("item_id", "uom_id", name="uq_item_uom"),
        Index("idx_item_units_sync", "camp_id", "updated_at"),
    )


class SupplierModel(Base, BaseMixin):
    __tablename__ = "suppliers"

    name = Column(String(200), nullable=False)
    code = Column(String(50), nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(String(500), nullable=True)
    tax_number = Column(String(50), nullable=True)
    contact_person = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1)

    __table_args__ = (
        Index("idx_suppliers_sync", "camp_id", "updated_at"),
    )


class WarehouseModel(Base, BaseMixin):
    __tablename__ = "warehouses"

    camp_id = Column(String(36), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(30), nullable=False)
    type = Column(String(10), default="main")
    location = Column(String(300), nullable=True)
    is_active = Column(Integer, default=1)

    __table_args__ = (
        Index("idx_warehouses_sync", "camp_id", "updated_at"),
    )


class ItemPriceModel(Base, BaseMixin):
    __tablename__ = "item_prices"

    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    price_type = Column(String(10), nullable=False)
    price = Column(Float, nullable=False)
    effective_date = Column(String(27), nullable=False)

    __table_args__ = (
        Index("idx_item_prices_sync", "camp_id", "updated_at"),
    )


# ==================== جداول المعاملات المخزنية ====================

class TransactionModel(Base, BaseMixin):
    __tablename__ = "transactions"

    transaction_no = Column(String(50), nullable=False)
    transaction_type = Column(String(20), nullable=False)
    transaction_date = Column(String(27), nullable=False)
    warehouse_from_id = Column(String(36), ForeignKey("warehouses.id"), nullable=True)
    warehouse_to_id = Column(String(36), ForeignKey("warehouses.id"), nullable=True)
    supplier_id = Column(String(36), ForeignKey("suppliers.id"), nullable=True)
    recipient_name = Column(String(200), nullable=True)
    custody_id = Column(String(36), ForeignKey("custodies.id"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(10), default="posted")
    notes = Column(String(1000), nullable=True)
    return_reason = Column(String(500), nullable=True)

    # العلاقات
    items = relationship("TransactionItemModel", backref="transaction", lazy="selectin",
                         cascade="all, delete-orphan")
    warehouse_from = relationship("WarehouseModel", foreign_keys=[warehouse_from_id])
    warehouse_to = relationship("WarehouseModel", foreign_keys=[warehouse_to_id])
    supplier = relationship("SupplierModel")
    user = relationship("UserModel")

    __table_args__ = (
        Index("idx_transactions_type", "transaction_type", "camp_id"),
        Index("idx_transactions_date", "transaction_date"),
        Index("idx_transactions_status", "status"),
        Index("idx_transactions_sync", "camp_id", "updated_at"),
    )


class TransactionItemModel(Base, BaseMixin):
    __tablename__ = "transaction_items"

    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    uom_id = Column(String(36), ForeignKey("units_of_measure.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=True)
    notes = Column(String(500), nullable=True)

    # العلاقات
    item = relationship("ItemModel")
    uom = relationship("UnitOfMeasureModel")

    __table_args__ = (
        Index("idx_trans_items_sync", "camp_id", "updated_at"),
    )


# ==================== جداول العهد ====================

class CustodyModel(Base, BaseMixin):
    __tablename__ = "custodies"

    custody_no = Column(String(50), nullable=False)
    employee_name = Column(String(200), nullable=False)
    employee_rank = Column(String(100), nullable=True)
    unit_name = Column(String(200), nullable=True)
    department = Column(String(200), nullable=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False)
    issue_date = Column(String(27), nullable=False)
    expected_return_date = Column(String(27), nullable=True)
    status = Column(String(10), default="active")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    notes = Column(String(1000), nullable=True)

    # العلاقات
    items = relationship("CustodyItemModel", backref="custody", lazy="selectin",
                         cascade="all, delete-orphan")
    warehouse = relationship("WarehouseModel")
    user = relationship("UserModel")

    __table_args__ = (
        Index("idx_custodies_sync", "camp_id", "updated_at"),
    )


class CustodyItemModel(Base, BaseMixin):
    __tablename__ = "custody_items"

    custody_id = Column(String(36), ForeignKey("custodies.id"), nullable=False)
    transaction_item_id = Column(String(36), nullable=True)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    uom_id = Column(String(36), ForeignKey("units_of_measure.id"), nullable=False)
    issued_qty = Column(Float, nullable=False)
    returned_qty = Column(Float, default=0)
    current_qty = Column(Float, default=0)
    condition_issued = Column(String(200), nullable=True)

    # العلاقات
    item = relationship("ItemModel")
    uom = relationship("UnitOfMeasureModel")

    __table_args__ = (
        Index("idx_custody_items_sync", "camp_id", "updated_at"),
    )


class CustodyReturnModel(Base, BaseMixin):
    __tablename__ = "custody_returns"

    return_no = Column(String(50), nullable=False)
    custody_id = Column(String(36), ForeignKey("custodies.id"), nullable=False)
    return_date = Column(String(27), nullable=False)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    notes = Column(String(1000), nullable=True)

    # العلاقات
    items = relationship("CustodyReturnItemModel", backref="return_", lazy="selectin",
                         cascade="all, delete-orphan")
    custody = relationship("CustodyModel")
    warehouse = relationship("WarehouseModel")

    __table_args__ = (
        Index("idx_custody_returns_sync", "camp_id", "updated_at"),
    )


class CustodyReturnItemModel(Base, BaseMixin):
    __tablename__ = "custody_return_items"

    return_id = Column(String(36), ForeignKey("custody_returns.id"), nullable=False)
    custody_item_id = Column(String(36), ForeignKey("custody_items.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    uom_id = Column(String(36), ForeignKey("units_of_measure.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    condition = Column(String(10), default="good")
    damage_notes = Column(String(500), nullable=True)

    # العلاقات
    item = relationship("ItemModel")
    uom = relationship("UnitOfMeasureModel")
    custody_item = relationship("CustodyItemModel")

    __table_args__ = (
        Index("idx_custody_return_items_sync", "camp_id", "updated_at"),
    )


# ==================== جداول الجرد ====================

class StocktakeModel(Base, BaseMixin):
    __tablename__ = "stocktakes"

    stocktake_no = Column(String(50), nullable=False)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False)
    stocktake_date = Column(String(27), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(10), default="draft")
    notes = Column(String(1000), nullable=True)

    # العلاقات
    items = relationship("StocktakeItemModel", backref="stocktake", lazy="selectin",
                         cascade="all, delete-orphan")
    warehouse = relationship("WarehouseModel")

    __table_args__ = (
        Index("idx_stocktakes_sync", "camp_id", "updated_at"),
    )


class StocktakeItemModel(Base, BaseMixin):
    __tablename__ = "stocktake_items"

    stocktake_id = Column(String(36), ForeignKey("stocktakes.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    uom_id = Column(String(36), ForeignKey("units_of_measure.id"), nullable=False)
    system_qty = Column(Float, default=0)
    counted_qty = Column(Float, default=0)
    difference_qty = Column(Float, default=0)
    notes = Column(String(500), nullable=True)

    # العلاقات
    item = relationship("ItemModel")
    uom = relationship("UnitOfMeasureModel")

    __table_args__ = (
        Index("idx_stocktake_items_sync", "camp_id", "updated_at"),
    )


# ==================== جدول الأرصدة (مشتق) ====================

class StockBalanceModel(Base, BaseMixin):
    __tablename__ = "stock_balances"

    item_id = Column(String(36), ForeignKey("items.id"), nullable=False)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False)
    uom_id = Column(String(36), ForeignKey("units_of_measure.id"), nullable=False)
    quantity = Column(Float, default=0)
    last_movement_at = Column(String(27), nullable=True)

    # العلاقات
    item = relationship("ItemModel")
    warehouse = relationship("WarehouseModel")
    uom = relationship("UnitOfMeasureModel")

    __table_args__ = (
        UniqueConstraint("item_id", "warehouse_id", "uom_id", name="uq_stock_balance"),
        Index("idx_stock_balances_sync", "camp_id", "updated_at"),
        Index("idx_stock_balances_item", "item_id", "warehouse_id"),
    )


# ==================== سجل التدقيق والمزامنة ====================

class AuditLogModel(Base, BaseMixin):
    __tablename__ = "audit_logs"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    username = Column(String(200), nullable=True)
    action = Column(String(20), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=True)
    description = Column(String(500), nullable=True)
    old_values = Column(Text, nullable=True)
    new_values = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)

    __table_args__ = (
        Index("idx_audit_logs_action", "action", "entity_type"),
        Index("idx_audit_logs_created", "created_at"),
    )


class SyncLogModel(Base, BaseMixin):
    __tablename__ = "sync_logs"

    sync_type = Column(String(10), nullable=False)
    status = Column(String(15), nullable=False, default="in_progress")
    started_at = Column(String(27), nullable=False)
    finished_at = Column(String(27), nullable=True)
    records_pushed = Column(Integer, default=0)
    records_pulled = Column(Integer, default=0)
    error_message = Column(String(2000), nullable=True)
    server_url = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_sync_logs_status", "status"),
        Index("idx_sync_logs_started", "started_at"),
    )


class SyncOutboxModel(Base, BaseMixin):
    __tablename__ = "sync_outbox"

    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    operation = Column(String(10), default="upsert")
    payload_json = Column(Text, nullable=False)
    status = Column(String(10), default="pending")
    attempt_count = Column(Integer, default=0)
    last_error = Column(String(1000), nullable=True)
    next_retry_at = Column(String(27), nullable=True)

    __table_args__ = (
        Index("idx_sync_outbox_status", "status"),
        Index("idx_sync_outbox_entity", "entity_type", "entity_id"),
    )