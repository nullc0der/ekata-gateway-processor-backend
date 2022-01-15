from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, Depends
from starlette.exceptions import HTTPException
from starlette import status

from app.db import get_default_database
from app.models.users import (
    UserDB, UserTwoFactorCreateResponse,
    UserTwoFactorResponse, UserTwoFactorUpdateResponse,
    UserTwoFactorUpdate, UserTwoFactorCreate, UserTwoFactorDelete)
from app.crud import user_two_factor
from app.api.api_v1.dependencies.auth.auth import current_active_verified_user
from app.permissions import auth as auth_permissions
from app.utils.auth import verify_user_password

two_factor_router = APIRouter()


@two_factor_router.get('', response_model=UserTwoFactorResponse)
async def get_two_factor_state(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: UserDB = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    return await user_two_factor.get_user_two_factor_state(db, user.id)


@two_factor_router.post('', response_model=UserTwoFactorCreateResponse)
async def create_user_two_factor(
        create_data: UserTwoFactorCreate,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: UserDB = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    if not verify_user_password(create_data.password, user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid Password'
        )
    return await user_two_factor.create_user_two_factor(db, user.id)


@two_factor_router.patch('', response_model=UserTwoFactorUpdateResponse)
async def enable_user_two_factor(
        update_data: UserTwoFactorUpdate,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: UserDB = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    return await user_two_factor.enable_user_two_factor(
        db, user.id, update_data)


@two_factor_router.delete('')
async def disable_user_two_factor(
        delete_data: UserTwoFactorDelete,
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: UserDB = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    if not verify_user_password(delete_data.password, user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid Password'
        )
    await user_two_factor.disable_user_two_factor(db, user.id)


@two_factor_router.post(
    '/get-new-recovery-codes', response_model=UserTwoFactorUpdateResponse)
async def get_new_recovery_codes(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: UserDB = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    return await user_two_factor.regenerate_two_factor_recovery_codes(
        db, user.id)
