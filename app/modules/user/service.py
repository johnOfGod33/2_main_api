from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    get_password_hash,
    verify_password,
)

from .model import UserCreate, UserInDB, UserOut

USERS_COLLECTION = "users"


def _doc_to_user_out(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        email=doc["email"],
        username=doc["username"],
        first_name=doc["first_name"],
        last_name=doc["last_name"],
        created_at=doc["created_at"],
    )


def _doc_to_user_in_db(doc: dict) -> UserInDB:
    return UserInDB.model_validate(doc)


async def create_user(db: AsyncIOMotorDatabase, user: UserCreate) -> UserOut:
    existing = await db[USERS_COLLECTION].find_one({"email": user.email})
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    now = datetime.now(timezone.utc)
    doc = {
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "hashed_password": get_password_hash(user.password),
        "created_at": now,
        "updated_at": now,
        "is_active": True,
    }
    result = await db[USERS_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_user_out(doc)


async def authenticate_user(
    db: AsyncIOMotorDatabase, email: str, password: str
) -> UserInDB | None:
    doc = await db[USERS_COLLECTION].find_one({"email": email})
    if doc is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
        return None
    if not verify_password(password, doc["hashed_password"]):
        return None
    return _doc_to_user_in_db(doc)


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> UserOut | None:
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        return None
    doc = await db[USERS_COLLECTION].find_one({"_id": oid})
    if doc is None:
        return None
    return _doc_to_user_out(doc)
