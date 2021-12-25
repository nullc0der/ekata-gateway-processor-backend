from bson import ObjectId
from typing import Optional, Dict
from decimal import Decimal, ROUND_HALF_UP

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic.types import UUID4
from pymongo import DESCENDING

from app.exceptions.payment import WalletAddressCreateFailureException
from app.models.payments import (
    Payment, PaymentCreate, PaymentCreateResponse,
    PaymentDB, PaymentUpdate)
from app.utils.payment import (
    get_currency_price, get_wallet_address, get_unique_payment_id)
from app.constants.payment import CRYPTO_ATOMIC


async def get_projects_payments(
        db: AsyncIOMotorDatabase, project_id: UUID4,
        limit: int = 5, page_number: int = 1,
        search: str = '', currency_name: str = '') -> Dict:
    payments = []
    skip = 0
    if not search and not currency_name:
        skip = limit * (page_number - 1)
    query = {'related_project_id': project_id}
    if search:
        query['$or'] = [
            {'payment_id': search},
            {'tx_ids': {'$all': [search]}}
        ]
    if currency_name:
        query['currency_name'] = currency_name
    payments_cur = db.payments.find(query).skip(
        skip).limit(limit).sort('_id', DESCENDING)
    async for payment in payments_cur:
        payments.append(
            Payment(
                **payment,
                created_on=ObjectId(payment['_id']).generation_time
            )
        )
    if page_number == 1:
        return {
            "payments": payments,
            "total_payments": await db.payments.count_documents(
                {'related_project_id': project_id})
        }
    return {
        "payments": payments
    }


async def get_payment(db: AsyncIOMotorDatabase, payment_id: str) -> PaymentDB:
    payment = await db.payments.find_one({'payment_id': payment_id})
    return PaymentDB(**payment)


async def create_payment(
        db: AsyncIOMotorDatabase,
        payment_create_data: PaymentCreate) -> Optional[PaymentCreateResponse]:
    currency_name = payment_create_data.currency_name
    wallet_address = get_wallet_address(currency_name)
    payment_id = await get_unique_payment_id(db)
    if not wallet_address:
        raise WalletAddressCreateFailureException()
    payment_create_data = payment_create_data.dict()
    payment_form = await db.payment_forms.find_one(
        {'id': payment_create_data['form_id']})
    amount_requested = Decimal(
        payment_form['amount_requested']
        * await get_currency_price(payment_create_data['currency_name']))\
        .quantize(CRYPTO_ATOMIC, ROUND_HALF_UP)
    await db.payments.insert_one(
        PaymentDB(
            **payment_create_data,
            amount_requested=amount_requested,
            payment_id=payment_id,
            wallet_address=wallet_address
            if currency_name != 'monero' else wallet_address['address'],
            related_project_id=payment_create_data['project_id'],
            monero_account_index=None
            if currency_name != 'monero' else wallet_address['account_index']
        ).dict()
    )
    return PaymentCreateResponse(
        **payment_create_data,
        payment_id=payment_id,
        wallet_address=wallet_address
        if currency_name != 'monero' else wallet_address['address'],
        amount_requested=amount_requested
    )


async def update_payment(
        db: AsyncIOMotorDatabase, payment_id: str,
        payment_update_data: PaymentUpdate):
    await db.payments.update_one(
        {'payment_id': payment_id}, {'$set': payment_update_data.dict()})
