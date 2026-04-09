"""Simple in-memory user session helper."""

_CURRENT_USER: str | None = None


def set_current_user(username: str):
    global _CURRENT_USER
    _CURRENT_USER = username


def get_current_user() -> str | None:
    return _CURRENT_USER


def clear_current_user():
    global _CURRENT_USER
    _CURRENT_USER = None
