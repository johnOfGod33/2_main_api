from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from .config import settings


async def start_up_mongodb(app: FastAPI) -> None:
    try:
        app.client = AsyncIOMotorClient(settings.MONGODB_URI)
        app.db = app.client[settings.MONGODB_DB]
    except Exception as e:
        raise RuntimeError(f"Failed to connect to MongoDB: {e}") from e


async def shutdown_mongodb(app: FastAPI) -> None:
    app.client.close()
