from sqlalchemy import Column, Integer, String, Date
from database.connection import Base

class Teacher(Base):
    __tablename__ = "teachers"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), unique=True, nullable=False)
    name    = Column(String(150), nullable=False)
    phone   = Column(String(20))
    address = Column(String(300))
    subject = Column(String(100))
    join_date = Column(Date)