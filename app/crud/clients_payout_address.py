from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic.types import UUID4

from app.models.clients_payout_address import (
    PayoutAddress, PayoutAddressCreate,
    PayoutAddressDB, PayoutAddressUpdate
)


async def get_clients_payout_address(
        db: AsyncIOMotorDatabase,
        user_id: UUID4,
        payout_address_id: UUID4) -> Optional[PayoutAddressDB]:
    payout_address = await db.payout_address.find_one(
        {'id': payout_address_id, 'owner_id': user_id})
    if payout_address:
        return PayoutAddressDB(**payout_address)


async def get_clients_payout_addresses(
        db: AsyncIOMotorDatabase, user_id: UUID4) -> List[PayoutAddress]:
    payout_addresses: List[PayoutAddress] = []
    payout_addresses_cur = db.payout_address.find({'owner_id': user_id})
    async for payout_address in payout_addresses_cur:
        payout_addresses.append(PayoutAddress(**payout_address))
    return payout_addresses


async def create_clients_payout_address(
        db: AsyncIOMotorDatabase,
        user_id: UUID4,
        payout_address_data: PayoutAddressCreate) -> PayoutAddress:
    payout_address_data = payout_address_data.dict()
    payout_address_data['owner_id'] = user_id
    result = await db.payout_address.insert_one(
        PayoutAddressDB(**payout_address_data).dict())
    payout_address = await db.payout_address.find_one(result.inserted_id)
    return PayoutAddress(**payout_address)


async def update_clients_payout_address(
        db: AsyncIOMotorDatabase,
        payout_address_id: UUID4,
        update_data: PayoutAddressUpdate) -> PayoutAddress:
    await db.payout_address.update_one(
        {'id': payout_address_id},
        {'$set': {'payout_address': update_data.payout_address}})
    payout_address = await db.payout_address.find_one(
        {'id': payout_address_id})
    return PayoutAddress(**payout_address)


async def delete_clients_payout_address(
        db: AsyncIOMotorDatabase,
        payout_address_id: UUID4) -> str:
    payout_address = await db.payout_address.find_one(
        {'id': payout_address_id})
    await db.payout_address.delete_one({'id': payout_address_id})
    return payout_address['currency_name']
