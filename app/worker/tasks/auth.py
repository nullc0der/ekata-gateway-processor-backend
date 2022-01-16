from app.utils.auth import (
    send_request_verify_email, send_forgot_password_email,
    send_two_factor_email, send_two_factor_recovery_code_regeneration_email)

from app.models.users import UserDB


async def task_send_request_verify_email(_, user: UserDB, token: str):
    return send_request_verify_email(user, token)


async def task_send_forgot_password_email(_, user: UserDB, token: str):
    return send_forgot_password_email(user, token)


async def task_send_two_factor_email(_, user: UserDB, enabled: bool):
    return send_two_factor_email(user, enabled)


async def task_send_two_factor_recovery_code_regeneration_email(
        _, user: UserDB):
    return send_two_factor_recovery_code_regeneration_email(user)
