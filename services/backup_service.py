"""
Backup and restore service for tuition_cms.db.

Uses SQLite's online backup API (sqlite3.Connection.backup()) instead of
shutil.copy2 — safe even with live SQLAlchemy connections open, guarantees
a consistent snapshot with no mid-transaction corruption.

Restore flow:
  1. Validate the chosen file is a real SQLite DB with expected tables.
  2. Auto-save a safety snapshot of the current DB before overwriting.
  3. Dispose SQLAlchemy engine so no file handles are held open.
  4. Atomic swap: write to a temp file beside the DB, then os.replace().
  5. Report success; caller must restart the app for the engine to reconnect.
"""

import sqlite3
import os
import shutil
import tempfile
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Resolve DB path the same way database/connection.py does ─────────────────
# connection.py uses a bare relative path "tuition_cms.db", which resolves
# relative to the process CWD.  We mirror that exactly.
_DB_FILENAME = "tuition_cms.db"

# Tables that must exist in any valid backup file
_REQUIRED_TABLES = {
    "students", "teachers", "classes", "groups",
    "attendance", "teacher_attendance", "student_subscriptions",
    "subscription_payments", "users", "settings",
}


def _resolve_db_path() -> str:
    """Return the absolute path to the live database."""
    return os.path.abspath(_DB_FILENAME)


def _validate_backup_file(path: str) -> tuple[bool, str]:
    """
    Check that `path` is a valid SQLite database containing the expected
    core tables.  Returns (ok: bool, message: str).
    """
    if not os.path.isfile(path):
        return False, "File does not exist."
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        ic = conn.execute("PRAGMA integrity_check").fetchone()
        if ic[0] != "ok":
            conn.close()
            return False, f"SQLite integrity check failed: {ic[0]}"
        tables = {
            r[0] for r in
            conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        missing = _REQUIRED_TABLES - tables
        if missing:
            return False, (
                f"File is missing expected tables: {', '.join(sorted(missing))}.\n"
                "This may not be a Gurukul backup."
            )
        return True, "ok"
    except sqlite3.DatabaseError as exc:
        return False, f"Not a valid SQLite database: {exc}"
    except Exception as exc:
        return False, f"Validation error: {exc}"


def backup_database(destination_dir: str) -> str:
    """
    Create a consistent snapshot of the live database using SQLite's
    online backup API.  Safe with live connections open.

    Returns the full path of the created backup file.
    Raises RuntimeError on failure.
    """
    db_path = _resolve_db_path()
    if not os.path.isfile(db_path):
        raise RuntimeError(f"Database not found at: {db_path}")

    os.makedirs(destination_dir, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gurukul_backup_{ts}.db"
    dest     = os.path.join(destination_dir, filename)

    try:
        src_conn = sqlite3.connect(db_path)
        dst_conn = sqlite3.connect(dest)
        src_conn.backup(dst_conn, pages=100)   # 100-page chunks, non-blocking
        dst_conn.close()
        src_conn.close()
    except Exception as exc:
        # Clean up partial file if it was created
        if os.path.exists(dest):
            try:
                os.remove(dest)
            except OSError:
                pass
        raise RuntimeError(f"Backup failed: {exc}") from exc

    # Quick integrity check on the backup we just made
    ok, msg = _validate_backup_file(dest)
    if not ok:
        try:
            os.remove(dest)
        except OSError:
            pass
        raise RuntimeError(f"Backup written but failed validation: {msg}")

    logger.info(f"Database backed up → {dest}")
    return dest


def restore_database(source_path: str) -> tuple[bool, str]:
    """
    Restore the database from `source_path`.

    Steps:
      1. Validate the source file.
      2. Auto-snapshot the current DB as a safety net.
      3. Dispose the SQLAlchemy engine (release file handles).
      4. Atomically swap in the new DB via a temp file + os.replace().

    Returns (success: bool, message: str).
    The caller is responsible for restarting / re-initialising the app.
    """
    db_path = _resolve_db_path()

    # ── Step 1: validate source ───────────────────────────────────────────────
    ok, msg = _validate_backup_file(source_path)
    if not ok:
        return False, f"Cannot restore — invalid backup file:\n{msg}"

    # ── Step 2: auto-snapshot current DB as safety net ────────────────────────
    safety_backup = None
    if os.path.isfile(db_path):
        try:
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe = os.path.join(
                os.path.dirname(db_path),
                f"gurukul_pre_restore_safety_{ts}.db"
            )
            src_conn = sqlite3.connect(db_path)
            dst_conn = sqlite3.connect(safe)
            src_conn.backup(dst_conn, pages=100)
            dst_conn.close()
            src_conn.close()
            safety_backup = safe
            logger.info(f"Safety snapshot before restore → {safe}")
        except Exception as exc:
            logger.warning(f"Could not create safety snapshot: {exc}")

    # ── Step 3: dispose SQLAlchemy engine ─────────────────────────────────────
    try:
        from database.connection import engine
        engine.dispose()
        logger.info("SQLAlchemy engine disposed before restore.")
    except Exception as exc:
        logger.warning(f"Could not dispose engine: {exc}")

    # ── Step 4: atomic restore via temp file + os.replace() ──────────────────
    db_dir   = os.path.dirname(db_path)
    tmp_path = None
    try:
        # Write the restored DB to a temp file in the same directory first
        fd, tmp_path = tempfile.mkstemp(dir=db_dir, suffix=".db.tmp")
        os.close(fd)

        src_conn = sqlite3.connect(source_path)
        dst_conn = sqlite3.connect(tmp_path)
        src_conn.backup(dst_conn, pages=100)
        dst_conn.close()
        src_conn.close()

        # Atomic swap — on POSIX this is truly atomic; on Windows it's
        # best-effort (os.replace overwrites the target in one step)
        os.replace(tmp_path, db_path)
        tmp_path = None   # consumed — don't try to delete it

        logger.info(f"Database restored from {source_path} → {db_path}")
        msg = "Database restored successfully."
        if safety_backup:
            msg += f"\n\nA safety snapshot of your previous data was saved to:\n{safety_backup}"
        return True, msg

    except Exception as exc:
        logger.error(f"Restore failed: {exc}")
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        hint = ""
        if safety_backup:
            hint = f"\n\nYour original data is safe at:\n{safety_backup}"
        return False, f"Restore failed: {exc}{hint}"
