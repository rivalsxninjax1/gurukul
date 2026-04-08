# gurukul.spec
import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/logo.png', 'assets'),
    ],
    hiddenimports=[
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.ext.declarative',
        'bcrypt',
        'pandas',
        'openpyxl',
        'openpyxl.cell._writer',
        'reportlab',
        'reportlab.platypus',
        'reportlab.lib.pagesizes',
        'reportlab.lib.colors',
        'reportlab.pdfgen.canvas',
        'dateutil',
        'dateutil.relativedelta',
        'PIL',
        'PIL.Image',
        'PyQt5',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GurukuCMS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No black console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Set to 'assets/icon.ico' if you have one
)