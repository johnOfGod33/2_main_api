from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.dependencies import get_current_user
from app.modules.storage.model import (
    DownloadUrlResponse,
    StoredObjectOut,
    UploadResponse,
)
from app.modules.user.model import UserOut

from .service import list_objects, sign_object_url, upload_object

router = APIRouter(prefix="/storage", tags=["Storage"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload(
    # _: Annotated[UserOut, Depends(get_current_user)],
    file: UploadFile,
) -> UploadResponse:
    key = await run_in_threadpool(upload_object, file)
    return UploadResponse(key=key)


@router.get("/download/{key:path}")
async def download(
    # _: Annotated[UserOut, Depends(get_current_user)],
    key: str,
    expires_in: int = Query(default=900, ge=60, le=86400),
) -> DownloadUrlResponse:
    signed_url = await run_in_threadpool(sign_object_url, key, expires_in, False)
    return DownloadUrlResponse(key=key, url=signed_url)


@router.get("/objects", response_model=list[StoredObjectOut])
async def list_storage_objects(
    current_user: Annotated[UserOut, Depends(get_current_user)],
) -> list[StoredObjectOut]:
    rows = await run_in_threadpool(list_objects)
    return [
        StoredObjectOut(
            key=r["key"],
            size=r.get("size"),
            last_modified=r.get("last_modified"),
        )
        for r in rows
    ]
