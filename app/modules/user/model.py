from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.custom_document import CustomDBDocument
from app.core.security import BCRYPT_MAX_PASSWORD_BYTES


class UserCreate(BaseModel):
    """Registration payload (POST /auth/register body)."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Data required to create a user account.",
        }
    )

    email: EmailStr = Field(description="Unique account email address.")
    password: str = Field(
        min_length=8,
        description="Plain-text password; minimum 8 characters (hashed server-side).",
    )

    @field_validator("password")
    @classmethod
    def password_within_bcrypt_byte_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password must not exceed {BCRYPT_MAX_PASSWORD_BYTES} UTF-8 bytes "
                "(bcrypt limit)."
            )
        return v

    username: str = Field(
        min_length=1,
        max_length=64,
        description="Display username on the platform.",
    )
    first_name: str = Field(
        min_length=1,
        max_length=128,
        description="User first name.",
    )
    last_name: str = Field(
        min_length=1,
        max_length=128,
        description="User last name.",
    )


class UserInDB(CustomDBDocument):
    """Full user as stored in the database (internal use)."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": "MongoDB user document including password hash and shared "
            "metadata (timestamps, soft-delete).",
        }
    )

    email: EmailStr = Field(description="Account email address.")
    username: str = Field(description="Username.")
    first_name: str = Field(description="First name.")
    last_name: str = Field(description="Last name.")
    hashed_password: str = Field(
        description="Bcrypt password hash; never expose in API responses.",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the account may sign in and use the API.",
    )


class UserOut(BaseModel):
    """User returned by the API (no sensitive fields)."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Public user profile after registration or for an "
            "authenticated user.",
        }
    )

    id: str = Field(description="User id (ObjectId as string).")
    email: EmailStr = Field(description="Email address.")
    username: str = Field(description="Username.")
    first_name: str = Field(description="First name.")
    last_name: str = Field(description="Last name.")
    created_at: datetime = Field(description="Account creation time (UTC).")


class LoginInput(BaseModel):
    """Credentials to obtain a JWT (POST /auth/login)."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Email and password for authentication.",
        }
    )

    email: EmailStr = Field(description="Account email.")
    password: str = Field(description="Plain-text password.")

    @field_validator("password")
    @classmethod
    def password_within_bcrypt_byte_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > BCRYPT_MAX_PASSWORD_BYTES:
            raise ValueError(
                f"Password must not exceed {BCRYPT_MAX_PASSWORD_BYTES} UTF-8 bytes "
                "(bcrypt limit)."
            )
        return v


class TokenOut(BaseModel):
    """OAuth2-style response after successful login."""

    model_config = ConfigDict(
        json_schema_extra={
            "description": "Bearer access token to send in the Authorization header.",
        }
    )

    access_token: str = Field(
        description="Signed JWT (HS256) including subject (user id) as sub.",
    )
    token_type: str = Field(
        default="bearer",
        description='Token type; always "bearer" for this flow.',
    )
