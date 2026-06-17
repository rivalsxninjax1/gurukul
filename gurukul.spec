# gurukul.spec
# PyInstaller build spec for Gurukul CMS
# Build ONLY on Windows to produce a Windows .exe
# Command: pyinstaller gurukul.spec

import sys
import os

block_cipher = None

# Collect all PyMuPDF files (includes native .dll/.so binaries)
from PyInstaller.utils.hooks import collect_all
fitz_datas, fitz_binaries, fitz_hiddenimports = collect_all('fitz')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=fitz_binaries,
    datas=[
        ('assets/logo.png', 'assets'),
    ] + fitz_datas,
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
        'fitz',
        'pymupdf',
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtPrintSupport',
    ] + fitz_hiddenimports,
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
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',   # Will be skipped gracefully if file not present
)
