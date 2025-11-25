from fastapi import Header, HTTPException, status, Depends

from backend_ide.core.security import decode_jwt_token
from backend_ide.schemas.user import User
from backend_ide.services.user_service import (
    get_user_from_db,
    is_user_deadline_over,
)


async def get_current_user(
    authorization: str = Header(...),
) -> User:
    """
    Достаём пользователя из JWT.
    Ожидаем заголовок:
        Authorization: Bearer <jwt>
    В payload токена ожидается `sub` = user_id.
    """
    scheme, _, param = authorization.partition(" ")
    if scheme.lower() != "bearer" or not param:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Нужно передать Bearer JWT токен в заголовке Authorization",
        )

    payload = decode_jwt_token(param)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="В токене нет user_id (sub)",
        )

    user = get_user_from_db(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    if is_user_deadline_over(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Время на выполнение задач уже истекло",
        )

    return user
