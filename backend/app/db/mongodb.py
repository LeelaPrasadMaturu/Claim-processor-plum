from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from ..config import get_settings

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def init_db() -> None:
    global _client, _database
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _database = _client[settings.database_name]
    
    await _database.claims.create_index("claim_id", unique=True)
    await _database.claims.create_index("member_id")
    await _database.claims.create_index("created_at")


async def close_db() -> None:
    global _client
    if _client:
        _client.close()


def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _database
