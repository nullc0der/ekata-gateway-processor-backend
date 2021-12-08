from typing import Any

from starlette import status
from starlette.exceptions import HTTPException

from app.models.users import User


def is_user_is_client(user: User):
    if not user.is_client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not enough permission'
        )


def is_user_is_owner_of_obj(
        user: User, obj: Any, field_to_check: str = 'owner_id'):
    if user.id != getattr(obj, field_to_check):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Not enough permission'
        )
