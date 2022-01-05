import json
import secrets
import hmac
import hashlib
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Union, List, Tuple
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic.types import UUID4
from starlette.exceptions import HTTPException
from starlette import status

from app.core.config import settings
from app.models.payments import Payment, PaymentUpdate
from app.utils.api_key import verify_and_update_api_key
from app.utils.daemon_api_wrapper import daemon_api_wrapper_manager
from app.utils.daemon_api_wrapper.monero import from_atomic
from app.utils.daemon_api_wrapper.baza import from_atomic as baza_from_atomic
from app.redis import redis_manager
from app.crud import payments as payments_crud
from app.constants.payment import (
    TX_FIELDS_TO_CHECK, TX_FIELDS_TO_SAVE, CRYPTO_ATOMIC)
from app.constants.payment_status import PaymentStatus
from app.worker import arq_manager


async def verify_form_id(
        db: AsyncIOMotorDatabase, project_id: UUID4, form_id: str):
    form = await db.payment_forms.find_one({'id': form_id})
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested form not found'
        )
    if form['related_project_id'] != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Project and form id mismatch'
        )


async def verify_project(
        db: AsyncIOMotorDatabase, project_id: UUID4, api_key: str):
    project = await db.projects.find_one({'id': project_id})
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested project not found'
        )
    verified, updated_api_key = verify_and_update_api_key(
        api_key, project['api_key_hashed'])
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='API key mismatch'
        )
    if verified and updated_api_key:
        await db.projects.update_one(
            {'id': project['id']},
            {'$set': {'api_key_hashed': updated_api_key}}
        )
    if not project['enabled_currency']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Project have no enabled currency'
        )


async def verify_payment_id(
        db: AsyncIOMotorDatabase, form_id: str, payment_id: str):
    payment_form = await db.payment_forms.find_one({'id': form_id})
    payment = await db.payments.find_one({'payment_id': payment_id})
    if not payment_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested form_id not found'
        )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Requested payment not found'
        )
    if payment_form['related_project_id'] != payment['related_project_id']:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Project id mismatch'
        )


async def get_unique_payment_id(db: AsyncIOMotorDatabase) -> str:
    payment_id = secrets.token_urlsafe(16)
    if await db.payments.find_one({'payment_id': payment_id}):
        return await get_unique_payment_id(db)
    return payment_id


def get_wallet_address(currency_name: str) -> Optional[Union[Dict, str]]:
    api_wrapper = daemon_api_wrapper_manager.api_wrappers[currency_name]
    wallet_address = api_wrapper.get_new_address()
    return wallet_address


def check_payment_valid(payment_results: List, currency_name: str) -> bool:
    fields = TX_FIELDS_TO_CHECK[currency_name]
    for payment_result in payment_results:
        for field in fields:
            if not payment_result.get(field):
                return False
            if currency_name != 'baza':
                if not payment_result['confirmations'] >= \
                        settings.dict()[
                        f'{currency_name.upper()}_MIN_CONFIRMATION_NEEDED']:
                    return False
    return True


def convert_payment_amount(
        amount: Union[float, int],
        currency_name: str) -> Decimal:
    if currency_name == 'monero':
        return from_atomic(amount).quantize(CRYPTO_ATOMIC, ROUND_HALF_UP)
    if currency_name == 'baza':
        return baza_from_atomic(amount).quantize(CRYPTO_ATOMIC, ROUND_HALF_UP)
    return Decimal(amount).quantize(CRYPTO_ATOMIC, ROUND_HALF_UP)


def compare_payment_address(
        payment_result: Dict, wallet_address: str, currency_name: str) -> bool:
    if currency_name == 'baza':
        for transfer in payment_result['transfers']:
            if transfer['address'] != wallet_address:
                return False
            return True
    return payment_result['address'] == wallet_address


def get_payment_amount_and_txid(
        payment_results: List,
        currency_name: str, wallet_address: str) -> Tuple[Decimal, List]:
    fields = TX_FIELDS_TO_SAVE[currency_name]
    amount = Decimal('0')
    txids_list = []
    for payment_result in payment_results:
        if compare_payment_address(
                payment_result, wallet_address, currency_name):
            if currency_name == 'baza':
                for transfer in payment_result[fields[0]]:
                    amount += convert_payment_amount(
                        transfer['amount'], currency_name)
            else:
                amount += convert_payment_amount(
                    payment_result[fields[0]], currency_name)
            txids = payment_result.get(fields[1])
            if isinstance(txids, list):
                txids_list += txids
            else:
                txids_list.append(txids)
    return (amount, txids_list)


async def get_payment_status(
        db: AsyncIOMotorDatabase, payment_id: str) -> Payment:
    payment = await payments_crud.get_payment(db, payment_id)
    if payment.amount_received.compare(payment.amount_requested)\
            == Decimal('-1'):
        api_wrapper = \
            daemon_api_wrapper_manager.api_wrappers[payment.currency_name]
        result = api_wrapper.list_transactions(
            payment.wallet_address
            if payment.currency_name != 'monero'
            else payment.monero_account_index)
        if result and payment.currency_name == 'baza':
            result = result['transactions']
        if result and check_payment_valid(result, payment.currency_name):
            amount, txids = get_payment_amount_and_txid(
                result, payment.currency_name, payment.wallet_address)
            if txids != payment.tx_ids:
                payment_status = PaymentStatus.PENDING
                if amount > payment.amount_requested:
                    payment_status = PaymentStatus.OVERPAID
                if amount == payment.amount_requested:
                    payment_status = PaymentStatus.FULFILLED
                payment_update_data = PaymentUpdate(
                    amount_received=amount,
                    tx_ids=txids,
                    raw_tx_data=json.dumps(result),
                    status=payment_status
                )
                await payments_crud.update_payment(
                    db, payment_id, payment_update_data)
    payment = await db.payments.find_one({'payment_id': payment_id})
    if payment['status'] != PaymentStatus.PENDING:
        payment_signature = await create_payment_signature(db, payment)
        await arq_manager.pool.enqueue_job(
            'task_send_payment_data_to_webhook',
            payment['payment_id'],
            payment_signature)
        await arq_manager.pool.enqueue_job(
            'task_add_payment_to_payout_queue',
            payment['payment_id']
        )
        return Payment(
            **payment,
            signature=payment_signature,
            created_on=ObjectId(payment['_id']).generation_time)
    return Payment(
        **payment, created_on=ObjectId(payment['_id']).generation_time)


async def create_payment_signature(
        db: AsyncIOMotorDatabase, payment: Dict):
    project = await db.projects.find_one(
        {'id': payment['related_project_id']})
    message = f"{payment['payment_id']}" + \
              f"{payment['wallet_address']}{payment['currency_name']}"
    return hmac.new(
        project['payment_signature_secret'].encode(),
        message.encode(), hashlib.sha256).hexdigest()


async def get_currency_price(currency_name: str) -> Optional[Decimal]:
    """
        This function will get a currency's price in atomic value of a fiat
        currency
    """
    currency_prices = await redis_manager.redis_client.get(
        'currency_price', encoding='utf-8')
    currency_prices = json.loads(currency_prices)
    if currency_prices:
        currency_price = currency_prices[currency_name].get('usd') * 100
        if currency_price:
            return Decimal(1 / currency_price)
