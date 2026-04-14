from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.core.custom_document import CustomDBDocument
from app.modules.user.model import UserPublicProfileOut


class ArticleStatus(str, Enum):
    draft = "draft"
    published = "published"
    reserved = "reserved"  # accepted offer or direct purchase awaiting payment
    sold = "sold"  # paid order, listing completed
    closed = "closed"  # seller closed manually


class ArticleListingPreview(BaseModel):
    """Lean article payload for embedded cards (offers, orders, notifications)."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Listing snapshot: title, image, short text, list price.",
        }
    )

    id: str = Field(description="Article ObjectId string.")
    title: str
    description_preview: str = Field(
        default="",
        description="Description truncated (~140 chars) for list/detail headers.",
    )
    list_price: float = Field(description="Current listing price on the article.")
    status: ArticleStatus
    primary_image_url: str | None = Field(
        default=None,
        description="First image URL if any.",
    )


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
        json_schema_extra={
            "description": "Partial article update (all fields optional).",
        },
    )

    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    status: ArticleStatus | None = None
    images: list[str] | None = None


class ArticleOut(CustomDBDocument):
    """Article persisted in MongoDB and returned by the API."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"description": "Article as exposed by the API."},
    )

    title: str
    description: str
    price: float
    status: ArticleStatus
    images: list[str]
    owner: UserPublicProfileOut = Field(
        description="Public seller profile (no email or phone number).",
    )
