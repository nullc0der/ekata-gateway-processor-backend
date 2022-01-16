from pathlib import Path
from passlib.context import CryptContext

from app.models.users import UserDB
from app.core.config import settings
from app.utils.common import send_email


password_ctx = CryptContext(
    schemes=['bcrypt'], deprecated='auto')


def send_request_verify_email(user: UserDB, token: str):
    with open(Path(settings.EMAIL_TEMPLATE_DIR) /
              "auth/request_verify_email.html") as f:
        html_template = f.read()
    send_email(
        email_to=user.email, email_from='gatewayprocessor@ekata.io',
        email_from_name='Ekata Gateway Processor',
        subject_template='Verify Email',
        html_template=html_template,
        environment={
            'useremail': user.email,
            'link': f'{settings.CLIENT_FRONTEND}/verify-email/{token}'
        }
    )


def send_forgot_password_email(user: UserDB, token: str):
    with open(Path(settings.EMAIL_TEMPLATE_DIR) /
              "auth/forgot_password.html") as f:
        html_template = f.read()
    send_email(
        email_to=user.email, email_from='gatewayprocessor@ekata.io',
        email_from_name='Ekata Gateway Processor',
        subject_template='Forgot Password',
        html_template=html_template,
        environment={
            'useremail': user.email,
            'link': f'{settings.CLIENT_FRONTEND}/reset-password/{token}'
        }
    )


def verify_user_password(password: str, user: UserDB):
    return password_ctx.verify(password, user.hashed_password)


def send_two_factor_email(user: UserDB, enabled: bool):
    with open(Path(settings.EMAIL_TEMPLATE_DIR) /
              'auth/two_factor.html') as f:
        html_template = f.read()
    send_email(
        email_to=user.email, email_from='gatewayprocessor@ekata.io',
        email_from_name='Ekata Gateway Processor',
        subject_template=f"Two factor {'enabled' if enabled else 'disabled'}",
        html_template=html_template,
        environment={
            'useremail': user.email,
            'enabled': enabled
        }
    )


def send_two_factor_recovery_code_regeneration_email(user: UserDB):
    with open(Path(settings.EMAIL_TEMPLATE_DIR) /
              'auth/two_factor_recovery_code_regeneration.html') as f:
        html_template = f.read()
    send_email(
        email_to=user.email, email_from='gatewayprocessor@ekata.io',
        email_from_name='Ekata Gateway Processor',
        subject_template="Two factor recovery code regenerated",
        html_template=html_template,
        environment={
            'useremail': user.email,
        }
    )
