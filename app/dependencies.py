from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.security import decode_access_token

from app.modules.user.model import UserOut
from app.modules.user.service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.db


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> UserOut:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
