# -*- mode: python ; coding: utf-8 -*-
"""
نظام الإمداد والتموين - PyInstaller Spec
Logistics & Supply Management - Build Spec
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect data files for SQLAlchemy, Babel, etc.
datas = []
hiddenimports = []

# UI assets
datas += collect_data_files('ui', includes=['*.qss', '*.png', '*.svg', '*.ico'])

# Babel locale data
try:
    datas += collect_data_files('babel')
except Exception:
    pass

# Hidden imports for dynamic modules
for mod in ['ui.views', 'ui.widgets', 'ui.screens',
            'core.models', 'core.services', 'core.security',
            'data.repositories_impl', 'sync']:
    try:
        hiddenimports += collect_submodules(mod)
    except Exception:
        pass

# Specific hidden imports
hiddenimports += [
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.orm.session',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'qtawesome',
    'pyqtgraph',
    'httpx',
    'PIL',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='نظام_الامداد',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='نظام_الامداد',
)