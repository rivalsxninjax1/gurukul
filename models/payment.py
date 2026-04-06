from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class Payment(Base):
    __tablename__ = "payments"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    student_id     = Column(Integer, ForeignKey("students.id"), nullable=False)
    amount_paid    = Column(Float, nullable=False)
    payment_date   = Column(Date, nullable=False)
    payment_method = Column(String(50), default="Cash")  # Cash / Bank / Online
    note           = Column(String(300))
    created_at     = Column(DateTime, default=func.now())

    student = relationship("Student", back_populates="payments")