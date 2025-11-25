from fastapi import APIRouter, Depends

from backend_ide.schemas.user import User
from backend_ide.api.deps import get_current_user
from backend_ide.services.user_service import seconds_left_for_user

router = APIRouter()


@router.get("/me")
async def read_me(user: User = Depends(get_current_user)):
    """
    Ручка для проверки токена и получения инфы о пользователе.
    Заодно показывает, сколько времени осталось на выполнение задач.
    """
    return {
        "id": user.id,
        "username": user.username,
        "assignment_deadline": user.assignment_deadline,
        "seconds_left": seconds_left_for_user(user),
    }
