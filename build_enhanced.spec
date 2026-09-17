# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# حل مشكلة ordinal 380 في مكتبات Qt
from PyInstaller.utils.hooks import collect_dynamic_libs

qt_binaries = collect_dynamic_libs('PySide6')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=qt_binaries,
    datas=[],
    hiddenimports=[
        'sqlalchemy',
        'sqlalchemy.ext',
        'sqlalchemy.orm',
        'sqlalchemy.sql',
        'pydantic',
        'pydantic.v1',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSql',
        'PySide6.QtNetwork',
        'core',
        'data',
        'ui',
        'sync',
        'app',
        'hashlib',
        'bcrypt',
        'passlib',
        'passlib.hash',
        'json',
        'datetime',
        'uuid'
    ],
    hookspath=[],
    hooksconfig={
        'PySide6': {
            'qt_plugins': ['platforms', 'styles', 'iconengines'],
        }
    },
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# إضافة بيانات إضافية
added_files = [
    ('app/resources/*', 'app/resources'),
    ('logs/*', 'logs'),
    ('*.bat', '.'),
]

for src, dest in added_files:
    a.datas += [(src, dest)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='نظام_الامداد',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # نافذة بدون كونسول
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
