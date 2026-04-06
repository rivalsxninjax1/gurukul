from sqlalchemy import (
    Column, Integer, String, Float, Date,
    ForeignKey, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class StudentSubscription(Base):
    __tablename__ = "student_subscriptions"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    student_id     = Column(Integer, ForeignKey("students.id"), nullable=False)
    start_date     = Column(Date, nullable=False)
    end_date       = Column(Date, nullable=False)
    total_fee      = Column(Float, nullable=False, default=0.0)
    status         = Column(String(20), default="active")  # active / expired
    created_at     = Column(DateTime, default=func.now())

    student  = relationship("Student", back_populates="subscriptions")
    payments = relationship(
        "SubscriptionPayment",
        back_populates="subscription",
        cascade="all, delete"
    )


class SubscriptionPayment(Base):
    __tablename__ = "subscription_payments"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    student_id     = Column(Integer, ForeignKey("students.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("student_subscriptions.id"), nullable=False)
    amount_paid    = Column(Float, nullable=False)
    payment_date   = Column(Date, nullable=False)
    payment_method = Column(String(50), default="Cash")
    note           = Column(String(300))
    created_at     = Column(DateTime, default=func.now())

    student      = relationship("Student", back_populates="payments")
    subscription = relationship("StudentSubscription", back_populates="payments")