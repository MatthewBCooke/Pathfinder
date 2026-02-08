# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Pathfinder GUI application.

Creates a standalone executable bundle for Windows, macOS, and Linux.
Build command: pyinstaller pathfinder.spec
Output: dist/pathfinder (or dist/pathfinder.exe on Windows)
"""

a = Analysis(
    ['pathfinder_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('pathfinder', 'pathfinder'),  # Include analysis package
        ('gui', 'gui'),                 # Include GUI package
        ('icon.ico', '.'),              # App icon (if exists)
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'numpy',
        'scipy',
        'pandas',
        'pathfinder.models',
        'pathfinder.io',
        'pathfinder.analysis',
        'pathfinder.entropy',
        'pathfinder.types',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=['tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Pathfinder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Pathfinder',
)

# macOS .app bundle (optional)
app = BUNDLE(
    coll,
    name='Pathfinder.app',
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    bundle_identifier='com.ubcsnyder.pathfinder',
)
