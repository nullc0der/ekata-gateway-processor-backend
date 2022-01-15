import sentry_sdk
from arq import create_pool, cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.worker.tasks import auth, payment, payout
from app.redis import redis_manager
from app.db import mongo_manager
from app.db import get_default_database
from app.utils.daemon_api_wrapper import daemon_api_wrapper_manager


async def startup(ctx):
    await mongo_manager.connect_to_database()
    await redis_manager.connect_to_redis()
    daemon_api_wrapper_manager.initialize_api_wrappers()
    ctx['db'] = await get_default_database()
    ctx['redis_client'] = redis_manager.redis_client
    if settings.SITE_TYPE != 'local':
        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)


async def shutdown(ctx):
    await mongo_manager.disconnect_from_database()
    await redis_manager.disconnect_from_redis()


class ARQManager(object):
    pool = None

    async def init_pool(self):
        self.pool = await create_pool(
            RedisSettings(settings.REDIS_HOST, settings.REDIS_PORT))


class WorkerSettings:
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT)
    functions = [
        auth.task_send_request_verify_email,
        auth.task_send_forgot_password_email,
        auth.task_send_two_factor_email,
        payment.task_send_payment_data_to_webhook,
        payout.task_create_clients_payout_queue,
        payout.task_add_payment_to_payout_queue
    ]
    cron_jobs = [
        cron(
            payment.task_sync_currency_price,
            minute=set(i for i in range(0, 60) if i % 5 == 0),
            run_at_startup=True
        ),
        cron(
            payout.task_clear_payout_queue,
            minute={0, 30}
        )
    ]
    on_startup = startup
    on_shutdown = shutdown


arq_manager = ARQManager()
