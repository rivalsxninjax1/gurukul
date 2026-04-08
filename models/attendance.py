from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base


class Attendance(Base):
    """Student attendance — entry + exit."""
    __tablename__ = "attendance"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    date       = Column(Date, nullable=False)
    entry_time = Column(Time)
    exit_time  = Column(Time)
    status     = Column(String(20), default="Present")

    student = relationship("Student", back_populates="attendances")


class TeacherAttendance(Base):
    """Teacher attendance — entry AND exit."""
    __tablename__ = "teacher_attendance"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id  = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    date        = Column(Date, nullable=False)
    entry_time  = Column(Time)
    exit_time   = Column(Time)
    status      = Column(String(20), default="Present")
    source_file = Column(String(300))

    teacher = relationship("Teacher", back_populates="attendances")


class AttendanceLog(Base):
    """Legacy raw import log."""
    __tablename__ = "attendance_logs"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    raw_user_id  = Column(String(50))
    timestamp    = Column(String(50))
    import_batch = Column(String(100))
    error_note   = Column(String(300))