from database.connection import engine, Base
from models import (
    user, class_group, student, teacher,
    attendance, attendance_raw,
    subscription, schedule, settings, exam, expense
)


def initialize_database():
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    _seed_settings()
    _seed_default_admin()
    print("✅ Database initialized.")


def _run_migrations():
    """Safe additive migrations only."""
    from sqlalchemy import text
    with engine.connect() as conn:

        # teacher_attendance
        res = conn.execute(
            text("PRAGMA table_info(teacher_attendance)")
        )
        ta_cols = [r[1] for r in res.fetchall()]
        if "exit_time" not in ta_cols:
            conn.execute(
                text("ALTER TABLE teacher_attendance "
                     "ADD COLUMN exit_time TIME")
            )
            print("✅ Migration: teacher_attendance.exit_time")
        if "status" not in ta_cols:
            conn.execute(
                text("ALTER TABLE teacher_attendance "
                     "ADD COLUMN status VARCHAR(20) DEFAULT 'Present'")
            )
            print("✅ Migration: teacher_attendance.status")

        # students
        res = conn.execute(text("PRAGMA table_info(students)"))
        st_cols = [r[1] for r in res.fetchall()]
        if "guardian_name" not in st_cols:
            conn.execute(
                text("ALTER TABLE students "
                     "ADD COLUMN guardian_name VARCHAR(150)")
            )
            print("✅ Migration: students.guardian_name")
        if "whatsapp_number" not in st_cols:
            conn.execute(
                text("ALTER TABLE students "
                     "ADD COLUMN whatsapp_number VARCHAR(20)")
            )
            print("✅ Migration: students.whatsapp_number")

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