"""
Pydantic (response/request) schemas — kept separate from the ORM models
so the API contract doesn't accidentally change when the DB schema does.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    kind: str


class PriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    store: StoreOut
    price: Optional[int] = None
    is_available: bool
    url: Optional[str] = None
    checked_at: datetime


class PriceHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    store_id: Optional[int] = None
    old_price: Optional[int] = None
    new_price: Optional[int] = None
    change_percent: Optional[float] = None
    created_at: datetime


class ProductListItem(BaseModel):
    """Row shape for the main dashboard table."""
    id: int
    name: str
    warehouse_title: Optional[str] = None
    quantity: Optional[int] = None
    category: str
    digikala_price: Optional[int] = None
    digikala_available: Optional[bool] = None
    torob_min_price: Optional[int] = None
    torob_min_store: Optional[str] = None
    cheapest_price: Optional[int] = None
    cheapest_store: Optional[str] = None
    change_percent: Optional[float] = None
    last_checked_at: Optional[datetime] = None


class ProductDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    warehouse_title: Optional[str] = None
    quantity: Optional[int] = None
    category: str
    digikala_url: Optional[str] = None
    torob_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    prices: list[PriceOut] = []


class ProductsPage(BaseModel):
    total: int
    items: list[ProductListItem]
