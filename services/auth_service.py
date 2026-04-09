import bcrypt
from database.connection import get_session
from models.user import User

def create_default_admin():
    """Run once at startup — creates admin if not exists."""
    session = get_session()
    existing = session.query(User).filter_by(username="admin").first()
    if not existing:
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        admin = User(username="admin", password=hashed.decode(), role="admin")
        session.add(admin)
        session.commit()
        print("✅ Default admin created. Username: admin | Password: admin123")
    session.close()

def verify_login(username: str, password: str) -> bool:
    session = get_session()
    user = session.query(User).filter_by(username=username).first()
    session.close()
    if not user:
        return False
    return bcrypt.checkpw(password.encode(), user.password.encode())


def change_password(username: str, old_password: str,
                    new_password: str) -> tuple[bool, str]:
    session = get_session()
    user = session.query(User).filter_by(username=username).first()
    if not user:
        session.close()
        return False, "User not found."
    if not bcrypt.checkpw(old_password.encode(), user.password.encode()):
        session.close()
        return False, "Old password is incorrect."
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    user.password = hashed.decode()
    session.commit()
    session.close()
    return True, "Password updated successfully."
