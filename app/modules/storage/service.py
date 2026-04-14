import uuid
from datetime import datetime
from threading import Lock
from time import time
from typing import Any

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

SIGNED_URL_CACHE_MAX_ITEMS = 5000
SIGNED_URL_CACHE_SAFETY_MARGIN_SECONDS = 15
_signed_url_cache: dict[tuple[str, int], tuple[str, float]] = {}
_signed_url_cache_lock = Lock()


def _bucket() -> str:
    if not settings.AWS_S3_BUCKET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SERVICE_UNAVAILABLE",
        )
    return settings.AWS_S3_BUCKET


def _s3_client():
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SERVICE_UNAVAILABLE",
        )
    kwargs: dict[str, Any] = {
        "service_name": "s3",
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "region_name": settings.AWS_REGION,
    }
    if settings.AWS_S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
    return boto3.client(**kwargs)


def upload_object(file: UploadFile) -> str:
    client = _s3_client()
    bucket = _bucket()
    name = file.filename or "upload"
    key = f"{uuid.uuid4().hex}_{name}"
    extra: dict[str, str] = {}
    if file.content_type:
        extra["ContentType"] = file.content_type
    try:
        file.file.seek(0)
        if extra:
            client.upload_fileobj(file.file, bucket, key, ExtraArgs=extra)
        else:
            client.upload_fileobj(file.file, bucket, key)
        return key
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_SERVER_ERROR",
        ) from e


def download_object(key: str, expires_in: int = 900) -> str:
    return sign_object_url(key=key, expires_in=expires_in, verify_exists=True)


def sign_object_url(
    key: str,
    expires_in: int = 900,
    verify_exists: bool = False,
) -> str:
    cache_key = (key, expires_in)
    now = time()
    if not verify_exists:
        with _signed_url_cache_lock:
            cached = _signed_url_cache.get(cache_key)
            if cached is not None:
                cached_url, cached_expiry = cached
                if now < (cached_expiry - SIGNED_URL_CACHE_SAFETY_MARGIN_SECONDS):
                    print("CACHE HIT")
                    return cached_url
    print("CACHE MISS")
    client = _s3_client()
    bucket = _bucket()
    try:
        # Useful for single-object endpoint; disabled in listing flows for speed.
        if verify_exists:
            client.head_object(Bucket=bucket, Key=key)
        signed_url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        if not verify_exists:
            with _signed_url_cache_lock:
                if len(_signed_url_cache) >= SIGNED_URL_CACHE_MAX_ITEMS:
                    _signed_url_cache.clear()
                _signed_url_cache[cache_key] = (signed_url, now + expires_in)
                print("CACHE SET")
        return signed_url
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "")
        if code in ("404", "NoSuchKey"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NOT_FOUND",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_SERVER_ERROR",
        ) from e


def list_objects() -> list[dict[str, Any]]:
    client = _s3_client()
    bucket = _bucket()
    try:
        response = client.list_objects_v2(Bucket=bucket)
        out: list[dict[str, Any]] = []
        for obj in response.get("Contents", []):
            lm = obj.get("LastModified")
            out.append(
                {
                    "key": obj["Key"],
                    "size": obj.get("Size"),
                    "last_modified": lm if isinstance(lm, datetime) else None,
                }
            )
        return out
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_SERVER_ERROR",
        ) from e
