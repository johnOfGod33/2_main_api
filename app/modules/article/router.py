from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.dependencies import get_current_user, get_current_user_optional, get_db
from app.modules.user.model import UserOut

from .model import ArticleCreate, ArticleOut, ArticleStatus, ArticleUpdate
from .service import (
    create_article,
    delete_article,
    get_article_by_id,
    get_articles,
    hydrate_article_image_urls,
    hydrate_articles_image_urls,
    update_article,
)

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get("", response_model=list[ArticleOut])
async def list_articles(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut | None = Depends(get_current_user_optional),
    status_filter: Annotated[
        ArticleStatus | None,
        Query(alias="status", description="Filter by status (ignored for anonymous)."),
    ] = None,
    owner_id: Annotated[
        str | None,
        Query(description="Only articles sold by this user id (ObjectId string)."),
    ] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[ArticleOut]:
    try:
        effective_status = (
            status_filter if current_user is not None else ArticleStatus.published
        )
        articles = await get_articles(
            db,
            effective_status,
            skip,
            limit,
            owner_id=owner_id,
        )
        return hydrate_articles_image_urls(articles)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(
    article_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> ArticleOut:
    try:
        article = await get_article_by_id(db, article_id)
        if article is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Article not found.",
            )
        return hydrate_article_image_urls(article)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("", response_model=ArticleOut, status_code=status.HTTP_201_CREATED)
async def post_article(
    body: ArticleCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> ArticleOut:
    try:
        return await create_article(db, body, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.put("/{article_id}", response_model=ArticleOut)
async def put_article(
    article_id: str,
    body: ArticleUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> ArticleOut:
    try:
        return await update_article(db, article_id, body, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_article(
    article_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
) -> Response:
    try:
        await delete_article(db, article_id, current_user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
