from typing import Dict
import uuid

from pydantic import BaseModel, validator
from pydantic.fields import Field
from pydantic.types import UUID4

from app.core.config import settings
from app.utils.daemon_api_wrapper import daemon_api_wrapper_manager


class PayoutAddressBase(BaseModel):
    currency_name: str
    payout_address: str

    @validator("payout_address")
    def validate_payout_address(cls, v: str):
        if not v:
            raise ValueError("Payout address can't be empty")
        return v

    @validator("currency_name", pre=True)
    def validate_currency_name(cls, v: str):
        if v not in settings.ALLOWED_CURRENCY_NAME:
            raise ValueError(f"Currency name {v} is not allowed")
        return v


class PayoutAddressCreate(PayoutAddressBase):
    @validator("payout_address")
    def validate_payout_address(cls, v: str, values: Dict):
        if not v:
            raise ValueError("Payout address can't be empty")
        currency_name = values.get('currency_name')
        api_wrapper = daemon_api_wrapper_manager.api_wrappers.get(
            currency_name)
        if not api_wrapper:
            raise ValueError("Invalid payout address")
        if not api_wrapper.validate_address(v):
            raise ValueError("Invalid payout address")
        return v


class PayoutAddressUpdate(PayoutAddressBase):
    @validator("payout_address")
    def validate_payout_address(cls, v: str, values: Dict):
        if not v:
            raise ValueError("Payout address can't be empty")
        currency_name = values.get('currency_name')
        api_wrapper = daemon_api_wrapper_manager.api_wrappers.get(
            currency_name)
        if not api_wrapper:
            raise ValueError("Invalid payout address")
        if not api_wrapper.validate_address(v):
            raise ValueError("Invalid payout address")
        return v


class PayoutAddressDB(PayoutAddressBase):
    owner_id: UUID4
    id: UUID4 = Field(default_factory=uuid.uuid4)

    class Config:
        orm_mode = True


class PayoutAddress(PayoutAddressBase):
    id: UUID4
