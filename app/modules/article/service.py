from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from .model import (
    ArticleCreate,
    ArticleListingPreview,
    ArticleOut,
    ArticleStatus,
    ArticleUpdate,
)


def article_to_listing_preview(article: ArticleOut) -> ArticleListingPreview:
    """Map full article API model to the embedded card (no extra DB roundtrip)."""
    desc = article.description
    if len(desc) > 140:
        desc = desc[:140] + "…"
    return ArticleListingPreview(
        id=article.id,
        title=article.title,
        description_preview=desc,
        list_price=article.price,
        status=article.status,
        primary_image_url=article.images[0] if article.images else None,
    )

ARTICLES_COLLECTION = "articles"


def _doc_to_article_out(doc: dict) -> ArticleOut:
    return ArticleOut.model_validate(doc)


async def create_article(
    db: AsyncIOMotorDatabase,
    article: ArticleCreate,
    owner_id: str,
) -> ArticleOut:
    now = datetime.now(timezone.utc)
    doc = {
        "title": article.title,
        "description": article.description,
        "price": article.price,
        "status": article.status.value,
        "images": article.images,
        "owner_id": owner_id,
        "created_at": now,
        "updated_at": now,
    }
    result = await db[ARTICLES_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_article_out(doc)


async def get_articles(
    db: AsyncIOMotorDatabase,
    status: ArticleStatus | None,
    skip: int,
    limit: int,
    owner_id: str | None = None,
) -> list[ArticleOut]:
    query: dict = {}
    if status is not None:
        query["status"] = status.value
    if owner_id is not None:
        query["owner_id"] = owner_id
    cursor = (
        db[ARTICLES_COLLECTION]
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    docs = await cursor.to_list(length=limit)
    return [_doc_to_article_out(d) for d in docs]


async def get_article_by_id(
    db: AsyncIOMotorDatabase,
    article_id: str,
) -> ArticleOut | None:
    try:
        oid = ObjectId(article_id)
    except InvalidId:
        return None
    doc = await db[ARTICLES_COLLECTION].find_one({"_id": oid})
    if doc is None:
        return None
    return _doc_to_article_out(doc)


async def update_article(
    db: AsyncIOMotorDatabase,
    article_id: str,
    data: ArticleUpdate,
    owner_id: str,
) -> ArticleOut:
    try:
        oid = ObjectId(article_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    doc = await db[ARTICLES_COLLECTION].find_one({"_id": oid})
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    if doc["owner_id"] != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to modify this article.",
        )
    patch = data.model_dump(exclude_unset=True, exclude_none=True)
    if not patch:
        return _doc_to_article_out(doc)
    if "status" in patch:
        patch["status"] = patch["status"].value
    patch["updated_at"] = datetime.now(timezone.utc)
    await db[ARTICLES_COLLECTION].update_one({"_id": oid}, {"$set": patch})
    updated = await db[ARTICLES_COLLECTION].find_one({"_id": oid})
    assert updated is not None
    return _doc_to_article_out(updated)


async def delete_article(
    db: AsyncIOMotorDatabase,
    article_id: str,
    owner_id: str,
) -> None:
    try:
        oid = ObjectId(article_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    doc = await db[ARTICLES_COLLECTION].find_one({"_id": oid})
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    if doc["owner_id"] != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this article.",
        )
    await db[ARTICLES_COLLECTION].delete_one({"_id": oid})


async def update_article_status_by_id(
    db: AsyncIOMotorDatabase,
    article_id: str,
    new_status: ArticleStatus,
) -> None:
    """Set article status (internal use by offer/order flows)."""
    try:
        oid = ObjectId(article_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    now = datetime.now(timezone.utc)
    res = await db[ARTICLES_COLLECTION].update_one(
        {"_id": oid},
        {"$set": {"status": new_status.value, "updated_at": now}},
    )
    if res.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
