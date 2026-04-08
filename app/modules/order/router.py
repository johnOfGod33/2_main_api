from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_db
from app.modules.user.model import UserOut

from .model import DirectPurchaseIn, OrderStatusUpdateIn, OrderWithArticleOut
from .service import (
    create_direct_order,
    get_my_orders,
    get_order_by_id,
    mock_payment,
    update_order_status,
)

router = APIRouter()


@router.post(
    "/direct",
    response_model=OrderWithArticleOut,
    status_code=status.HTTP_201_CREATED,
)
async def post_direct_order(
    body: DirectPurchaseIn,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> OrderWithArticleOut:
    try:
        return await create_direct_order(db, body.article_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/{order_id}/pay", response_model=OrderWithArticleOut)
async def post_mock_pay(
    order_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> OrderWithArticleOut:
    try:
        return await mock_payment(db, order_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.put("/{order_id}/status", response_model=OrderWithArticleOut)
async def put_order_status(
    order_id: str,
    body: OrderStatusUpdateIn,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> OrderWithArticleOut:
    try:
        return await update_order_status(db, order_id, body.status, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/mine", response_model=list[OrderWithArticleOut])
async def list_my_orders(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
    role: Literal["buyer", "seller"] = Query(description='Use "buyer" or "seller".'),
) -> list[OrderWithArticleOut]:
    try:
        return await get_my_orders(db, current_user.id, role)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/{order_id}", response_model=OrderWithArticleOut)
async def get_order(
    order_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> OrderWithArticleOut:
    try:
        return await get_order_by_id(db, order_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
