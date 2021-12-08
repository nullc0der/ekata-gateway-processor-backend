import logging

import aioredis

from app.core.config import settings

logger = logging.getLogger(settings.LOGGER_NAME)


class RedisManager(object):
    redis_client = None

    async def connect_to_redis(self):
        logger.info("Connecting to redis...")
        self.redis_client = await aioredis.create_redis_pool(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1")

    async def disconnect_from_redis(self):
        logger.info("Disconnecting from redis...")
        self.redis_client.close()
        await self.redis_client.wait_closed()
