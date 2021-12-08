import secrets
from typing import Optional, List

from datetime import datetime

from pydantic import BaseModel, UUID4, Field, validator, AnyHttpUrl

from app.core.config import settings


class PaymentFormBase(BaseModel):
    amount_requested: int
    fiat_currency: str

    @validator("fiat_currency")
    def validate_fiat_currency(cls, v: str):
        if v.lower() not in settings.ALLOWED_FIAT_CURRENCY:
            raise ValueError(f"Currency name {v} is not allowed")
        return v.lower()


class PaymentFormDB(PaymentFormBase):
    id: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    related_project_id: UUID4


class PaymentFormCreate(PaymentFormBase):
    project_id: UUID4
    api_key: str


class PaymentFormResponse(BaseModel):
    id: str
    created_on: datetime


class FormInfo(PaymentFormBase):
    id: str


class ProjectInfo(BaseModel):
    id: UUID4
    enabled_currency: Optional[List[str]]
    domain_name: Optional[AnyHttpUrl]
