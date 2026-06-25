import logging
import os
import sys


def _get_log_dir() -> str:
    """Return the correct log directory for both dev and packaged (.exe) runs."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller .exe — write logs beside the database
        base = os.path.join(
            os.path.expanduser("~"), "Documents", "GurukulCMS", "logs"
        )
    else:
        # Development — write logs next to main.py
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base = os.path.join(root, "logs")
    os.makedirs(base, exist_ok=True)
    return base


def setup_logger():
    log_dir  = _get_log_dir()
    log_file = os.path.join(log_dir, "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
