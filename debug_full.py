import sys
sys.path.insert(0, r'E:\Emdad_system')

print("="*70)
print("🔍 تشخيص كامل للنظام")
print("="*70)

# 1. استيراد المكونات
print("\n1. 🔧 استيراد المكونات:")
try:
    from ui.main_window import MainWindow
    print("   ✅ MainWindow تم استيراده بنجاح")
except Exception as e:
    print(f"   ❌ خطأ في استيراد MainWindow: {e}")
    sys.exit(1)

# 2. إنشاء نافذة للتشخيص
print("\n2. 📋 إنشاء نافذة تشخيصية:")
try:
    from PyQt6.QtWidgets import QApplication
    app = QApplication([])
    window = MainWindow()
    print("   ✅ MainWindow تم إنشاؤه بنجاح")
except Exception as e:
    print(f"   ❌ خطأ في إنشاء MainWindow: {e}")
    sys.exit(1)

# 3. فحص المسارات الفورية
print("\n3. 🚀 فحص المسارات الفورية (self.routes):")
if hasattr(window, 'routes'):
    routes = window.routes
    print(f"   📊 إجمالي المسارات الفورية: {len(routes)}")
    print("\n   المسارات الفورية:")
    for i, (name, panel) in enumerate(routes.items(), 1):
        panel_type = type(panel).__name__
        print(f"      {i:2d}. {name:35s} -> {panel_type}")
else:
    print("   ❌ لا توجد خاصية self.routes")

# 4. فحص المسارات البطيئة
print("\n4. 🏃 فحص المسارات البطيئة (_lazy_routes):")
if hasattr(window, '_lazy_routes'):
    lazy_routes = window._lazy_routes
    print(f"   📊 إجمالي المسارات البطيئة: {len(lazy_routes)}")
    print("\n   المسارات البطيئة (أول 10):")
    for i, (name, panel_func) in enumerate(lazy_routes.items(), 1):
        print(f"      {i:2d}. {name:45s}")
        if i >= 10:
            print("      ... (وأخرى)")
            break
else:
    print("   ❌ لا توجد خاصية _lazy_routes")

# 5. فحص الأزرار الجانبية
print("\n5. 📌 فحص الأزرار الجانبية (sidebar_buttons):")
if hasattr(window, 'sidebar_buttons'):
    sidebar_buttons = window.sidebar_buttons
    print(f"   📊 إجمالي الأزرار الجانبية: {len(sidebar_buttons)}")
    print("\n   الأزرار الجانبية:")
    for i, (name, button) in enumerate(sidebar_buttons.items(), 1):
        print(f"      {i:2d}. {name:45s}")
else:
    print("   ❌ لا توجد خاصية sidebar_buttons")

# 6. البحث عن شاشات الإدارة المحددة
print("\n6. 🔍 البحث عن شاشات إدارة الأصناف المحددة:")
target_name = 'إدارة الأصناف'
found_in_routes = target_name in window.routes if hasattr(window, 'routes') else False
found_in_lazy_routes = target_name in window._lazy_routes if hasattr(window, '_lazy_routes') else False
found_in_sidebar = target_name in window.sidebar_buttons if hasattr(window, 'sidebar_buttons') else False

print(f"   📍 البحث عن '{target_name}':")
print(f"      ✅ في المسارات الفورية: {found_in_routes}")
print(f"      ✅ في المسارات البطيئة: {found_in_lazy_routes}")
print(f"      ✅ في الأزرار الجانبية: {found_in_sidebar}")

if not (found_in_routes or found_in_lazy_routes or found_in_sidebar):
    print(f"\n   ⚠️  '{target_name}' غير موجود!")
    print("\n   🔍 الشاشات المحتملة المشابهة:")
    if hasattr(window, 'sidebar_buttons'):
        for btn_name in window.sidebar_buttons.keys():
            if 'صنف' in btn_name or 'إدارة' in btn_name or 'أصناف' in btn_name:
                print(f"      → {btn_name}")

# 7. فحص حالة الصلاحيات
print("\n7. 🔒 فحص حالة الصلاحيات:")
if hasattr(window, 'current_user'):
    user = window.current_user
    print(f"   👤 المستخدم الحالي: {user.get('full_name', 'غير معروف') if user else 'null'}")
    print(f"   🎭 الدور: {user.get('role', 'null') if user else 'null'}")
else:
    print("   ❌ لا توجد خاصية current_user")

# 8. فحص حالة الشاشة المحددة
print("\n8. 📺 فحص حالة الشاشة المحددة:")
if found_in_routes:
    panel = window.routes[target_name]
    print(f"   📱 نوع اللوحة: {type(panel).__name__}")
    print(f"   🏭 اسم الفئة: {panel.__class__.__name__}")
    if hasattr(panel, '_data_loaded'):
        print(f"   📊 حالة تحميل البيانات: {panel._data_loaded}")
else:
    print(f"   ❌ '{target_name}' غير متاح")

print("\n" + "="*70)
print("🎯 التشخيص مكتمل!")
print("="*70)