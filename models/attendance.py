from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base

class Attendance(Base):
    __tablename__ = "attendance"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date       = Column(Date, nullable=False)
    entry_time = Column(Time)
    exit_time  = Column(Time)
    status     = Column(String(20), default="Present")
    # Status: Present / Absent / Incomplete

    student = relationship("Student", back_populates="attendances")

class AttendanceLog(Base):
    """Raw import log — every row from Excel stored here."""
    __tablename__ = "attendance_logs"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    raw_user_id = Column(String(50))
    timestamp  = Column(String(50))  # stored as raw string from Excel
    import_batch = Column(String(100))  # filename + date
    error_note = Column(String(300))   # if unknown ID etc.