from typing import Tuple, Optional, Union

from motor.motor_asyncio import AsyncIOMotorDatabase

from fastapi import (
    APIRouter, Depends, HTTPException, Response, status, Request)

from fastapi_users import (
    BaseUserManager, InvalidPasswordException,
    FastAPIUsers as BaseFastAPIUsers, password,
    models)
from fastapi_users.router.common import ErrorCode, ErrorModel
from fastapi_users.openapi import OpenAPIResponseType
from fastapi_users.authentication import (
    AuthenticationBackend, Authenticator, Strategy,
    BearerTransport, JWTStrategy)
from fastapi_users.db import MongoDBUserDatabase
from fastapi_users.manager import UserManagerDependency

from app.api.api_v1.dependencies.auth.login_form import LoginForm
from app.core.config import settings
from app.models.users import User, UserCreate, UserDB, UserUpdate
from app.db import get_default_database
from app.worker import arq_manager
from app.constants.auth_errors import AuthErrors
from app.crud.user_two_factor import (
    get_user_two_factor_state, verify_two_factor_code)


class UserManager(BaseUserManager[UserCreate, UserDB]):
    user_db_model = UserDB
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def authenticate(
        self, credentials: LoginForm,
        db: AsyncIOMotorDatabase) -> \
            Tuple[Optional[models.UD], bool, bool]:
        user = await super().authenticate(credentials)
        if user:
            two_factor_state = await get_user_two_factor_state(db, user.id)
            two_factor_verified = False
            if two_factor_state.is_enabled and credentials.two_factor_code:
                two_factor_verified = await verify_two_factor_code(
                    db, user.id, credentials.two_factor_code)
            return (user, two_factor_state.is_enabled, two_factor_verified)
        return (None, False, False)

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


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS
    )


def get_auth_router(
    backend: AuthenticationBackend,
    get_user_manager: UserManagerDependency[models.UC, models.UD],
    authenticator: Authenticator,
    requires_verification: bool = False,
) -> APIRouter:
    """Generate a router with login/logout
     routes for an authentication backend."""
    router = APIRouter()
    get_current_user_token = authenticator.current_user_token(
        active=True, verified=requires_verification
    )

    login_responses: OpenAPIResponseType = {
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorModel,
            "content": {
                "application/json": {
                    "examples": {
                        ErrorCode.LOGIN_BAD_CREDENTIALS: {
                            "summary":
                            "Bad credentials or the user is inactive.",
                            "value": {
                                "detail": ErrorCode.LOGIN_BAD_CREDENTIALS
                            },
                        },
                        ErrorCode.LOGIN_USER_NOT_VERIFIED: {
                            "summary": "The user is not verified.",
                            "value":
                            {"detail": ErrorCode.LOGIN_USER_NOT_VERIFIED},
                        },
                        AuthErrors.REQUIRED_2FA_CODE: {
                            "summary": "User need to provide 2FA code.",
                            "value": {
                                "detail": AuthErrors.REQUIRED_2FA_CODE
                            }
                        }
                    }
                }
            },
        },
        **backend.transport.get_openapi_login_responses_success(),
    }

    @router.post(
        "/login",
        name=f"auth:{backend.name}.login",
        responses=login_responses,
    )
    async def login(
        response: Response,
        credentials: LoginForm = Depends(),
        user_manager: BaseUserManager[models.UC,
                                      models.UD] = Depends(get_user_manager),
        strategy: Strategy[models.UC, models.UD] = Depends(
            backend.get_strategy),
        db: AsyncIOMotorDatabase = Depends(get_default_database)
    ):
        user, user_has_two_factor_enabled, verified_two_factor =\
            await user_manager.authenticate(credentials, db)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
            )
        if requires_verification and not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
            )
        if user and user_has_two_factor_enabled and not verified_two_factor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=AuthErrors.REQUIRED_2FA_CODE
            )
        return await backend.login(strategy, user, response)

    logout_responses: OpenAPIResponseType = {
        **{
            status.HTTP_401_UNAUTHORIZED: {
                "description": "Missing token or inactive user."
            }
        },
        **backend.transport.get_openapi_logout_responses_success(),
    }

    @router.post(
        "/logout",
        name=f"auth:{backend.name}.logout", responses=logout_responses
    )
    async def logout(
        response: Response,
        user_token: Tuple[models.UD, str] = Depends(get_current_user_token),
        strategy: Strategy[models.UC, models.UD] = Depends(
            backend.get_strategy),
    ):
        user, token = user_token
        return await backend.logout(strategy, user, token, response)

    return router


class FastAPIUsers(BaseFastAPIUsers):
    def get_auth_router(
            self, backend: AuthenticationBackend,
            requires_verification: bool = False) -> APIRouter:
        return get_auth_router(
            backend,
            self.get_user_manager,
            self.authenticator,
            requires_verification,
        )


bearer_transport = BearerTransport(tokenUrl='api/v1/auth/jwt/login')

auth_backend = AuthenticationBackend(
    name='jwt', transport=bearer_transport, get_strategy=get_jwt_strategy)

fastapi_users = FastAPIUsers(
    get_user_manager,
    [auth_backend],
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
