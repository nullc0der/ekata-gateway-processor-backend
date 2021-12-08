from app.utils.auth import (
    send_request_verify_email, send_forgot_password_email)

from app.models.users import UserDB


async def task_send_request_verify_email(_, user: UserDB, token: str):
    return send_request_verify_email(user, token)


async def task_send_forgot_password_email(_, user: UserDB, token: str):
    return send_forgot_password_email(user, token)
