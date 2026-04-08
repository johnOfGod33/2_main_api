from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from app.core.custom_document import CustomDBDocument
from app.modules.article.model import ArticleListingPreview


class OrderStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    disputed = "disputed"


class OrderCreate(CustomDBDocument):
    """Internal shape for an order row before or after persistence."""

    model_config = ConfigDict(populate_by_name=True)

    article_id: str
    buyer_id: str
    seller_id: str
    amount: float
    offer_id: str | None = None
    is_direct_purchase: bool = False


class OrderOut(CustomDBDocument):
    """Order document stored in MongoDB."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "description": "Purchase order with payment/shipping state.",
        },
    )

    article_id: str
    buyer_id: str
    seller_id: str
    amount: float
    status: OrderStatus
    offer_id: str | None = None
    is_direct_purchase: bool = False


class OrderWithArticleOut(OrderOut):
    """Order + embedded listing card for purchase flows and history."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "description": "Order with article title, image, and short description.",
        },
    )

    article: ArticleListingPreview | None = Field(
        default=None,
        description="Joined article; null if the listing was deleted.",
    )


class DirectPurchaseIn(BaseModel):
    """Body for POST /orders/direct."""

    article_id: str = Field(description="Article to buy at listed price.")


class OrderStatusUpdateIn(BaseModel):
    """Body for PUT /orders/{id}/status."""

    status: OrderStatus
