from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.payment_form import (
    PaymentFormDB, PaymentFormCreate, PaymentFormResponse)


async def create_payment_form(
        db: AsyncIOMotorDatabase,
        payment_form_create_data: PaymentFormCreate) -> PaymentFormResponse:
    result = await db.payment_forms.insert_one(
        PaymentFormDB(
            **payment_form_create_data.dict(),
            related_project_id=payment_form_create_data.project_id
        ).dict()
    )
    payment_form = await db.payment_forms.find_one({'_id': result.inserted_id})
    return PaymentFormResponse(
        **payment_form,
        created_on=ObjectId(payment_form['_id']).generation_time)


async def get_payment_form(
        db: AsyncIOMotorDatabase, form_id: str) -> PaymentFormDB:
    payment_form = await db.payment_forms.find_one({'id': form_id})
    return PaymentFormDB(**payment_form)
