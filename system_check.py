"""سكربت فحص شامل للنظام من الصفر"""
import os
import sys
import sqlite3
import traceback

def check_database():
    """فحص قاعدة البيانات"""
    print("\n=== 1. فحص قاعدة البيانات ===")
    db_path = os.path.join("data", "logistics.db")
    print(f"  مسار قاعدة البيانات: {db_path}")
    print(f"  موجود: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print("  ❌ قاعدة البيانات غير موجودة!")
        return False
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # فحص الجداول
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print(f"  عدد الجداول: {len(tables)}")
    print(f"  الجداول: {tables}")
    
    # فحص المستخدمين
    cur.execute("SELECT username, full_name, role, is_active FROM users")
    users = cur.fetchall()
    print(f"  عدد المستخدمين: {len(users)}")
    for u in users:
        print(f"    - {u}")
    
    # فحص المعسكرات
    cur.execute("SELECT name, code FROM camps")
    camps = cur.fetchall()
    print(f"  عدد المعسكرات: {len(camps)}")
    
    # فحص الأصناف
    cur.execute("SELECT COUNT(*) FROM items")
    items_count = cur.fetchone()[0]
    print(f"  عدد الأصناف: {items_count}")
    
    # فحص المخازن
    cur.execute("SELECT COUNT(*) FROM warehouses")
    wh_count = cur.fetchone()[0]
    print(f"  عدد المخازن: {wh_count}")
    
    conn.close()
    return True

def check_imports():
    """فحص استيراد الوحدات الأساسية"""
    print("\n=== 2. فحص استيراد الوحدات ===")
    modules = [
        ("app.config", "الإعدادات"),
        ("core.enums", "التعدادات"),
        ("core.models.base", "النموذج الأساسي"),
        ("core.models.item", "نموذج الصنف"),
        ("core.models.user", "نموذج المستخدم"),
        ("core.models.transaction", "نموذج المعاملات"),
        ("core.models.warehouse", "نموذج المخزن"),
        ("core.models.custody", "نموذج العهد"),
        ("core.models.stocktake", "نموذج الجرد"),
        ("core.models.audit", "نموذج التدقيق"),
        ("core.models.sync", "نموذج المزامنة"),
        ("core.security.authentication", "المصادقة"),
        ("core.security.authorization", "الصلاحيات"),
        ("core.services.user_service", "خدمة المستخدمين"),
        ("core.services.inventory_service", "خدمة المخزون"),
        ("core.services.transaction_service", "خدمة المعاملات"),
        ("core.services.audit_service", "خدمة التدقيق"),
        ("data.database", "قاعدة البيانات"),
        ("data.orm_models", "نماذج ORM"),
        ("data.migrations", "الترقيات"),
        ("data.seed_data", "البيانات الأولية"),
        ("sync.api_client", "عميل API"),
        ("sync.network_monitor", "مراقب الشبكة"),
        ("sync.sync_engine", "محرك المزامنة"),
        ("ui.main_window", "النافذة الرئيسية"),
        ("ui.theme", "الثيم"),
    ]
    
    success = 0
    failed = 0
    for module, desc in modules:
        try:
            __import__(module)
            print(f"  ✅ {desc} ({module})")
            success += 1
        except Exception as e:
            print(f"  ❌ {desc} ({module}): {e}")
            failed += 1
    
    print(f"\n  النتيجة: {success} نجح، {failed} فشل")
    return failed == 0

def check_ui_screens():
    """فحص شاشات الواجهة"""
    print("\n=== 3. فحص شاشات الواجهة ===")
    screens = [
        "ui.views.inventory_view",
        "ui.views.items_management_view",
        "ui.views.receive_view",
        "ui.views.issue_view",
        "ui.views.transfer_view",
        "ui.views.warehouses_view",
        "ui.views.beneficiary_units_view",
        "ui.views.entitlements_view",
        "ui.views.daily_strength_view",
        "ui.views.returns_view",
        "ui.views.facilities_view",
        "ui.views.inventory_count_view",
        "ui.views.suppliers_view",
        "ui.views.reports_view",
        "ui.views.logistics_tracker_view",
        "ui.views.settings_view",
        "ui.views.transfer_notifications_view",
        "ui.views.login_dialog",
        "ui.views.emergency_view",
        "ui.views.emergency_sync_view",
        "ui.views.opening_balance_view",
        "ui.views.notification_view",
        "ui.views.personnel_view",
        "ui.views.sync_screen",
        "ui.views.transactions_screen",
        "ui.toast_widget",
        "ui.loading_overlay",
        "ui.api_service",
        "ui.screens.dashboard_screen",
        "ui.screens.items_management_view",
        "ui.screens.inventory_view",
        "ui.screens.warehouses_view",
        "ui.screens.receive_view",
        "ui.screens.issue_view",
        "ui.screens.transactions_screen",
        "ui.screens.custody_screen",
        "ui.screens.stocktake_screen",
        "ui.screens.reports_view",
        "ui.screens.sync_screen",
        "ui.screens.settings_screen",
    ]
    
    success = 0
    failed = 0
    for screen in screens:
        try:
            __import__(screen)
            print(f"  ✅ {screen}")
            success += 1
        except Exception as e:
            print(f"  ❌ {screen}: {e}")
            failed += 1
    
    print(f"\n  النتيجة: {success} نجح، {failed} فشل")
    return failed == 0

def check_widgets():
    """فحص مكونات الواجهة"""
    print("\n=== 4. فحص مكونات الواجهة ===")
    widgets = [
        "ui.widgets.sidebar",
        "ui.widgets.header",
    ]
    
    success = 0
    failed = 0
    for w in widgets:
        try:
            __import__(w)
            print(f"  ✅ {w}")
            success += 1
        except Exception as e:
            print(f"  ❌ {w}: {e}")
            failed += 1
    
    print(f"\n  النتيجة: {success} نجح، {failed} فشل")
    return failed == 0

def check_repositories():
    """فحص المستودعات"""
    print("\n=== 5. فحص مستودعات البيانات ===")
    repos = [
        "core.repositories.base_repository",
        "data.repositories_impl.base_sqlite_repository",
        "data.repositories_impl.repository_factory",
    ]
    
    success = 0
    failed = 0
    for r in repos:
        try:
            __import__(r)
            print(f"  ✅ {r}")
            success += 1
        except Exception as e:
            print(f"  ❌ {r}: {e}")
            failed += 1
    
    print(f"\n  النتيجة: {success} نجح، {failed} فشل")
    return failed == 0

def run_tests():
    """تشغيل الاختبارات"""
    print("\n=== 6. تشغيل الاختبارات ===")
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True, text=True, encoding="utf-8"
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    return result.returncode == 0

def main():
    print("=" * 60)
    print("فحص شامل لنظام الإمداد والتموين")
    print("=" * 60)
    
    results = []
    
    # 1. فحص قاعدة البيانات
    try:
        results.append(("قاعدة البيانات", check_database()))
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        traceback.print_exc()
        results.append(("قاعدة البيانات", False))
    
    # 2. فحص الاستيرادات
    try:
        results.append(("استيراد الوحدات", check_imports()))
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        traceback.print_exc()
        results.append(("استيراد الوحدات", False))
    
    # 3. فحص الشاشات
    try:
        results.append(("شاشات الواجهة", check_ui_screens()))
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        traceback.print_exc()
        results.append(("شاشات الواجهة", False))
    
    # 4. فحص المكونات
    try:
        results.append(("مكونات الواجهة", check_widgets()))
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        traceback.print_exc()
        results.append(("مكونات الواجهة", False))
    
    # 5. فحص المستودعات
    try:
        results.append(("مستودعات البيانات", check_repositories()))
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        traceback.print_exc()
        results.append(("مستودعات البيانات", False))
    
    # 6. تشغيل الاختبارات
    try:
        results.append(("الاختبارات", run_tests()))
    except Exception as e:
        print(f"  ❌ خطأ: {e}")
        traceback.print_exc()
        results.append(("الاختبارات", False))
    
    # التقرير النهائي
    print("\n" + "=" * 60)
    print("التقرير النهائي")
    print("=" * 60)
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
    
    all_pass = all(s for _, s in results)
    print(f"\n  النتيجة الإجمالية: {'✅ جميع الفحوصات نجحت' if all_pass else '❌ توجد فحوصات فاشلة'}")
    print("=" * 60)
    
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())