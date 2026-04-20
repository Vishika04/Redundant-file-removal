# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['A:\\web development\\desktopApp\\RedundantFileRemover\\main.py'],
    pathex=['A:\\web development\\desktopApp\\RedundantFileRemover'],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('assets\\*', 'assets'),
        ('features', 'features'),
    ],
    hiddenimports=[
        'features.core.constants',
        'features.core.models',
        'features.core.utils',
        'features.scanner.worker',
        'features.scanner.tab',
        'features.storage.worker',
        'features.storage.tab',
        'features.ui.style',
        'features.ui.header',
        'features.ui.sidebar',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RedundantFileRemover',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\logo.ico'],
)
