from typing import List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import UUID4
from pymongo import DESCENDING

from app.models.payout import Payout


async def get_clients_payouts(
        db: AsyncIOMotorDatabase, user_id: UUID4) -> List[Payout]:
    payouts = []
    payout_cur = db.payouts.find(
        {'owner_id': user_id}).sort('_id', DESCENDING)
    async for payout in payout_cur:
        payouts.append(
            Payout(
                **payout,
                created_on=ObjectId(payout['_id']).generation_time
            )
        )
    return payouts
