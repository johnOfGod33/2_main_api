from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.article.aggregation import lookup_article_listing_preview
from app.modules.article.model import ArticleStatus
from app.modules.article.service import (
    get_article_by_id,
    update_article_status_by_id,
)
from app.modules.order.service import create_order_from_offer

from .model import OfferCreate, OfferOut, OfferStatus, OfferWithArticleOut

OFFERS_COLLECTION = "offers"


def _doc_to_offer_out(doc: dict) -> OfferOut:
    return OfferOut.model_validate(doc)


async def _aggregate_offer_with_article(
    db: AsyncIOMotorDatabase,
    pipeline_prefix: list[dict],
) -> list[OfferWithArticleOut]:
    pipeline = [
        *pipeline_prefix,
        *lookup_article_listing_preview("article_id"),
    ]
    cursor = db[OFFERS_COLLECTION].aggregate(pipeline)
    raw = await cursor.to_list(None)
    return [OfferWithArticleOut.model_validate(d) for d in raw]


async def get_offer_with_article_by_id(
    db: AsyncIOMotorDatabase,
    offer_id: str,
) -> OfferWithArticleOut | None:
    try:
        oid = ObjectId(offer_id)
    except InvalidId:
        return None
    rows = await _aggregate_offer_with_article(
        db,
        [{"$match": {"_id": oid}}, {"$limit": 1}],
    )
    return rows[0] if rows else None


async def _get_offer_doc(db: AsyncIOMotorDatabase, offer_id: str) -> dict | None:
    try:
        oid = ObjectId(offer_id)
    except InvalidId:
        return None
    return await db[OFFERS_COLLECTION].find_one({"_id": oid})


async def create_offer(
    db: AsyncIOMotorDatabase,
    offer: OfferCreate,
    buyer_id: str,
) -> OfferWithArticleOut:
    article = await get_article_by_id(db, offer.article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    if article.status != ArticleStatus.published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offers are only allowed on published listings.",
        )
    if article.owner_id == buyer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot place an offer on your own listing.",
        )
    dup = await db[OFFERS_COLLECTION].find_one(
        {
            "article_id": offer.article_id,
            "buyer_id": buyer_id,
            "status": OfferStatus.pending.value,
        }
    )
    if dup is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending offer on this article.",
        )
    now = datetime.now(timezone.utc)
    doc = {
        "article_id": offer.article_id,
        "amount": offer.amount,
        "status": OfferStatus.pending.value,
        "buyer_id": buyer_id,
        "seller_id": article.owner_id,
        "created_at": now,
        "updated_at": now,
    }
    result = await db[OFFERS_COLLECTION].insert_one(doc)
    enriched = await get_offer_with_article_by_id(db, str(result.inserted_id))
    if enriched is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Offer data inconsistency after insert.",
        )
    return enriched


async def get_offers_for_article(
    db: AsyncIOMotorDatabase,
    article_id: str,
    requester_id: str,
) -> list[OfferWithArticleOut]:
    article = await get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    rows = await _aggregate_offer_with_article(
        db,
        [
            {"$match": {"article_id": article_id}},
            {"$sort": {"created_at": -1}},
            {"$limit": 500},
        ],
    )
    buyer_ids = {r.buyer_id for r in rows}
    if requester_id != article.owner_id and requester_id not in buyer_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view offers for this article.",
        )
    return rows


async def get_my_offers(
    db: AsyncIOMotorDatabase, buyer_id: str
) -> list[OfferWithArticleOut]:
    return await _aggregate_offer_with_article(
        db,
        [
            {"$match": {"buyer_id": buyer_id}},
            {"$sort": {"created_at": -1}},
            {"$limit": 200},
        ],
    )


async def respond_to_offer(
    db: AsyncIOMotorDatabase,
    offer_id: str,
    accept: bool,
    seller_id: str,
) -> OfferWithArticleOut:
    doc = await _get_offer_doc(db, offer_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found.",
        )
    if doc["seller_id"] != seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the seller can respond to this offer.",
        )
    if doc["status"] != OfferStatus.pending.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offer is no longer pending.",
        )
    now = datetime.now(timezone.utc)
    article_id = doc["article_id"]

    if accept:
        await db[OFFERS_COLLECTION].update_one(
            {"_id": doc["_id"]},
            {"$set": {"status": OfferStatus.accepted.value, "updated_at": now}},
        )
        await db[OFFERS_COLLECTION].update_many(
            {
                "article_id": article_id,
                "status": OfferStatus.pending.value,
                "_id": {"$ne": doc["_id"]},
            },
            {"$set": {"status": OfferStatus.declined.value, "updated_at": now}},
        )
        await update_article_status_by_id(db, article_id, ArticleStatus.reserved)
        updated_offer = await _get_offer_doc(db, offer_id)
        if updated_offer is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Offer not found after accept.",
            )
        await create_order_from_offer(db, _doc_to_offer_out(updated_offer))
    else:
        await db[OFFERS_COLLECTION].update_one(
            {"_id": doc["_id"]},
            {"$set": {"status": OfferStatus.declined.value, "updated_at": now}},
        )
    enriched = await get_offer_with_article_by_id(db, offer_id)
    if enriched is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Offer data inconsistency.",
        )
    return enriched


async def cancel_offer(
    db: AsyncIOMotorDatabase,
    offer_id: str,
    buyer_id: str,
) -> OfferWithArticleOut:
    doc = await _get_offer_doc(db, offer_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer not found.",
        )
    if doc["buyer_id"] != buyer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the buyer can cancel this offer.",
        )
    if doc["status"] != OfferStatus.pending.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending offers can be cancelled.",
        )
    now = datetime.now(timezone.utc)
    await db[OFFERS_COLLECTION].update_one(
        {"_id": doc["_id"]},
        {"$set": {"status": OfferStatus.cancelled.value, "updated_at": now}},
    )
    enriched = await get_offer_with_article_by_id(db, offer_id)
    if enriched is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Offer data inconsistency after cancel.",
        )
    return enriched
