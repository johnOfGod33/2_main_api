from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import create_access_token
from app.dependencies import get_current_user, get_db

from .model import LoginInput, TokenOut, UserCreate, UserOut
from .service import authenticate_user, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserOut:
    try:
        return await create_user(db, body)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.post("/login", response_model=TokenOut, status_code=status.HTTP_200_OK)
async def login(
    body: LoginInput,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> TokenOut:
    try:
        user = await authenticate_user(db, body.email, body.password)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = create_access_token({"sub": user.id})
        return TokenOut(
            access_token=token,
            token_type="bearer",  # nosec B106
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@router.get("/me", response_model=UserOut)
async def read_me(
    current_user: Annotated[UserOut, Depends(get_current_user)],
) -> UserOut:
    try:
        return current_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
