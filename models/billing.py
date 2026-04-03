from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base

class Billing(Base):
    __tablename__ = "billing"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    amount     = Column(Float, nullable=False)
    due_date   = Column(Date)
    paid       = Column(String(10), default="Unpaid")  # Paid / Unpaid
    note       = Column(String(300))

    student = relationship("Student", back_populates="bills")