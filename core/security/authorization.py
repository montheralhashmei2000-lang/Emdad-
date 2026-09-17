"""
نظام الإمداد والتموين - خدمة التخويل والصلاحيات
Authorization Service - RBAC (Role-Based Access Control)
"""
from enum import Enum
from typing import List, Optional, Set
from functools import wraps

from core.models.base import BaseSchema
from core.models.user import User

class Permission(str, Enum):
    """الصلاحيات الأساسية"""
    # صلاحيات المخزون
    INVENTORY_VIEW = "inventory.view"
    INVENTORY_CREATE = "inventory.create"
    INVENTORY_EDIT = "inventory.edit"
    INVENTORY_DELETE = "inventory.delete"
    INVENTORY_ADJUST = "inventory.adjust"
    INVENTORY_EXPORT = "inventory.export"
    
    # صلاحيات الأصناف
    ITEMS_VIEW = "items.view"
    ITEMS_CREATE = "items.create"
    ITEMS_EDIT = "items.edit"
    ITEMS_DELETE = "items.delete"
    ITEMS_MANAGE = "items.manage"
    
    # صلاحيات المعاملات
    TRANSACTIONS_VIEW = "transactions.view"
    TRANSACTIONS_CREATE = "transactions.create"
    TRANSACTIONS_APPROVE = "transactions.approve"
    TRANSACTIONS_CANCEL = "transactions.cancel"
    
    # صلاحيات الصرف
    ISSUE_VIEW = "issue.view"
    ISSUE_CREATE = "issue.create"
    ISSUE_APPROVE = "issue.approve"
    ISSUE_ISSUE = "issue.issue"
    ISSUE_CANCEL = "issue.cancel"
    
    # صلاحيات الاستلام
    RECEIVE_VIEW = "receive.view"
    RECEIVE_CREATE = "receive.create"
    RECEIVE_APPROVE = "receive.approve"
    RECEIVE_CANCEL = "receive.cancel"
    
    # صلاحيات المرتجعات
    RETURNS_VIEW = "returns.view"
    RETURNS_CREATE = "returns.create"
    RETURNS_APPROVE = "returns.approve"
    
    # صلاحيات التحويلات
    TRANSFERS_VIEW = "transfers.view"
    TRANSFERS_CREATE = "transfers.create"
    TRANSFERS_APPROVE = "transfers.approve"
    TRANSFERS_RECEIVE = "transfers.receive"
    
    # صلاحيات الاستحقاقات
    ENTITLEMENTS_VIEW = "entitlements.view"
    ENTITLEMENTS_CREATE = "entitlements.create"
    ENTITLEMENTS_EDIT = "entitlements.edit"
    ENTITLEMENTS_APPROVE = "entitlements.approve"
    
    # صلاحيات التقارير
    REPORTS_VIEW = "reports.view"
    REPORTS_EXPORT = "reports.export"
    REPORTS_PRINT = "reports.print"
    
    # صلاحيات النظام
    SYSTEM_ADMIN = "system.admin"
    USERS_MANAGE = "users.manage"
    SETTINGS_MANAGE = "settings.manage"

class Role(BaseSchema):
    """دور المستخدم"""
    name: str
    description: Optional[str] = None
    permissions: List[Permission] = []
    is_active: bool = True

class UserRole(BaseSchema):
    """ربط المستخدم بالدور"""
    user_id: str
    role_id: str

