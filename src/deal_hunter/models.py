from datetime import datetime
from decimal import Decimal
from hashlib import sha256

from pydantic import BaseModel, Field, computed_field


class Product(BaseModel):
    retailer: str
    title: str
    url: str
    sku: str | None = None
    image_url: str | None = None

    @computed_field
    @property
    def id(self) -> str:
        key = f"{self.retailer}:{self.title}:{self.sku or self.url}"
        return sha256(key.encode()).hexdigest()[:16]


class PricePoint(BaseModel):
    product_id: str
    price: Decimal
    currency: str = "USD"
    in_stock: bool = True
    timestamp: datetime = Field(default_factory=datetime.now)
    shipping: str | None = None


class Perk(BaseModel):
    product_id: str
    category: str
    description: str
    value: str | None = None


class ComparisonReport(BaseModel):
    query: str
    generated_at: datetime = Field(default_factory=datetime.now)
    products: list[Product] = []
    prices: list[PricePoint] = []
    perks: list[Perk] = []
    summary_markdown: str = ""
    price_changes: list[dict] = []
