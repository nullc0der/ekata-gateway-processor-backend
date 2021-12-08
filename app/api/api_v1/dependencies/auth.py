from typing import Optional, Union

from fastapi import Depends, Request
from fastapi_users import (
    BaseUserManager, InvalidPasswordException, FastAPIUsers, password)
from fastapi_users.db import MongoDBUserDatabase
from fastapi_users.authentication import JWTAuthentication

from app.core.config import settings
from app.models.users import User, UserCreate, UserDB, UserUpdate
from app.db import get_default_database
from app.worker import arq_manager


class UserManager(BaseUserManager[UserCreate, UserDB]):
    user_db_model = UserDB
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def update(
            self,
            user_update: UserUpdate,
            user: UserDB,
            safe: bool = False,
            request: Optional[Request] = None) -> UserDB:
        if user_update.password:
            verified, _ = password.verify_and_update_password(
                user_update.current_password, user.hashed_password)
            if not verified:
                raise InvalidPasswordException(
                    reason="Current password not matching")
        if user_update.current_password:
            del user_update.current_password
        return await super().update(
            user_update, user, safe=safe, request=request)

    async def validate_password(
            self, password: str, user: Union[UserCreate, UserDB]) -> None:
        # TODO: Add some password validation logic, like min length,
        # common password, special chars, uppercase, lowercase,
        # no other user info in password, numbers etc
        if not password:
            raise InvalidPasswordException(
                reason='Empty password is not allowed')

    async def on_after_register(
            self, user: UserDB, request: Optional[Request] = None):
        await self.request_verify(user, request)

    async def on_after_forgot_password(
            self, user: UserDB, token: str, request: Optional[Request] = None):
        await arq_manager.pool.enqueue_job(
            'task_send_forgot_password_email', user, token)

    async def on_after_request_verify(
            self, user: UserDB, token: str, request: Optional[Request] = None):
        await arq_manager.pool.enqueue_job(
            'task_send_request_verify_email', user, token)


def get_user_db(db=Depends(get_default_database)):
    users_collection = db.users
    yield MongoDBUserDatabase(UserDB, users_collection)


def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


jwt_authentication = JWTAuthentication(
    settings.SECRET_KEY,
    lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    tokenUrl='api/v1/auth/jwt/login'
)


fastapi_users = FastAPIUsers(
    get_user_manager,
    [jwt_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB
)

current_active_user = fastapi_users.current_user(active=True)
current_active_verified_user = fastapi_users.current_user(
    active=True, verified=True)

# TODO: Enhancement: Do authentication in middleware
#  with permission check if possible
