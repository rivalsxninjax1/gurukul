from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from database.connection import Base


class AttendanceRawLog(Base):
    """Every row from every Excel import — raw, untouched."""
    __tablename__ = "attendance_logs_raw"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(String(50), nullable=False)
    timestamp   = Column(String(50), nullable=False)
    source_file = Column(String(300))
    imported_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "timestamp", name="uq_raw_user_ts"),
    )


class UnmatchedAttendanceLog(Base):
    """user_ids that had no matching student/teacher."""
    __tablename__ = "unmatched_attendance_logs"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    user_id   = Column(String(50))
    timestamp = Column(String(50))
    reason    = Column(String(200))