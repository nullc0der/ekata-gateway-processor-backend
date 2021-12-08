from typing import Union

from motor.motor_asyncio import AsyncIOMotorDatabase
from starlette.exceptions import HTTPException
from starlette import status

from app.models.projects import (ProjectCreate, ProjectUpdate)
from app.models.users import User
from app.crud import clients_payout_address


async def check_payout_address_added(
        db: AsyncIOMotorDatabase,
        user: User, project_data: Union[ProjectCreate, ProjectUpdate]):
    if project_data.enabled_currency:
        clients_payout_addresses = \
            await clients_payout_address.get_clients_payout_addresses(
                db, user.id)
        available_payout_addresses = [
            i.currency_name for i in clients_payout_addresses]
        for i in project_data.enabled_currency:
            if i not in available_payout_addresses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{i}'s payment address is not added"
                )
