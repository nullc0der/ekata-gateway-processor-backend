from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, validator, UUID4

from app.core.config import settings
from app.constants.payment_status import PaymentStatus


class PaymentBase(BaseModel):
    currency_name: str

    @validator("currency_name")
    def validate_currency_name(cls, v: str):
        if v not in settings.ALLOWED_CURRENCY_NAME:
            raise ValueError(f"Currency name {v} is not allowed")
        return v


class PaymentCreate(PaymentBase):
    project_id: UUID4
    form_id: str


class PaymentCreateResponse(PaymentBase):
    payment_id: str
    wallet_address: str
    amount_requested: Decimal


class Payment(PaymentBase):
    payment_id: str
    wallet_address: str
    amount_requested: Decimal
    amount_received: Optional[Decimal]
    tx_ids: Optional[List[str]]
    created_on: Optional[datetime]
    status: PaymentStatus
    form_id: str
    signature: Optional[str]


class PaymentDB(PaymentBase):
    payment_id: str
    wallet_address: str
    related_project_id: UUID4
    amount_requested: Decimal
    amount_received: Decimal = Decimal('0')
    tx_ids: Optional[List[str]]
    raw_tx_data: Optional[str]
    monero_account_index: Optional[int]
    status: PaymentStatus = PaymentStatus.PENDING
    form_id: str

    class Config:
        orm_mode = True


class PaymentUpdate(BaseModel):
    amount_received: Optional[Decimal]
    tx_ids: Optional[List[str]]
    raw_tx_data: Optional[str]
    status: Optional[PaymentStatus]
