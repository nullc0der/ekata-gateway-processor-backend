from app.models.users import UserDB
from pathlib import Path

from app.core.config import settings
from app.utils.common import send_email


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
