from sqlalchemy import Column, Integer, String
from database.connection import Base


class Setting(Base):
    __tablename__ = "settings"

    id    = Column(Integer, primary_key=True, autoincrement=True)
    key   = Column(String(100), unique=True, nullable=False)
    value = Column(String(500), nullable=False)