from typing import List, Optional, Union
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, UUID4


class PayoutBase(BaseModel):
    currency_name: str
    amount: Decimal
    tx_ids: Union[List[str], str]
    payout_processed_for_payments: List[str]


class PayoutDB(PayoutBase):
    owner_id: UUID4
    raw_tx_data: Optional[str]


class Payout(PayoutBase):
    created_on: Optional[datetime]
