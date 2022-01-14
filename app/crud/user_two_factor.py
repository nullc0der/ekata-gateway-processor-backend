from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import UUID4
from pyotp.totp import TOTP
from starlette import status
from starlette.exceptions import HTTPException

from app.core.config import settings

from app.models.users import (
    UserTwoFactorCreateResponse, UserTwoFactorDB,
    UserTwoFactorResponse, UserTwoFactorUpdate, UserTwoFactorUpdateResponse)
from app.utils.user_two_factor import (
    get_recovery_codes, verify_two_factor_recovery_code)

# TODO: Send email on enable and disable and ask for password on enable/disable


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
    if TOTP(two_factor['secret_key']).verify(update_data.code):
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
        return UserTwoFactorUpdateResponse(recovery_codes=recovery_codes)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail='Invalid verification code'
    )


async def disable_user_two_factor(
        db: AsyncIOMotorDatabase,
        user_id: UUID4):
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
    two_factor_code_verified = TOTP(two_factor['secret_key']).verify(code)
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