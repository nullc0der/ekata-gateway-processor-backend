from fastapi import APIRouter

from app.api.api_v1.dependencies.auth import fastapi_users, jwt_authentication


auth_router = APIRouter()

auth_router.include_router(
    fastapi_users.get_auth_router(
        jwt_authentication, requires_verification=True), prefix='/jwt')
auth_router.include_router(fastapi_users.get_register_router())
auth_router.include_router(fastapi_users.get_reset_password_router())
auth_router.include_router(fastapi_users.get_verify_router())
