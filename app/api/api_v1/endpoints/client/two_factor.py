from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, Depends

from app.db import get_default_database
from app.models.users import (
    User, UserTwoFactorCreateResponse,
    UserTwoFactorResponse, UserTwoFactorUpdateResponse,
    UserTwoFactorUpdate)
from app.crud import user_two_factor
from app.api.api_v1.dependencies.auth.auth import current_active_verified_user
from app.permissions import auth as auth_permissions

two_factor_router = APIRouter()


@two_factor_router.get('', response_model=UserTwoFactorResponse)
async def get_two_factor_state(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    return await user_two_factor.get_user_two_factor_state(db, user.id)


@two_factor_router.post('', response_model=UserTwoFactorCreateResponse)
async def create_user_two_factor(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    return await user_two_factor.create_user_two_factor(db, user.id)


@two_factor_router.patch('', response_model=UserTwoFactorUpdateResponse)
async def enable_user_two_factor(
        update_data: UserTwoFactorUpdate,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    return await user_two_factor.enable_user_two_factor(
        db, user.id, update_data)


@two_factor_router.delete('')
async def disable_user_two_factor(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    await user_two_factor.disable_user_two_factor(db, user.id)


@two_factor_router.post(
    '/get-new-recovery-codes', response_model=UserTwoFactorUpdateResponse)
async def get_new_recovery_codes(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    return await user_two_factor.regenerate_two_factor_recovery_codes(
        db, user.id)
