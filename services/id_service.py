"""
Auto-generates unique IDs for students and teachers.
Students: numeric  1001, 1002, 1003 …
Teachers: T101, T102, T103 …
"""
from database.connection import get_session
from models.student import Student
from models.teacher import Teacher


def generate_student_id() -> str:
    session = get_session()
    existing = session.query(Student.user_id).all()
    session.close()

    numeric = []
    for (uid,) in existing:
        try:
            numeric.append(int(uid))
        except (ValueError, TypeError):
            pass

    if not numeric:
        return "1001"
    return str(max(numeric) + 1)


def generate_teacher_id() -> str:
    session = get_session()
    existing = session.query(Teacher.user_id).all()
    session.close()

    numeric = []
    for (uid,) in existing:
        if isinstance(uid, str) and uid.startswith("T"):
            try:
                numeric.append(int(uid[1:]))
            except ValueError:
                pass

    if not numeric:
        return "T101"
    return f"T{max(numeric) + 1}"