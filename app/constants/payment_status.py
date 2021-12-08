from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = 'PENDING'
    FULFILLED = 'FULFILLED'
    OVERPAID = 'OVERPAID'
