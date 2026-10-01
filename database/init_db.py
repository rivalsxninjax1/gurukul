from database.connection import engine, Base
from models import (
    user, class_group, student, teacher,
    attendance, attendance_raw,
    subscription, schedule, settings, exam, expense,
    deleted_ledger,
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

        # students.monthly_fee — added for Nepali-month auto billing.
        # Existing students get their latest subscription fee as monthly
        # fee. A backup of the database is taken first.
        if "monthly_fee" not in st_cols:
            _backup_db_before_migration()
            conn.execute(
                text("ALTER TABLE students ADD COLUMN monthly_fee FLOAT")
            )
            conn.execute(text("""
                UPDATE students SET monthly_fee = (
                    SELECT total_fee FROM student_subscriptions ss
                    WHERE ss.student_id = students.id
                    ORDER BY ss.start_date DESC, ss.id DESC LIMIT 1
                )
                WHERE monthly_fee IS NULL
            """))
            conn.commit()
            print("✅ Migration: students.monthly_fee (backfilled)")

        # deleted_student_ledger — added in v1.3
        res = conn.execute(
            text("SELECT name FROM sqlite_master "
                 "WHERE type='table' AND name='deleted_student_ledger'")
        )
        if not res.fetchone():
            conn.execute(text("""
                CREATE TABLE deleted_student_ledger (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name        VARCHAR(150) NOT NULL,
                    student_user_id     VARCHAR(50)  NOT NULL,
                    revenue_preserved   FLOAT NOT NULL DEFAULT 0.0,
                    pending_written_off FLOAT NOT NULL DEFAULT 0.0,
                    deleted_at          DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ Migration: deleted_student_ledger table created")
        # Any punch recorded means the student was present. Incomplete
        # was used before the status logic was corrected.
        result = conn.execute(
            text("UPDATE attendance SET status = 'Present' "
                 "WHERE status = 'Incomplete'")
        )
        if result.rowcount:
            print(f"✅ Migration: {result.rowcount} Incomplete "
                  "attendance records → Present")
        conn.commit()


def _backup_db_before_migration():
    """Copy the SQLite file next to itself before a data-changing migration."""
    import os, shutil, datetime
    from database.connection import _DB_PATH
    try:
        if os.path.isfile(_DB_PATH):
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = f"{_DB_PATH}.before_monthly_fee_{stamp}.bak"
            shutil.copy2(_DB_PATH, dest)
            print(f"✅ Backup before migration: {dest}")
    except Exception as exc:  # never block start-up because of a backup
        print(f"⚠ Could not create pre-migration backup: {exc}")


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