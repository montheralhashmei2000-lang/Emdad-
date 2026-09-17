@echo off
chcp 65001 >nul
echo ====================================
echo    بناء التطبيق - PyInstaller
echo ====================================
echo.
echo تثبيت PyInstaller (إذا لم يكن مثبتاً)...
pip install pyinstaller -q
echo.
echo جاري البناء...
pyinstaller "نظام_الامداد.spec" --clean --noconfirm
echo.
echo ====================================
echo    اكتمل البناء!
echo    المجلد: dist\نظام_الامداد
echo ====================================
pause