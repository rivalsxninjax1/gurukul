import shutil
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
DB_PATH = "tuition_cms.db"


def backup_database(destination_dir: str) -> str:
    os.makedirs(destination_dir, exist_ok=True)
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tuition_cms_backup_{ts}.db"
    dest     = os.path.join(destination_dir, filename)
    shutil.copy2(DB_PATH, dest)
    logger.info(f"Database backed up to {dest}")
    return dest


def restore_database(source_path: str) -> bool:
    try:
        shutil.copy2(source_path, DB_PATH)
        logger.info(f"Database restored from {source_path}")
        return True
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        return False