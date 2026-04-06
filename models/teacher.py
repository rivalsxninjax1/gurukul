from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from database.connection import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    user_id   = Column(String(50), unique=True, nullable=False)
    name      = Column(String(150), nullable=False)
    phone     = Column(String(20))
    address   = Column(String(300))
    subject   = Column(String(100))
    join_date = Column(Date)

    attendances = relationship(
        "TeacherAttendance",
        back_populates="teacher",
        cascade="all, delete"
    )