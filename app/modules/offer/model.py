from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.core.custom_document import CustomDBDocument
from app.modules.article.model import ArticleListingPreview


class OfferStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled"


class OfferCreate(BaseModel):
    """Buyer submits a price offer on a listing."""

    model_config = ConfigDict(
        json_schema_extra={"description": "Create an offer on a published article."}
    )

    article_id: str = Field(description="Target article id (ObjectId string).")
    amount: float = Field(gt=0, description="Proposed price; must be positive.")


class OfferOut(CustomDBDocument):
    """Offer document stored in MongoDB."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "description": "Offer including parties and lifecycle state.",
        },
    )

    article_id: str
    amount: float
    status: OfferStatus
    buyer_id: str
    seller_id: str


class OfferWithArticleOut(OfferOut):
    """Offer + embedded listing card for mobile / web lists."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "description": "Offer with article title, image, and short description.",
        },
    )

    article: ArticleListingPreview | None = Field(
        default=None,
        description="Joined article; null if the listing was deleted.",
    )
