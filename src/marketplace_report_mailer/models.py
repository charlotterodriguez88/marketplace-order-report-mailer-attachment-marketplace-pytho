from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class AssetStatus(StrEnum):
    READY = "ready"
    PROCESSING = "processing"


class SellerAsset(BaseModel):
    asset_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    media_type: str = Field(min_length=1)
    status: AssetStatus


class BuyerUpdate(BaseModel):
    title: str = Field(min_length=1)
    published_at: str = Field(min_length=1)


class Seller(BaseModel):
    display_name: str = Field(min_length=1)


class Buyer(BaseModel):
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        local, separator, domain = value.partition("@")
        if not separator or not local or "." not in domain:
            raise ValueError("email must contain a local part and domain")
        return value


class OrderHandoffRequest(BaseModel):
    order_id: str = Field(min_length=1)
    seller: Seller
    buyer: Buyer
    assets: list[SellerAsset] = Field(min_length=1)
    updates: list[BuyerUpdate] = Field(default_factory=list)


class HandoffResult(BaseModel):
    order_id: str
    status: str
    reason: str
    message_id: str | None = None
