from fastapi import APIRouter, HTTPException, status, Query
from fastapi.param_functions import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_default_database
from app.models.payment_form import (
    FormInfo, PaymentFormCreate, PaymentFormResponse)
from app.utils.payment import verify_project
from app.crud import payment_form

payment_form_router = APIRouter()


@payment_form_router.post('/create', response_model=PaymentFormResponse)
async def create_payment_form(
        payment_form_create_data: PaymentFormCreate,
        db: AsyncIOMotorDatabase = Depends(get_default_database)):
    await verify_project(
        db, payment_form_create_data.project_id,
        payment_form_create_data.api_key)
    return await payment_form.create_payment_form(db, payment_form_create_data)


@payment_form_router.get('/get-form-info', response_model=FormInfo)
async def get_form_info(
        form_id: str = Query(..., alias='form-id'),
        db: AsyncIOMotorDatabase = Depends(get_default_database)):
    form = await db.payment_forms.find_one({'id': form_id})
    if not form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Payment form not found'
        )
    return form
