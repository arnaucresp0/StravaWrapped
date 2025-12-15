# src/user_context.py

from typing import Optional

# User context active (only for local / testing)
_active_user: Optional[dict] = None


def set_active_user(athlete_id: int, access_token: str):
    global _active_user
    _active_user = {
        "athlete_id": athlete_id,
        "access_token": access_token
    }


def get_active_user() -> dict:
    if not _active_user:
        raise RuntimeError("No active user. Authenticate first.")
    return _active_user
