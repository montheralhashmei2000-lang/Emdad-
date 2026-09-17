import sys
import re
sys.path.insert(0, r'E:\\Emdad_system')

print("="*70)
print("🔍 فحص سبب عدم ظهور الأزرار")
print("="*70)

with open(r'E:\\Emdad_system\\ui\\main_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

# استخراج دالة _build_sidebar بالكامل
sidebar_pattern = r'def _build_sidebar\(self\) -> QWidget:(.*?)(?=\n    def |\nclass |\Z)'
sidebar_match = re.search(sidebar_pattern, content, re.DOTALL)

if sidebar_match:
    sidebar_code = sidebar_match.group(1)
    
    # البحث عن الحلقة التي تضيف الأزرار
    loop_pattern = r'for label.*?in.*?:(.*?)(?=\n        [a-z]|\n    [a-z]|\Z)'
    loops = re.findall(loop_pattern, sidebar_code, re.DOTALL)
    
    print("\n📋 الحلقات التي تضيف الأزرار:")
    for i, loop in enumerate(loops, 1):
        print(f"\n--- الحلقة {i} ---")
        print(loop[:1500])
        if len(loop) > 1500:
            print("...")
    
    # البحث عن شروط skip/continue
    skip_pattern = r'(if.*?(?:skip|continue|not.*?allowed|not.*?perm)):'
    skips = re.findall(skip_pattern, sidebar_code)
    
    print(f"\n⚠️  شروط التخطي المكتشفة: {len(skips)}")
    for skip in skips[:5]:
        print(f"   - {skip[:100]}")
    
    # البحث عن الـ permissions check
    perm_pattern = r'if.*?(?:user_perms|perm|allowed|permission).*?:(.*?)(?=\n        [a-z]|\n    [a-z]|\Z)'
    perms = re.findall(perm_pattern, sidebar_code, re.DOTALL)
    
    print(f"\n🔒 فحوصات الصلاحيات: {len(perms)}")
    for i, perm in enumerate(perms[:3], 1):
        print(f"\n--- فحص {i} ---")
        print(perm[:500])

print("\n" + "="*70)