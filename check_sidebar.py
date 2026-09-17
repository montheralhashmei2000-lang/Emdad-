import sys
import re
sys.path.insert(0, r'E:\\Emdad_system')

print("="*60)
print("🔍 فحص بناء القائمة الجانبية")
print("="*60)

# قراءة ملف main_window.py مباشرة
try:
    with open(r'E:\\Emdad_system\\ui\\main_window.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("✅ تم قراءة main_window.py بنجاح")
    
    # البحث عن دالة _build_sidebar
    sidebar_pattern = r'def _build_sidebar\(self\) -> QWidget:(.*?)(?=\n\s+def |\n\s+class |\Z)'
    sidebar_match = re.search(sidebar_pattern, content, re.DOTALL)
    
    if sidebar_match:
        sidebar_code = sidebar_match.group(1)
        print("\n📋 محتوى دالة _build_sidebar:")
        print("-"*50)
        print(sidebar_code[:2000])  # أول 2000 حرف
        if len(sidebar_code) > 2000:
            print("... (مُقتصر على أول 2000 حرف)")
    else:
        print("❌ لم يتم العثور على دالة _build_sidebar")
    
    # البحث عن جميع استدعاءات self.sidebar_buttons[]
    button_pattern = r"self\.sidebar_buttons\['([^']+)'\]"
    buttons = re.findall(button_pattern, content)
    
    print(f"\n🔘 جميع الأزرار المكتشفة ({len(buttons)}):")
    for i, btn in enumerate(sorted(set(buttons)), 1):
        print(f"   {i:2d}. {btn}")
        
    # البحث عن كلمات مفتاحية محددة
    print("\n🔍 البحث عن كلمات مفتاحية:")
    keywords = ['إدارة الأصناف', 'صنف', 'Items', 'إدارة القوة', 'الأرصدة الافتتاحية']
    for keyword in keywords:
        matches = [btn for btn in buttons if keyword in btn]
        if matches:
            print(f"   '{keyword}': {matches}")
        else:
            print(f"   '{keyword}': غير موجود")
            
except Exception as e:
    print(f"❌ خطأ: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)