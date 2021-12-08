from typing import Tuple
from passlib.context import CryptContext


api_key_ctx = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verify_and_update_api_key(
        plain_api_key: str, hashed_api_key: str) -> Tuple[bool, str]:
    return api_key_ctx.verify_and_update(plain_api_key, hashed_api_key)


def hash_api_key(plain_api_key: str) -> str:
    return api_key_ctx.hash(plain_api_key)
