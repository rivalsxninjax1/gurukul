import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


def _get_db_path() -> str:
    """
    Returns absolute path to tuition_cms.db.
    Works in:
      - Mac/Windows development: next to main.py
      - PyInstaller .exe: in user's Documents/GurukulCMS folder
        (the .exe is read-only inside its bundle, so DB must live outside)
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle — store DB in user's Documents
        docs = os.path.join(
            os.path.expanduser("~"), "Documents", "GurukulCMS"
        )
        os.makedirs(docs, exist_ok=True)
        return os.path.join(docs, "tuition_cms.db")
    else:
        # Development — store next to main.py (project root)
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(root, "tuition_cms.db")


_DB_PATH = _get_db_path()

engine = create_engine(
    f"sqlite:///{_DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    return SessionLocal()
