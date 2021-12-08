from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb_manager import MongoManager


mongo_manager = MongoManager()


async def get_default_database() -> Optional[AsyncIOMotorDatabase]:
    return mongo_manager.database
