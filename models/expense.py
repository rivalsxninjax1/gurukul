from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from database.connection import Base


class Expense(Base):
    __tablename__ = "expenses"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    title       = Column(String(200), nullable=False)
    amount      = Column(Float, nullable=False)
    date        = Column(Date, nullable=False)
    description = Column(String(500))
    created_at  = Column(DateTime, default=func.now())