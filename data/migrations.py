"""
نظام الإمداد والتموين - ترقيات قاعدة البيانات
Database Migration Manager - Version-based schema updates
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import DATA_DIR, APP_VERSION
from data.database import get_session, init_database, engine


MIGRATIONS_FILE = DATA_DIR / "schema_version.json"


def _get_current_version() -> str:
    """قراءة إصدار قاعدة البيانات الحالي."""
    if MIGRATIONS_FILE.exists():
        try:
            data = json.loads(MIGRATIONS_FILE.read_text(encoding="utf-8"))
            return data.get("version", "0.0.0")
        except (json.JSONDecodeError, OSError):
            return "0.0.0"
    return "0.0.0"


def _set_current_version(version: str) -> None:
    """تحديث إصدار قاعدة البيانات."""
    MIGRATIONS_FILE.write_text(
        json.dumps({"version": version, "app_version": APP_VERSION}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def run_migrations() -> None:
    """
    تشغيل الترقيات اللازمة لقاعدة البيانات.
    يُستدعى عند بدء تشغيل التطبيق.
    """
    current = _get_current_version()
    print(f"[Migrations] الإصدار الحالي لقاعدة البيانات: {current}")

    session = get_session()
    try:
        # الترقية إلى 1.0.0: إنشاء الجداول الأساسية
        if current < "1.0.0":
            print("[Migrations] ترقية إلى 1.0.0: إنشاء الجداول الأساسية...")
            init_database()
            _set_current_version("1.0.0")

        # الترقيات المستقبلية تضاف هنا:
        # if current < "1.1.0":
        #     print("[Migrations] ترقية إلى 1.1.0: إضافة حقل xxx...")
        #     with engine.connect() as conn:
        #         conn.execute(text("ALTER TABLE xyz ADD COLUMN ..."))
        #     _set_current_version("1.1.0")

        print(f"[Migrations] قاعدة البيانات محدثة: {_get_current_version()}")
    finally:
        session.close()


def reset_database() -> None:
    """إعادة تعيين قاعدة البيانات (حذف وإعادة إنشاء)."""
    import os
    from app.config import DATABASE_PATH

    confirm = input("سيتم حذف جميع البيانات! هل أنت متأكد؟ (yes/no): ")
    if confirm.lower() != "yes":
        print("تم الإلغاء.")
        return

    # حذف ملف قاعدة البيانات
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
        print(f"[Reset] تم حذف: {DATABASE_PATH}")

    # حذف ملف WAL و SHM إن وجد
    for ext in ["-wal", "-shm"]:
        p = Path(str(DATABASE_PATH) + ext)
        if p.exists():
            p.unlink()

    # حذف ملف الإصدار
    if MIGRATIONS_FILE.exists():
        MIGRATIONS_FILE.unlink()

    print("[Reset] يتم إنشاء قاعدة بيانات جديدة...")
    init_database()
    _set_current_version(APP_VERSION)
    print(f"[Reset] تم إنشاء قاعدة بيانات جديدة بنجاح (الإصدار: {APP_VERSION}).")