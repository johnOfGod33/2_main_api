from datetime import datetime

from pydantic import BaseModel


class StoredObjectOut(BaseModel):
    key: str
    size: int | None = None
    last_modified: datetime | None = None


class UploadResponse(BaseModel):
    key: str


class DownloadUrlResponse(BaseModel):
    key: str
    url: str
