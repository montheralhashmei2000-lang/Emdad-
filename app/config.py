ل"""
نظام الإمداد والتموين - الإعدادات العامة
Offline-First Logistics & Supply System - Application Configuration
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Optional


APP_NAME = "نظام الإمداد والتموين"
APP_VERSION = "1.0.0"
APP_CODE = "LOGISTICS_SUPPLY_SYSTEM"
APP_ORG = "مكتب النظم والمعلومات"


def get_base_dir() -> Path:
    """
    تحديد المسار الأساسي للتطبيق.
    - في وضع التطوير: مجلد المشروع.
    - في وضع التنفيذ (.exe): مجلد البرنامج المُجمَّع.
    """
    if getattr(sys, "frozen", False):  # PyInstaller
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
RESOURCES_DIR = BASE_DIR / "app" / "resources"

# إنشاء المجلدات إذا لم تكن موجودة
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# مسار قاعدة البيانات المحلية SQLite
DATABASE_PATH = DATA_DIR / "logistics.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
DATABASE_TIMEOUT = 30  # ثانية
REQUEST_TIMEOUT = 15   # ثانية

# إعدادات الأمان
SECRET_KEY = "your-secret-key-here-change-me-in-production"
DEFAULT_TOKEN = "default-admin-token-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
TOKEN_EXPIRE_DAYS = 7


class Settings:
    """إعدادات قابلة للتعديل من شاشة الإعدادات."""

    def __init__(self) -> None:
        # معرف المعسكر المحلي (يُعيّن من إعدادات التهيئة أو المزامنة)
        self.camp_id: Optional[str] = None

        # عنوان الخادم المركزي REST API
        self.server_url: str = ""

        # فترة فحص الاتصال بالمزامنة (بالدقائق)
        self.sync_interval_minutes: int = 5

        # فترة فحص حالة الشبكة (بالثواني)
        self.network_check_seconds: int = 15

        # مهلة الطلب للخادم (بالثواني)
        self.request_timeout_seconds: int = 10

        # تمكين المزامنة التلقائية
        self.auto_sync_enabled: bool = True

        # معرف الجهاز المحلي (ثابت لكل تثبيت)
        self.device_id: str = self._generate_or_load_device_id()

    @staticmethod
    def _generate_or_load_device_id() -> str:
        """توليد أو تحميل معرف الجهاز المحلي الثابت."""
        device_file = BASE_DIR / ".device_id"
        if device_file.exists():
            return device_file.read_text(encoding="utf-8").strip()
        device_id = str(uuid.uuid4())
        device_file.write_text(device_id, encoding="utf-8")
        return device_id

    def save(self) -> None:
        """حفظ الإعدادات في ملف JSON للأجهزة المتعددة."""
        import json

        settings_file = DATA_DIR / "settings.json"
        payload = {
            "camp_id": self.camp_id,
            "server_url": self.server_url,
            "sync_interval_minutes": self.sync_interval_minutes,
            "network_check_seconds": self.network_check_seconds,
            "request_timeout_seconds": self.request_timeout_seconds,
            "auto_sync_enabled": self.auto_sync_enabled,
            "device_id": self.device_id,
        }
        settings_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls) -> "Settings":
        """تحميل الإعدادات المحفوظة إن وجدت."""
        import json

        settings = cls()
        settings_file = DATA_DIR / "settings.json"
        if settings_file.exists():
            try:
                payload = json.loads(settings_file.read_text(encoding="utf-8"))
                settings.camp_id = payload.get("camp_id")
                settings.server_url = payload.get("server_url", "")
                settings.sync_interval_minutes = payload.get("sync_interval_minutes", 5)
                settings.network_check_seconds = payload.get("network_check_seconds", 15)
                settings.request_timeout_seconds = payload.get("request_timeout_seconds", 10)
                settings.auto_sync_enabled = payload.get("auto_sync_enabled", True)
            except (json.JSONDecodeError, OSError):
                pass
        return settings

    def __repr__(self) -> str:
        return (
            f"Settings(camp_id={self.camp_id!r}, server_url={self.server_url!r}, "
            f"auto_sync={self.auto_sync_enabled}, device_id={self.device_id!r})"
        )


# نسخة عامة من الإعدادات
settings = Settings.load()


def init_app_settings(camp_id: str | None = None, server_url: str = "") -> None:
    """تهيئة الإعدادات العامة عند تشغيل التطبيق."""
    global settings
    settings = Settings.load()
    if camp_id:
        settings.camp_id = camp_id
    if server_url:
        settings.server_url = server_url
    settings.save()