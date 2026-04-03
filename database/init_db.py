from database.connection import engine, Base
# Import all models so Base knows about them
from models import student, teacher, class_group, attendance, billing, user

def initialize_database():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully.")