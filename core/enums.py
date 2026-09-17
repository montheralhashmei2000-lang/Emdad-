"""
نظام الإمداد والتموين - القيم الثابتة (Enums)
Core Domain Enums - مشتركة بين الطبقات كافة
"""
from __future__ import annotations

from enum import Enum


class SyncStatus(str, Enum):
    """حالة المزامنة للسجلات."""
    PENDING = "pending"       # في انتظار المزامنة
    SYNCED = "synced"         # تمت المزامنة بنجاح
    FAILED = "failed"         # فشلت المزامنة


class TransactionType(str, Enum):
    """أنواع المعاملات المخزنية."""
    RECEIVE = "receive"               # سند استلام مخزني
    ISSUE = "issue"                   # أمر صرف مخزني
    TRANSFER = "transfer"             # تحويل مخزني
    STOCKTAKE = "stocktake"           # جرد دوري
    WRITEOFF = "writeoff"             # إتلاف / تالف
    CUSTODY_ISSUE = "custody_issue"   # صرف عهد
    CUSTODY_RETURN = "custody_return" # استرجاع عهد
    RETURN = "return"                 # مرتجع


class TransactionStatus(str, Enum):
    """حالة المعاملة."""
    DRAFT = "draft"         # مسودة
    POSTED = "posted"       # معتمدة ومرحّلة
    CANCELLED = "cancelled" # ملغاة


class UserRole(str, Enum):
    """أدوار المستخدمين."""
    ADMIN = "admin"               # مدير النظام
    WAREHOUSE = "warehouse"       # أمين مخزن
    ACCOUNTANT = "accountant"     # محاسب
    VIEWER = "viewer"             # مُطّلع فقط


class CustodyStatus(str, Enum):
    """حالة العهد."""
    ACTIVE = "active"         # عهد سارية
    PARTIAL = "partial"       # استرجاع جزئي
    RETURNED = "returned"     # تم الاسترجاع كاملاً
    OVERDUE = "overdue"       # متأخرة عن تاريخ الاستحقاق


class ReturnCondition(str, Enum):
    """حالة الصنف عند الاسترجاع."""
    GOOD = "good"         # بحالة جيدة
    DAMAGED = "damaged"   # تالف
    MISSING = "missing"   # مفقود


class StocktakeStatus(str, Enum):
    """حالة دورة الجرد."""
    DRAFT = "draft"           # قيد الإعداد
    COMPLETED = "completed"   # مكتملة
    CANCELLED = "cancelled"   # ملغاة


class WarehouseType(str, Enum):
    """نوع المخزن."""
    MAIN = "main"   # مخزن رئيسي
    SUB = "sub"     # مخزن فرعي


class SyncLogStatus(str, Enum):
    """حالة جلسة المزامنة."""
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncOperation(str, Enum):
    """نوع العملية في طابور المزامنة."""
    UPSERT = "upsert"
    DELETE = "delete"


class AuditAction(str, Enum):
    """أفعال سجل التدقيق."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SYNC = "sync"
    LOGIN = "login"
    LOGOUT = "logout"
    PRINT = "print"
    EXPORT = "export"


class PriceType(str, Enum):
    """نوع السعر."""
    PURCHASE = "purchase"  # سعر شراء
    ISSUE = "issue"        # سعر صرف


class RowStatus(str, Enum):
    """حالة الصنف/المخزن."""
    ACTIVE = "active"
    INACTIVE = "inactive"