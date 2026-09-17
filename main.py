"""
نظام الإمداد والتموين - نقطة الدخول الرئيسية
Logistics & Supply Management System - Main Entry Point
Offline-First Desktop Application for Inventory, Custody, and Transactions Management
"""
from __future__ import annotations

import sys
import os
import logging
from pathlib import Path

# إضافة المسار الحالي إلى sys.path (لضمان عمل الاستيراد من المجلدات)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ==================== إعداد التسجيل (Logging) ====================

def setup_logging() -> None:
    """إعداد نظام تسجيل الأحداث (Logging)."""
    from app.config import LOGS_DIR

    log_file = LOGS_DIR / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # تقليل مستوى تسجيل المكتبات الخارجية
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info("=" * 60)
    logging.info("بدء تشغيل نظام الإمداد والتموين")
    logging.info("=" * 60)


# ==================== تهيئة قاعدة البيانات ====================

def initialize_database() -> None:
    """تهيئة قاعدة البيانات وتشغيل الترقيات والبذور."""
    from data.migrations import run_migrations
    from data.seed_data import init_sample_data as seed_all

    # تشغيل الترقيات
    run_migrations()

    # إضافة البيانات الابتدائية إذا كانت قاعدة البيانات فارغة
    try:
        from data.database import get_session
        from data.orm_models import UnitOfMeasureModel

        session = get_session()
        count = session.query(UnitOfMeasureModel).count()
        session.close()

        if count == 0:
            logging.info("قاعدة البيانات فارغة - جاري إضافة البيانات الابتدائية...")
            seed_all()
    except Exception as e:
        logging.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        raise


# ==================== تشغيل التطبيق ====================

def main():
    """نقطة الدخول الرئيسية للتطبيق."""
    # إعداد التسجيل
    setup_logging()

    # تهيئة قاعدة البيانات
    logging.info("تهيئة قاعدة البيانات...")
    initialize_database()

    # استيراد PyQt6
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QIcon
    except ImportError as e:
        logging.error(f"خطأ في استيراد PyQt6: {e}")
        print("❌ يرجى تثبيت المكتبات المطلوبة: pip install PyQt6 qtawesome pyqtgraph")
        sys.exit(1)

    # إنشاء تطبيق Qt
    app = QApplication(sys.argv)
    app.setApplicationName("نظام الإمداد والتموين")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("مكتب النظم والمعلومات")

    # تطبيق الثيم
    from ui.theme import setup_theme
    setup_theme(app)

    # إنشاء وعرض النافذة الرئيسية
    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    logging.info("تم تشغيل التطبيق بنجاح")

    # تشغيل حلقة الأحداث
    sys.exit(app.exec())


if __name__ == "__main__":
    main()