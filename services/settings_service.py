from database.connection import get_session
from models.settings import Setting


def get_setting(key: str, default: str = "") -> str:
    session = get_session()
    s = session.query(Setting).filter_by(key=key).first()
    session.close()
    return s.value if s else default


def set_setting(key: str, value: str):
    session = get_session()
    s = session.query(Setting).filter_by(key=key).first()
    if s:
        s.value = value
    else:
        session.add(Setting(key=key, value=value))
    session.commit()
    session.close()


def get_all_settings() -> dict:
    session = get_session()
    rows = session.query(Setting).all()
    result = {r.key: r.value for r in rows}
    session.close()
    return result