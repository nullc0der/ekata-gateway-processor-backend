from enum import Enum


class AuthErrors(str, Enum):
    REQUIRED_2FA_CODE = 'REQUIRED_2FA_CODE'
