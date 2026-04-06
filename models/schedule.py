from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class Schedule(Base):
    __tablename__ = "schedules"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    class_id    = Column(Integer, ForeignKey("classes.id"))
    group_id    = Column(Integer, ForeignKey("groups.id"), nullable=True)
    teacher_id  = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    day_of_week = Column(String(20), nullable=False)   # "Monday" … "Sunday"
    start_time  = Column(Time, nullable=False)
    end_time    = Column(Time, nullable=False)
    subject     = Column(String(100))

    class_   = relationship("Class")
    group    = relationship("Group")
    teacher  = relationship("Teacher")