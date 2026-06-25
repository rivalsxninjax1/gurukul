# gurukul.spec
# PyInstaller build spec for Gurukul CMS
# Build ONLY on Windows to produce a Windows .exe
# Command: pyinstaller gurukul.spec

import sys
import os
from PyInstaller.utils.hooks import collect_all

# ── PyMuPDF / fitz ──────────────────────────────────────────────────────────
# 'fitz' is the legacy namespace; 'pymupdf' is used in PyMuPDF >= 1.23.
# Guard the pymupdf collect so older installs don't break the build.
fitz_datas,   fitz_binaries,   fitz_hiddenimports   = collect_all('fitz')
try:
    pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = collect_all('pymupdf')
except Exception:
    pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = [], [], []

# ── Pillow ───────────────────────────────────────────────────────────────────
pil_datas, pil_binaries, pil_hiddenimports = collect_all('PIL')

# ── Icon guard ───────────────────────────────────────────────────────────────
# PyInstaller 6.x hard-errors on a missing icon file.
_icon_path = os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'assets', 'icon.ico')
_icon = _icon_path if os.path.isfile(_icon_path) else None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=fitz_binaries + pymupdf_binaries + pil_binaries,
    datas=[
        ('assets/logo.png', 'assets'),
    ] + fitz_datas + pymupdf_datas + pil_datas,
    hiddenimports=[
        # ── SQLAlchemy ────────────────────────────────────────────────────────
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.dialects.sqlite.pysqlite',
        'sqlalchemy.sql.default_comparator',
        'sqlalchemy.sql.sqltypes',
        'sqlalchemy.sql.visitors',
        'sqlalchemy.ext.declarative',
        'sqlalchemy.orm.decl_api',
        'sqlalchemy.orm.relationships',
        'sqlalchemy.event',
        'sqlalchemy.pool',

        # ── All app models (dynamically imported at runtime) ──────────────────
        'models.user',
        'models.student',
        'models.teacher',
        'models.class_group',
        'models.attendance',
        'models.attendance_raw',
        'models.subscription',
        'models.schedule',
        'models.settings',
        'models.exam',
        'models.expense',
        'models.deleted_ledger',

        # ── bcrypt ────────────────────────────────────────────────────────────
        'bcrypt',
        '_bcrypt',

        # ── pandas / numpy ────────────────────────────────────────────────────
        'pandas',
        'pandas.core.arrays.masked',
        'pandas.core.arrays.integer',
        'pandas.core.arrays.floating',
        'numpy',
        'numpy.core._multiarray_umath',
        'numpy.core._methods',

        # ── openpyxl / xlrd ───────────────────────────────────────────────────
        'openpyxl',
        'openpyxl.cell._writer',
        'openpyxl.styles.stylesheet',
        'openpyxl.drawing.image',
        'xlrd',

        # ── reportlab ─────────────────────────────────────────────────────────
        'reportlab',
        'reportlab.platypus',
        'reportlab.platypus.flowables',
        'reportlab.platypus.paragraph',
        'reportlab.platypus.tables',
        'reportlab.lib.pagesizes',
        'reportlab.lib.colors',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.pdfgen.canvas',
        'reportlab.graphics',
        'reportlab.graphics.shapes',

        # ── dateutil ──────────────────────────────────────────────────────────
        'dateutil',
        'dateutil.relativedelta',
        'dateutil.parser',
        'dateutil.tz',

        # ── PIL / Pillow ──────────────────────────────────────────────────────
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.PngImagePlugin',
        'PIL.JpegImagePlugin',

        # ── PyMuPDF ───────────────────────────────────────────────────────────
        'fitz',
        'pymupdf',

        # ── sqlite3 (used directly by backup_service) ─────────────────────────
        'sqlite3',

        # ── PyQt5 ─────────────────────────────────────────────────────────────
        'PyQt5',
        'PyQt5.QtWidgets',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtPrintSupport',
        'PyQt5.QtNetwork',
        'PyQt5.sip',

        # ── stdlib ────────────────────────────────────────────────────────────
        'shutil',
        'tempfile',
        'logging',
        'math',
        're',

    ] + fitz_hiddenimports + pymupdf_hiddenimports + pil_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.QtWebEngine',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

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
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_icon,
)
