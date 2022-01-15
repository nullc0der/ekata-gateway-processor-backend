from typing import List, Optional, Dict
from datetime import datetime

from pyotp import random_base32

from pydantic import validator, BaseModel, UUID4, Field
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


class UserTwoFactorBase(BaseModel):
    is_enabled: bool = False


class UserTwoFactorDB(UserTwoFactorBase):
    owner_id: UUID4
    recovery_codes_hashed: Optional[List[Dict]]
    secret_key: str = Field(default_factory=random_base32)


class UserTwoFactorUpdate(BaseModel):
    code: int


class UserTwoFactorCreate(BaseModel):
    password: str


class UserTwoFactorDelete(UserTwoFactorCreate):
    pass


class UserTwoFactorResponse(UserTwoFactorBase):
    pass


class UserTwoFactorCreateResponse(BaseModel):
    provisioning_uri: str


class UserTwoFactorUpdateResponse(BaseModel):
    recovery_codes: List
