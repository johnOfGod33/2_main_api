from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ArticleStatus(str, Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class ArticleCreate(BaseModel):
    """Payload to create a listing."""

    model_config = ConfigDict(
        json_schema_extra={"description": "Fields required to create an article."}
    )

    title: str = Field(min_length=1, max_length=256, description="Listing title.")
    description: str = Field(min_length=1, description="Full description.")
    price: float = Field(ge=0, description="Price; must be non-negative.")
    status: ArticleStatus = Field(
        default=ArticleStatus.draft,
        description="Visibility / lifecycle state.",
    )
    images: list[str] = Field(
        default_factory=list,
        description="S3 or CDN URLs for images.",
    )


class ArticleUpdate(BaseModel):
    """Partial update; omit fields you do not want to change."""

    model_config = ConfigDict(
        json_schema_extra={"description": "Partial article update (all fields optional)."}
    )

    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    status: ArticleStatus | None = None
    images: list[str] | None = None


class ArticleOut(BaseModel):
    """Article returned by the API."""

    model_config = ConfigDict(
        json_schema_extra={"description": "Article as exposed by the API."}
    )

    id: str = Field(description="Article id (ObjectId as string).")
    title: str
    description: str
    price: float
    status: ArticleStatus
    images: list[str]
    owner_id: str = Field(description="User id of the seller.")
    created_at: datetime
    updated_at: datetime