# الأدوار المحددة مسبقاً
PREDEFINED_ROLES = {
    "super_admin": Role(
        name="مدير النظام",
        description="صلاحيات كاملة على النظام",
        permissions=list(Permission)
    ),
    "warehouse_manager": Role(
        name="مدير المستودع",
        description="إدارة المخزون والمعاملات",
        permissions=[
            Permission.INVENTORY_VIEW,
            Permission.INVENTORY_CREATE,
            Permission.INVENTORY_EDIT,
            Permission.INVENTORY_ADJUST,
            Permission.TRANSACTIONS_VIEW,
            Permission.TRANSACTIONS_CREATE,
            Permission.TRANSACTIONS_APPROVE,
            Permission.ISSUE_VIEW,
            Permission.ISSUE_CREATE,
            Permission.ISSUE_APPROVE,
            Permission.RECEIVE_VIEW,
            Permission.RECEIVE_CREATE,
            Permission.RECEIVE_APPROVE,
            Permission.RETURNS_VIEW,
            Permission.RETURNS_CREATE,
            Permission.TRANSFERS_VIEW,
            Permission.TRANSFERS_CREATE,
            Permission.REPORTS_VIEW,
            Permission.REPORTS_EXPORT
        ]
    ),
    "warehouse_clerk": Role(
        name="أمين مستودع",
        description="تنفيذ المعاملات المخزنية",
        permissions=[
            Permission.INVENTORY_VIEW,
            Permission.TRANSACTIONS_VIEW,
            Permission.TRANSACTIONS_CREATE,
            Permission.ISSUE_VIEW,
            Permission.ISSUE_CREATE,
            Permission.RECEIVE_VIEW,
            Permission.RECEIVE_CREATE,
            Permission.RETURNS_VIEW,
            Permission.RETURNS_CREATE,
            Permission.TRANSFERS_VIEW,
            Permission.TRANSFERS_CREATE,
            Permission.REPORTS_VIEW
        ]
    ),
    "accountant": Role(
        name="محاسب",
        description="مراجعة التقارير والمعاملات",
        permissions=[
            Permission.INVENTORY_VIEW,
            Permission.TRANSACTIONS_VIEW,
            Permission.ISSUE_VIEW,
            Permission.RECEIVE_VIEW,
            Permission.RETURNS_VIEW,
            Permission.TRANSFERS_VIEW,
            Permission.ENTITLEMENTS_VIEW,
            Permission.REPORTS_VIEW,
            Permission.REPORTS_EXPORT,
            Permission.REPORTS_PRINT
        ]
    ),
    "viewer": Role(
        name="مطلع",
        description="عرض البيانات فقط",
        permissions=[
            Permission.INVENTORY_VIEW,
            Permission.TRANSACTIONS_VIEW,
            Permission.ISSUE_VIEW,
            Permission.RECEIVE_VIEW,
            Permission.RETURNS_VIEW,
            Permission.TRANSFERS_VIEW,
            Permission.REPORTS_VIEW
        ]
    )
}

def has_permission(user: User, permission: Permission) -> bool:
    """التحقق من وجود صلاحية للمستخدم"""
    if not user or not user.is_active:
        return False
    
    # TODO: استبدال هذا بطلب حقيقي لقاعدة البيانات
    # للحصول على أدوار المستخدم وصلاحياته
    user_permissions = get_user_permissions(user.id)
    return permission in user_permissions

def get_user_permissions(user_id: str) -> Set[Permission]:
    """الحصول على جميع صلاحيات المستخدم"""
    # TODO: استبدال هذا بطلب حقيقي لقاعدة البيانات
    # للحصول على أدوار المستخدم وصلاحياته
    return set()

def require_permission(permission: Permission):
    """ديكوريتر للتحقق من الصلاحية"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # TODO: الحصول على المستخدم الحالي من الجلسة
            current_user = None  # get_current_user()
            
            if not has_permission(current_user, permission):
                raise PermissionError(f"ليس لديك صلاحية: {permission.value}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

class AuthorizationService:
    """خدمة التخويل والصلاحيات"""
    
    def __init__(self):
        pass
    
    def check_permission(self, user: User, permission: Permission) -> bool:
        """التحقق من صلاحية المستخدم"""
        return has_permission(user, permission)
    
    def get_user_roles(self, user_id: str) -> List[Role]:
        """الحصول على أدوار المستخدم"""
        # TODO: تنفيذ الطلب لقاعدة البيانات
        return []
    
    def assign_role(self, user_id: str, role_id: str) -> bool:
        """تعيين دور للمستخدم"""
        # TODO: تنفيذ الطلب لقاعدة البيانات
        return True
    
    def revoke_role(self, user_id: str, role_id: str) -> bool:
        """إلغاء دور من المستخدم"""
        # TODO: تنفيذ الطلب لقاعدة البيانات
        return True