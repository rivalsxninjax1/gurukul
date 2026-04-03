from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base

class Student(Base):
    __tablename__ = "students"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String(50), unique=True, nullable=False)  # for attendance matching
    name       = Column(String(150), nullable=False)
    dob        = Column(Date)
    phone      = Column(String(20))
    address    = Column(String(300))
    join_date  = Column(Date)
    photo_path = Column(String(300))
    class_id   = Column(Integer, ForeignKey("classes.id"))
    group_id   = Column(Integer, ForeignKey("groups.id"))

    class_      = relationship("Class", back_populates="students")
    group       = relationship("Group", back_populates="students")
    attendances = relationship("Attendance", back_populates="student")
    bills       = relationship("Billing", back_populates="student")