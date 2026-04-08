"""
Dynamic logo path helper.
Works in both development and PyInstaller packaged (.exe) environments.

Usage:
    from utils.logo_helper import get_logo_path, logo_pixmap
    
    path = get_logo_path()          # str path to logo.png
    pix  = logo_pixmap(64, 64)      # QPixmap scaled to size
"""

import os
import sys


def get_project_root() -> str:
    """
    Return the project root directory.
    Works in:
      - Normal Python execution: directory containing this file's parent
      - PyInstaller .exe: sys._MEIPASS (temp extraction folder)
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return sys._MEIPASS
    # Running as normal Python — go up from utils/ to project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_logo_path() -> str:
    """
    Return absolute path to assets/logo.png.
    Falls back gracefully if file doesn't exist.
    """
    root = get_project_root()
    path = os.path.join(root, "assets", "logo.png")
    return path


def logo_exists() -> bool:
    """Return True if logo.png is present."""
    return os.path.isfile(get_logo_path())


def logo_pixmap(width: int = 48, height: int = 48):
    """
    Return a QPixmap of the logo scaled to (width, height).
    Returns None if logo file doesn't exist.
    Preserves aspect ratio, smooth transformation.
    """
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtCore import Qt

    path = get_logo_path()
    if not os.path.isfile(path):
        return None
    pix = QPixmap(path)
    if pix.isNull():
        return None
    return pix.scaled(
        width, height,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )


def logo_for_reportlab(max_width_pt: float = 60,
                        max_height_pt: float = 60):
    """
    Return a reportlab Image object for use in PDFs.
    Returns None if logo doesn't exist.
    max_width_pt / max_height_pt are in points (1 pt = 1/72 inch).
    """
    path = get_logo_path()
    if not os.path.isfile(path):
        return None
    try:
        from reportlab.platypus import Image as RLImage
        from PIL import Image as PILImage

        # Measure actual image dimensions to preserve aspect ratio
        with PILImage.open(path) as img:
            w_px, h_px = img.size

        ratio = min(max_width_pt / w_px, max_height_pt / h_px)
        return RLImage(path, width=w_px * ratio, height=h_px * ratio)
    except Exception:
        return None