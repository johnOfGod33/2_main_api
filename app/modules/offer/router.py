from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db
from app.modules.user.model import UserOut

from .model import OfferCreate, OfferWithArticleOut
from .service import (
    cancel_offer,
    create_offer,
    get_my_offers,
    get_offers_for_article,
    respond_to_offer,
)

router = APIRouter()


@router.post("", response_model=OfferWithArticleOut, status_code=status.HTTP_201_CREATED)
async def post_offer(
    body: OfferCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> OfferWithArticleOut:
    try:
        return await create_offer(db, body, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/mine", response_model=list[OfferWithArticleOut])
async def list_my_offers(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> list[OfferWithArticleOut]:
    try:
        return await get_my_offers(db, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/article/{article_id}", response_model=list[OfferWithArticleOut])
async def list_offers_for_article(
    article_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> list[OfferWithArticleOut]:
    try:
        return await get_offers_for_article(db, article_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.put("/{offer_id}/accept", response_model=OfferWithArticleOut)
async def accept_offer(
    offer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> OfferWithArticleOut:
    try:
        return await respond_to_offer(db, offer_id, True, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.put("/{offer_id}/decline", response_model=OfferWithArticleOut)
async def decline_offer(
    offer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> OfferWithArticleOut:
    try:
        return await respond_to_offer(db, offer_id, False, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.put("/{offer_id}/cancel", response_model=OfferWithArticleOut)
async def cancel_offer_route(
    offer_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> OfferWithArticleOut:
    try:
        return await cancel_offer(db, offer_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
