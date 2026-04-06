from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class Exam(Base):
    __tablename__ = "exams"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=func.now())

    subjects = relationship(
        "ExamSubject",
        back_populates="exam",
        cascade="all, delete"
    )
    results = relationship(
        "StudentResult",
        back_populates="exam",
        cascade="all, delete"
    )


class ExamSubject(Base):
    __tablename__ = "exam_subjects"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    exam_id      = Column(Integer, ForeignKey("exams.id"), nullable=False)
    subject_name = Column(String(150), nullable=False)
    full_marks   = Column(Float, nullable=False, default=100)
    pass_marks   = Column(Float, nullable=False, default=40)

    exam    = relationship("Exam", back_populates="subjects")
    results = relationship(
        "StudentResult",
        back_populates="subject",
        cascade="all, delete"
    )


class StudentResult(Base):
    __tablename__ = "student_results"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    exam_id    = Column(Integer, ForeignKey("exams.id"),    nullable=False)
    subject_id = Column(Integer, ForeignKey("exam_subjects.id"), nullable=False)
    marks      = Column(Float, nullable=False, default=0)

    student = relationship("Student", back_populates="results")
    exam    = relationship("Exam",    back_populates="results")
    subject = relationship("ExamSubject", back_populates="results")