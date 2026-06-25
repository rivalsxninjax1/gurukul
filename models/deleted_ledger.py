from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database.connection import Base


class DeletedStudentLedger(Base):
    """Preserves financial summary of deleted students.

    When a student is deleted:
    - revenue_preserved  = total amount actually paid across all their subs
    - pending_written_off = total outstanding (fee − paid) that is written off

    The dashboard adds these to its totals so revenue is never lost from
    the books and the pending amount is correctly subtracted.
    """
    __tablename__ = "deleted_student_ledger"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    student_name        = Column(String(150), nullable=False)
    student_user_id     = Column(String(50),  nullable=False)
    revenue_preserved   = Column(Float, nullable=False, default=0.0)
    pending_written_off = Column(Float, nullable=False, default=0.0)
    deleted_at          = Column(DateTime, default=func.now())
