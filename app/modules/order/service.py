from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.modules.article.aggregation import lookup_article_listing_preview
from app.modules.article.model import ArticleStatus
from app.modules.article.service import get_article_by_id, update_article_status_by_id
from app.modules.offer.model import OfferOut, OfferStatus

from .model import OrderOut, OrderStatus, OrderWithArticleOut

ORDERS_COLLECTION = "orders"
OFFERS_COLLECTION = "offers"


def _doc_to_order_out(doc: dict) -> OrderOut:
    return OrderOut.model_validate(doc)


async def _aggregate_orders_with_article(
    db: AsyncIOMotorDatabase,
    pipeline_prefix: list[dict],
) -> list[OrderWithArticleOut]:
    pipeline = [
        *pipeline_prefix,
        *lookup_article_listing_preview("article_id"),
    ]
    cursor = db[ORDERS_COLLECTION].aggregate(pipeline)
    raw = await cursor.to_list(None)
    return [OrderWithArticleOut.model_validate(d) for d in raw]


async def get_order_with_article_by_id(
    db: AsyncIOMotorDatabase,
    order_id: str,
) -> OrderWithArticleOut | None:
    try:
        oid = ObjectId(order_id)
    except InvalidId:
        return None
    rows = await _aggregate_orders_with_article(
        db,
        [{"$match": {"_id": oid}}, {"$limit": 1}],
    )
    return rows[0] if rows else None


async def _get_order_doc(db: AsyncIOMotorDatabase, order_id: str) -> dict | None:
    try:
        oid = ObjectId(order_id)
    except InvalidId:
        return None
    return await db[ORDERS_COLLECTION].find_one({"_id": oid})


async def create_order_from_offer(
    db: AsyncIOMotorDatabase,
    offer: OfferOut,
) -> OrderOut:
    now = datetime.now(timezone.utc)
    doc = {
        "article_id": offer.article_id,
        "buyer_id": offer.buyer_id,
        "seller_id": offer.seller_id,
        "amount": offer.amount,
        "status": OrderStatus.pending.value,
        "offer_id": offer.id,
        "is_direct_purchase": False,
        "created_at": now,
        "updated_at": now,
    }
    result = await db[ORDERS_COLLECTION].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _doc_to_order_out(doc)


async def create_direct_order(
    db: AsyncIOMotorDatabase,
    article_id: str,
    buyer_id: str,
) -> OrderWithArticleOut:
    article = await get_article_by_id(db, article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found.",
        )
    if article.status != ArticleStatus.published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article must be published for direct purchase.",
        )
    seller_id = article.owner.id
    if seller_id == buyer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot purchase your own listing.",
        )
    now = datetime.now(timezone.utc)
    await db[OFFERS_COLLECTION].update_many(
        {"article_id": article_id, "status": OfferStatus.pending.value},
        {"$set": {"status": OfferStatus.declined.value, "updated_at": now}},
    )
    await update_article_status_by_id(db, article_id, ArticleStatus.reserved)
    doc = {
        "article_id": article_id,
        "buyer_id": buyer_id,
        "seller_id": seller_id,
        "amount": article.price,
        "status": OrderStatus.pending.value,
        "offer_id": None,
        "is_direct_purchase": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db[ORDERS_COLLECTION].insert_one(doc)
    enriched = await get_order_with_article_by_id(db, str(result.inserted_id))
    if enriched is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order data inconsistency after insert.",
        )
    return enriched


async def mock_payment(
    db: AsyncIOMotorDatabase,
    order_id: str,
    buyer_id: str,
) -> OrderWithArticleOut:
    doc = await _get_order_doc(db, order_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    if doc["buyer_id"] != buyer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the buyer can pay for this order.",
        )
    if doc["status"] != OrderStatus.pending.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is not awaiting payment.",
        )
    now = datetime.now(timezone.utc)
    await db[ORDERS_COLLECTION].update_one(
        {"_id": doc["_id"]},
        {"$set": {"status": OrderStatus.paid.value, "updated_at": now}},
    )
    await update_article_status_by_id(db, doc["article_id"], ArticleStatus.sold)
    enriched = await get_order_with_article_by_id(db, order_id)
    if enriched is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order data inconsistency after payment.",
        )
    return enriched


async def update_order_status(
    db: AsyncIOMotorDatabase,
    order_id: str,
    new_status: OrderStatus,
    requester_id: str,
) -> OrderWithArticleOut:
    doc = await _get_order_doc(db, order_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    current = OrderStatus(doc["status"])
    buyer_id = doc["buyer_id"]
    seller_id = doc["seller_id"]
    now = datetime.now(timezone.utc)

    if new_status == OrderStatus.shipped:
        if current != OrderStatus.paid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status transition.",
            )
        if requester_id != seller_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the seller can mark the order as shipped.",
            )
    elif new_status == OrderStatus.delivered:
        if current != OrderStatus.shipped:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status transition.",
            )
        if requester_id != buyer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the buyer can confirm delivery.",
            )
    elif new_status == OrderStatus.cancelled:
        if current not in (OrderStatus.paid, OrderStatus.shipped):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status transition.",
            )
        if requester_id not in (buyer_id, seller_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the buyer or seller can cancel this order.",
            )
    elif new_status == OrderStatus.disputed:
        if current not in (
            OrderStatus.paid,
            OrderStatus.shipped,
            OrderStatus.delivered,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status transition.",
            )
        if requester_id not in (buyer_id, seller_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the buyer or seller can open a dispute.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status transition.",
        )

    await db[ORDERS_COLLECTION].update_one(
        {"_id": doc["_id"]},
        {"$set": {"status": new_status.value, "updated_at": now}},
    )
    if new_status == OrderStatus.cancelled:
        await update_article_status_by_id(
            db, doc["article_id"], ArticleStatus.published
        )
    enriched = await get_order_with_article_by_id(db, order_id)
    if enriched is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order data inconsistency after status update.",
        )
    return enriched


async def get_my_orders(
    db: AsyncIOMotorDatabase,
    user_id: str,
    role: str,
) -> list[OrderWithArticleOut]:
    if role == "buyer":
        query = {"buyer_id": user_id}
    elif role == "seller":
        query = {"seller_id": user_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='role must be "buyer" or "seller".',
        )
    return await _aggregate_orders_with_article(
        db,
        [
            {"$match": query},
            {"$sort": {"created_at": -1}},
            {"$limit": 200},
        ],
    )


async def get_order_by_id(
    db: AsyncIOMotorDatabase,
    order_id: str,
    requester_id: str,
) -> OrderWithArticleOut:
    doc = await _get_order_doc(db, order_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    if requester_id not in (doc["buyer_id"], doc["seller_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view this order.",
        )
    enriched = await get_order_with_article_by_id(db, order_id)
    if enriched is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Order data inconsistency.",
        )
    return enriched
