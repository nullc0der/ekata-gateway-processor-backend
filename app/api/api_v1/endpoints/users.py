from fastapi import APIRouter

from app.api.api_v1.dependencies.auth.auth import fastapi_users

users_router = APIRouter()

users_router.include_router(
    fastapi_users.get_users_router(requires_verification=True))
