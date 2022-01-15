from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import UUID4
from pyotp.totp import TOTP
from starlette import status
from starlette.exceptions import HTTPException

from app.core.config import settings

from app.models.users import (
    UserTwoFactorCreateResponse, UserTwoFactorDB,
    UserTwoFactorResponse, UserTwoFactorUpdate, UserTwoFactorUpdateResponse,
    UserDB)
from app.utils.user_two_factor import (
    get_recovery_codes, verify_two_factor_recovery_code)
from app.worker import arq_manager

# TODO: Send email on enable and disable and ask for password on enable/disable
# , code is not getting scanned in dark mode sometime, need to give user
# one more code time window, service worker fix, text changes and copy in
# a well, close button and disable click outside, hint for recovery code


async def get_user_two_factor_state(
        db: AsyncIOMotorDatabase, user_id: UUID4) -> UserTwoFactorResponse:
    two_factor = await db.user_two_factor.find_one({'owner_id': user_id})
    if two_factor and two_factor['is_enabled']:
        return UserTwoFactorResponse(is_enabled=True)
    return UserTwoFactorResponse(is_enabled=False)


async def create_user_two_factor(
        db: AsyncIOMotorDatabase,
        user_id: UUID4) -> UserTwoFactorCreateResponse:
    two_factor = await db.user_two_factor.find_one({'owner_id': user_id})
    user = await db.users.find_one({'id': user_id})
    if not two_factor:
        result = await db.user_two_factor.insert_one(
            UserTwoFactorDB(owner_id=user['id']).dict())
        two_factor = await db.user_two_factor.find_one(result.inserted_id)
    return UserTwoFactorCreateResponse(
        provisioning_uri=TOTP(
            two_factor['secret_key']
        ).provisioning_uri(
            name=user['email'],
            issuer_name=settings.CLIENT_FRONTEND
        )
    )


async def enable_user_two_factor(
        db: AsyncIOMotorDatabase,
        user_id: UUID4,
        update_data: UserTwoFactorUpdate) -> UserTwoFactorUpdateResponse:
    two_factor = await db.user_two_factor.find_one({'owner_id': user_id})
    if TOTP(two_factor['secret_key']).verify(update_data.code, valid_window=1):
        recovery_codes, recovery_codes_hashed = get_recovery_codes()
        await db.user_two_factor.update_one(
            {'owner_id': user_id},
            {
                '$set': {
                    'recovery_codes_hashed': recovery_codes_hashed,
                    'is_enabled': True
                }
            }
        )
        user = await db.users.find_one({'id': user_id})
        await arq_manager.pool.enqueue_job(
            'task_send_two_factor_email', UserDB(**user), True)
        return UserTwoFactorUpdateResponse(recovery_codes=recovery_codes)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Invalid verification code'
    )


async def disable_user_two_factor(
        db: AsyncIOMotorDatabase,
        user_id: UUID4):
    user = await db.users.find_one({'id': user_id})
    await arq_manager.pool.enqueue_job(
        'task_send_two_factor_email', UserDB(**user), False)
    await db.user_two_factor.delete_one({'owner_id': user_id})


async def regenerate_two_factor_recovery_codes(
        db: AsyncIOMotorDatabase,
        user_id: UUID4) -> UserTwoFactorUpdateResponse:
    recovery_codes, recovery_codes_hashed = get_recovery_codes()
    await db.user_two_factor.update_one(
        {'owner_id': user_id},
        {
            '$set': {
                'recovery_codes_hashed': recovery_codes_hashed,
            }
        }
    )
    return UserTwoFactorUpdateResponse(recovery_codes=recovery_codes)


async def verify_two_factor_code(
        db: AsyncIOMotorDatabase, user_id: UUID4, code: int) -> bool:
    two_factor = await db.user_two_factor.find_one({'owner_id': user_id})
    two_factor_code_verified = TOTP(
        two_factor['secret_key']).verify(code, valid_window=1)
    if not two_factor_code_verified:
        recovery_codes_hashed = two_factor['recovery_codes_hashed']
        for recovery_code_hashed in recovery_codes_hashed:
            if not recovery_code_hashed['used']:
                two_factor_code_verified = verify_two_factor_recovery_code(
                    str(code), recovery_code_hashed['code'])
                if two_factor_code_verified:
                    recovery_code_hashed['used'] = True
                    break
        if two_factor_code_verified:
            await db.user_two_factor.update_one(
                {'owner_id': user_id},
                {
                    '$set': {
                        'recovery_codes_hashed': recovery_codes_hashed,
                    }
                }
            )
    return two_factor_code_verified
