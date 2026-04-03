from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.connection import Base

class Class(Base):
    __tablename__ = "classes"

    id   = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

    groups   = relationship("Group", back_populates="class_", cascade="all, delete")
    students = relationship("Student", back_populates="class_")

class Group(Base):
    __tablename__ = "groups"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    name     = Column(String(100), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)

    class_   = relationship("Class", back_populates="groups")
    students = relationship("Student", back_populates="group")