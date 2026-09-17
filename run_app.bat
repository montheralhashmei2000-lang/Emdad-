@echo off
chcp 65001 >nul
title نظام الإمداد والتموين
cd /d "%~dp0"
echo ====================================
echo    نظام الإمداد والتموين
echo    Logistics & Supply Management
echo ====================================
echo.
python main.py
if errorlevel 1 (
    echo.
    echo خطأ: فشل تشغيل التطبيق
    pause
)