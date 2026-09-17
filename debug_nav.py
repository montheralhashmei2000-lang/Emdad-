import sys
sys.path.insert(0, r'E:\Emdad_system')
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

app = QApplication([])
window = MainWindow()

print("🔍 تشخيص مشكلة التنقل\n")
print("1. routes:", list(window.routes.keys()) if hasattr(window, 'routes') else "لا توجد")
print("\n2. sidebar_buttons:", list(window.sidebar_buttons.keys()) if hasattr(window, 'sidebar_buttons') else "لا توجد")

# Search for the items management button name
if hasattr(window, 'sidebar_buttons'):
    for btn_name in window.sidebar_buttons.keys():
        if 'ص' in btn_name or 'ن' in btn_name:
            print(f"   مماثل: '{btn_name}'")