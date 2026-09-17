"""
نظام الإمداد والتموين - نموذج المستخدم
User Model with roles and permissions
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import Field, EmailStr, ConfigDict

from core.models.base import BaseSchema
from core.enums import UserRole

class User(BaseSchema):
    """نموذج المستخدم"""
    username: str = Field(..., min_length=3, max_length=50, description="اسم المستخدم")
    full_name: str = Field(..., min_length=1, max_length=200, description="الاسم الكامل")
    email: Optional[EmailStr] = Field(None, description="البريد الإلكتروني")
    password_hash: str = Field(..., description="هاش كلمة المرور")
    role: UserRole = Field(default=UserRole.VIEWER, description="دور المستخدم")
    is_active: bool = Field(default=True, description="حالة المستخدم")
    last_login: Optional[str] = Field(None, description="تاريخ آخر تسجيل دخول")
    phone: Optional[str] = Field(None, max_length=20, description="رقم الهاتف")
    department: Optional[str] = Field(None, max_length=100, description="القسم")
    position: Optional[str] = Field(None, max_length=100, description="المنصب")
    
    # حقول للقراءة فقط
    permissions: List[str] = Field(default_factory=list, description="قائمة الصلاحيات")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "admin",
                "full_name": "مدير النظام",
                "email": "admin@example.com",
                "role": "admin",
                "is_active": True,
                "department": "تقنية المعلومات",
                "position": "مدير النظام"
            }
        }
    )

class UserCreate(BaseSchema):
    """نموذج إنشاء مستخدم جديد"""
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6, max_length=100)
    role: UserRole = Field(default=UserRole.VIEWER)
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)

class UserUpdate(BaseSchema):
    """نموذج تحديث بيانات المستخدم"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    phone: Optional[str] = Field(None, max_length=20)
    department: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)

class ChangePassword(BaseSchema):
    """نموذج تغيير كلمة المرور"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=100)
    confirm_password: str = Field(..., min_length=6, max_length=100)