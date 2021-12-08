import secrets
import urllib
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseSettings, AnyHttpUrl, validator


class Settings(BaseSettings):
    API_V1_STR: str = '/api/v1'
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24  # 1 Day
    PROJECT_NAME: str
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    TIMEZONE: str = 'UTC'
    CLIENT_FRONTEND: AnyHttpUrl
    SITE_TYPE: str

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(
            cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Logging
    LOGGER_NAME: str = "ekata-gateway-processor-backend"
    LOG_FORMAT: str = "%(levelprefix)s %(message)s"
    LOG_LEVEL: str = "DEBUG"
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",

            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            LOGGER_NAME: {"handlers": ["default"], "level": LOG_LEVEL},
        },
    }

    @validator("LOGGER_NAME", pre=True)
    def populate_logger_name(cls, v: str, values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return values.get('PROJECT_NAME')

    # Database
    MONGO_HOST: str
    MONGO_PORT: str
    MONGO_USER: str
    MONGO_PASS: str
    MONGO_DB: str
    MONGO_URL: Optional[str] = None

    @validator("MONGO_USER", pre=True)
    def quote_mongo_username(cls, v: str):
        return urllib.parse.quote_plus(v)

    @validator("MONGO_PASS", pre=True)
    def quote_mongo_password(cls, v: str):
        return urllib.parse.quote_plus(v)

    @validator("MONGO_URL", pre=True)
    def assemble_db_connection(
            cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return f'mongodb://{values.get("MONGO_USER")}' + \
            f':{values.get("MONGO_PASS")}@{values.get("MONGO_HOST")}' + \
            f':{values.get("MONGO_PORT")}/{values.get("MONGO_DB")}'

    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_TEMPLATE_DIR: Optional[str] = "app/email_templates/"

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int

    # Currency supported
    ALLOWED_CURRENCY_NAME: List[str] = ['bitcoin', 'dogecoin', 'monero']
    ALLOWED_FIAT_CURRENCY: List[str] = ['usd']

    # Bitcoin
    BITCOIN_DAEMON_HOST: str
    BITCOIN_WALLET_RPC_USERNAME: str
    BITCOIN_WALLET_RPC_PASSWORD: str
    BITCOIN_WALLET_NAME: str
    BITCOIN_MIN_CONFIRMATION_NEEDED: int

    # Dogecoin
    # DOGECOIN_DAEMON_HOST: str
    # DOGECOIN_WALLET_RPC_USERNAME: str
    # DOGECOIN_WALLET_RPC_PASSWORD: str
    # DOGECOIN_MIN_CONFIRMATION_NEEDED: int

    # Monero
    # MONERO_DAEMON_HOST: str
    # MONERO_WALLET_RPC_USERNAME: str
    # MONERO_WALLET_RPC_PASSWORD: str
    # MONERO_MIN_CONFIRMATION_NEEDED: int
    # MONERO_WALLET_NAME: str
    # MONERO_WALLET_PASSWORD: str

    # Sentry
    SENTRY_DSN: AnyHttpUrl


settings = Settings()
