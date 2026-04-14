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

from .model import (
    UserCreate,
    UserInDB,
    UserOut,
    UserProfile,
    UserProfileUpdate,
    UserPublicProfileOut,
)

USERS_COLLECTION = "users"


def _doc_to_user_out(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        email=doc["email"],
        username=doc["username"],
        first_name=doc["first_name"],
        last_name=doc["last_name"],
        phone_number=doc.get("phone_number"),
        profile=UserProfile.model_validate(doc.get("profile", {})),
        created_at=doc["created_at"],
    )


def _doc_to_user_in_db(doc: dict) -> UserInDB:
    return UserInDB.model_validate(doc)


def _doc_to_user_public_profile(doc: dict) -> UserPublicProfileOut:
    return UserPublicProfileOut(
        id=str(doc["_id"]),
        username=doc["username"],
        first_name=doc["first_name"],
        last_name=doc["last_name"],
        profile=UserProfile.model_validate(doc.get("profile", {})),
    )


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
        "phone_number": user.phone_number,
        "profile": user.profile.model_dump(),
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


async def get_public_user_profile_by_id(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> UserPublicProfileOut | None:
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        return None
    doc = await db[USERS_COLLECTION].find_one({"_id": oid})
    if doc is None:
        return None
    return _doc_to_user_public_profile(doc)


async def update_user_profile(
    db: AsyncIOMotorDatabase,
    user_id: str,
    profile_data: UserProfileUpdate,
) -> UserOut:
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    existing = await db[USERS_COLLECTION].find_one({"_id": oid})
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    patch = profile_data.model_dump(exclude_unset=True)
    if not patch:
        return _doc_to_user_out(existing)

    current_profile = UserProfile.model_validate(
        existing.get("profile", {})
    ).model_dump()
    current_profile.update(patch)

    now = datetime.now(timezone.utc)
    await db[USERS_COLLECTION].update_one(
        {"_id": oid},
        {"$set": {"profile": current_profile, "updated_at": now}},
    )
    updated = await db[USERS_COLLECTION].find_one({"_id": oid})
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update inconsistency.",
        )
    return _doc_to_user_out(updated)
