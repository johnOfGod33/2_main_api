from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer

PyObjectId = Annotated[
    str,
    BeforeValidator(str),
    PlainSerializer(lambda x: str(x), return_type=str),
]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CustomDBDocument(BaseModel):
    """Base fields for documents stored in MongoDB (Motor)."""

    model_config = ConfigDict(populate_by_name=True)

    id: Optional[PyObjectId] = Field(
        alias="_id", default=None, description="document ID"
    )
    created_at: datetime = Field(
        default_factory=_utc_now, description="date of creation"
    )
    updated_at: datetime = Field(
        default_factory=_utc_now, title="date of last update"
    )
    is_deleted: bool = Field(default=False, description="is document deleted")
    deleted_at: Optional[datetime] = Field(None, description="date of deletion")
