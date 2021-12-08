from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_default_database
from app.exceptions.payment import WalletAddressCreateFailureException
from app.models.payments import Payment, PaymentCreate, PaymentCreateResponse
from app.utils.payment import verify_form_id, verify_payment_id
from app.crud import payments
from app.utils import payment as payment_utils

payment_router = APIRouter()


@payment_router.post('/create', response_model=PaymentCreateResponse)
async def create_payment(
        payment_create_data: PaymentCreate,
        db: AsyncIOMotorDatabase = Depends(get_default_database)):
    await verify_form_id(
        db, payment_create_data.project_id, payment_create_data.form_id)
    try:
        payment_create_response = await payments.create_payment(
            db, payment_create_data)
    except WalletAddressCreateFailureException:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Wallet address creation failure'
        )
    return payment_create_response


@payment_router.get('/get-payment-status', response_model=Payment)
async def get_payment_status(
        form_id: str = Query(..., alias='form-id'),
        payment_id: str = Query(..., alias='payment-id'),
        db: AsyncIOMotorDatabase = Depends(get_default_database)):
    await verify_payment_id(db, form_id, payment_id)
    return await payment_utils.get_payment_status(db, payment_id)
