from typing import Optional
from datetime import datetime

from pydantic import validator
from fastapi_users import models


class User(models.BaseUser):
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    joined_on: datetime = datetime.utcnow()
    is_client: bool = True


class UserCreate(models.BaseUserCreate):
    username: str
    first_name: Optional[str]
    last_name: Optional[str]

    @validator("username")
    def validate_username(cls, v: str):
        if not v:
            raise ValueError("Username cannot be empty")
        return v


class UserUpdate(models.CreateUpdateDictModel):
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    current_password: Optional[str]
    password: Optional[str]
    is_active: Optional[bool]
    is_superuser: Optional[bool]
    is_verified: Optional[bool]

    class Config:
        min_anystr_length = 1


class UserDB(User, models.BaseUserDB):
    pass
