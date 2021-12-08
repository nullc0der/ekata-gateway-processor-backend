import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
from app.db.type_registry import type_registry

logger = logging.getLogger(settings.LOGGER_NAME)


class MongoManager(object):
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

    async def connect_to_database(self):
        logger.info("Connecting to mongodb...")
        self.client = AsyncIOMotorClient(
            settings.MONGO_URL,
            uuidRepresentation="standard",
            type_registry=type_registry,
            tz_aware=True
        )
        await self.client.server_info()
        self.database = self.client.get_default_database()
        logger.info("Connected to mongodb")

    async def disconnect_from_database(self):
        logger.info("Disconnecting from mongodb...")
        self.client.close()
        logger.info("Disconnected from mongodb")
