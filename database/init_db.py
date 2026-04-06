from database.connection import engine, Base
from models import (
    user, class_group, student, teacher,
    attendance, attendance_raw,
    subscription, schedule, settings, exam
)


def initialize_database():
    Base.metadata.create_all(bind=engine)
    _migrate_teacher_attendance()
    _seed_settings()
    _seed_default_admin()
    print("✅ Database initialized.")


def _migrate_teacher_attendance():
    """Add exit_time and status columns to teacher_attendance if missing."""
    from sqlalchemy import text
    with engine.connect() as conn:
        # Check existing columns
        result = conn.execute(
            text("PRAGMA table_info(teacher_attendance)")
        )
        cols = [row[1] for row in result]

        if "exit_time" not in cols:
            conn.execute(
                text("ALTER TABLE teacher_attendance ADD COLUMN exit_time TIME")
            )
            print("✅ Migrated: added exit_time to teacher_attendance")

        if "status" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE teacher_attendance "
                    "ADD COLUMN status VARCHAR(20) DEFAULT 'Present'"
                )
            )
            print("✅ Migrated: added status to teacher_attendance")

        conn.commit()


def _seed_settings():
    from database.connection import get_session
    from models.settings import Setting
    session = get_session()
    defaults = {
        "attendance_threshold": "75",
        "default_fee":          "2000",
        "centre_name":          "Tuition Centre",
        "centre_phone":         "",
        "centre_address":       "",
    }
    for key, value in defaults.items():
        if not session.query(Setting).filter_by(key=key).first():
            session.add(Setting(key=key, value=value))
    session.commit()
    session.close()


def _seed_default_admin():
    from database.connection import get_session
    from models.user import User
    import bcrypt
    session = get_session()
    if not session.query(User).filter_by(username="admin").first():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        session.add(User(
            username="admin",
            password=hashed.decode(),
            role="admin"
        ))
        session.commit()
    session.close()