from datetime import datetime, timezone
from typing import Optional

from backend_ide.schemas.user import User

# Заглушка БД — заменишь на реальную работу с БД
_fake_users_db = {
    "user-1": {
        "id": "user-1",
        "username": "alice",
        "assignment_deadline": datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc),
    }
}


def get_user_from_db(user_id: str) -> Optional[User]:
    data = _fake_users_db.get(user_id)
    if not data:
        return None
    return User(**data)


def is_user_deadline_over(user: User) -> bool:
    now = datetime.now(timezone.utc)
    return now > user.assignment_deadline


def seconds_left_for_user(user: User) -> int:
    now = datetime.now(timezone.utc)
    delta = user.assignment_deadline - now
    return max(int(delta.total_seconds()), 0)
