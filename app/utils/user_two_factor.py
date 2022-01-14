import random
import string
from typing import Dict, List, Tuple

from passlib.context import CryptContext


two_factor_recovery_code_ctx = CryptContext(
    schemes=['bcrypt'], deprecated='auto')


def verify_two_factor_recovery_code(
        plain_two_factor_recovery_code: str,
        hashed_two_factor_recovery_code: str) -> bool:
    return two_factor_recovery_code_ctx.verify(
        plain_two_factor_recovery_code, hashed_two_factor_recovery_code)


def hash_two_factor_recovery_code(plain_two_factor_recovery_code: str) -> str:
    return two_factor_recovery_code_ctx.hash(
        plain_two_factor_recovery_code)


def get_recovery_codes() -> Tuple[List, List[Dict]]:
    codes = []
    codes_hashed = []
    for i in range(6):
        code = ''.join(random.SystemRandom().choice(string.digits)
                       for _ in range(6))
        codes.append(code)
        codes_hashed.append({
            'used': False,
            'code': hash_two_factor_recovery_code(code)
        })
    return (codes, codes_hashed)
