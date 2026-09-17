"""
نظام الإمداد والتموين - خدمة المصادقة
Authentication Service - handles user login, session management
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from core.models.base import BaseSchema
from core.models.user import User
from app.config import settings

# إعدادات الأمان
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseSchema):
    """نموذج رمز الوصول"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseSchema):
    """بيانات الرمز"""
    username: Optional[str] = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من تطابق كلمة المرور"""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """توليد هاش كلمة المرور"""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def hash_password(password: str) -> str:
    """توليد هاش كلمة المرور (alias for get_password_hash)"""
    return get_password_hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """إنشاء رمز وصول JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def authenticate_user(username: str, password: str, repo_factory=None) -> Optional[User]:
    """مصادقة المستخدم"""
    from data.repositories_impl.repository_factory import RepositoryFactory
    repo = repo_factory or RepositoryFactory()
    user = repo.users.get_by_username(username)
    
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def get_current_user(token: str) -> Optional[User]:
    """الحصول على المستخدم الحالي من الرمز"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except JWTError:
        return None
    
    # TODO: استبدال هذا بطلب حقيقي لقاعدة البيانات
    from data.repositories_impl.repository_factory import RepositoryFactory
    repo = RepositoryFactory()
    user = repo.users.get_by_username(token_data.username)
    
    if user is None:
        return None
    return user