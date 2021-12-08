from logging.config import dictConfig

import sentry_sdk
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from app.core.config import settings
from app.db import mongo_manager
from app.api.api_v1.api import api_router
from app.worker import arq_manager
from app.redis import redis_manager
# from app.utils.daemon_api_wrapper import daemon_api_wrapper_manager


dictConfig(settings.LOGGING_CONFIG)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f'{settings.API_V1_STR}/openapi.json'
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin)
                       for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if settings.SITE_TYPE != 'local':
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)
    app.add_middleware(SentryAsgiMiddleware)


@app.on_event("startup")
async def startup():
    await mongo_manager.connect_to_database()
    await arq_manager.init_pool()
    await redis_manager.connect_to_redis()
    # daemon_api_wrapper_manager.initialize_api_wrappers()


@app.on_event("shutdown")
async def shutdown():
    await mongo_manager.disconnect_from_database()
    await redis_manager.disconnect_from_redis()

app.include_router(api_router, prefix=settings.API_V1_STR)
