"""
نظام الإمداد والتموين - قاعدة البيانات المحلية SQLite
Database Engine, Session, and Connection Management
"""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base

from app.config import DATABASE_URL

# الكائن الأساسي لتعريف جداول ORM
Base = declarative_base()

# إنشاء محرك قاعدة البيانات (مع دعم WAL للكتابة المتزامنة)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # PySide6 يعمل على خيط واحد
    echo=False,                                 # تعطيل تسجيل الاستعلامات (شغّل True للتطوير)
    pool_pre_ping=True,                         # فحص الاتصال قبل الاستخدام
)

# تفعيل Write-Ahead Logging (WAL) لتحسين أداء القراءة/الكتابة المتزامنة
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-8000")  # 8MB cache
    cursor.execute("PRAGMA busy_timeout=5000")  # 5 ثوانٍ مهلة الانتظار
    cursor.close()


# مصنع جلسات قاعدة البيانات
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_session() -> Session:
    """الحصول على جلسة قاعدة بيانات جديدة."""
    return SessionLocal()


def init_database() -> None:
    """إنشاء جميع الجداول في قاعدة البيانات (في حال لم تكن موجودة)."""
    from data.orm_models import (
        CampModel,
        UserModel,
        ItemCategoryModel,
        UnitOfMeasureModel,
        ItemModel,
        ItemUnitModel,
        SupplierModel,
        WarehouseModel,
        TransactionModel,
        TransactionItemModel,
        CustodyModel,
        CustodyItemModel,
        CustodyReturnModel,
        CustodyReturnItemModel,
        StocktakeModel,
        StocktakeItemModel,
        StockBalanceModel,
        ItemPriceModel,
        AuditLogModel,
        SyncLogModel,
        SyncOutboxModel,
    )
    Base.metadata.create_all(bind=engine)


def close_database() -> None:
    """إغلاق جميع اتصالات قاعدة البيانات."""
    engine.dispose()