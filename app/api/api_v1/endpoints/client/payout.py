from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import APIRouter, Depends

from app.models.payout import Payout
from app.models.users import User
from app.crud import clients_payout
from app.db import get_default_database
from app.permissions import auth as auth_permissions
from app.api.api_v1.dependencies.auth.auth import current_active_verified_user

payouts_router = APIRouter()


@payouts_router.get('', response_model=List[Payout])
async def get_clients_payouts(
        db: AsyncIOMotorDatabase = Depends(get_default_database),
        user: User = Depends(current_active_verified_user)):
    auth_permissions.is_user_is_client(user)
    return await clients_payout.get_clients_payouts(db, user.id)
