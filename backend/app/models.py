"""
ORM models.

Products        -> one row per physical product we track
Stores          -> a fixed small set of sources: "digikala", "torob:<seller-name>"
Prices          -> latest known price per (product, store) pair, upserted on every check
PriceHistory    -> append-only log of every price change we detect, used for the charts
                    and for deciding whether to fire a Telegram alert
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Text, DateTime, ForeignKey,
    Boolean, Enum, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


class ProductCategory(str, enum.Enum):
    NEW = "new"          # محصولات نو
    STOCK = "stock"       # محصولات استوک
    UNKNOWN = "unknown"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    warehouse_title = Column(String(200), nullable=True)   # عنوان داده‌شده انبار (short internal code)
    url = Column(Text, nullable=True)                       # primary reference URL (digikala if present, else torob)
    digikala_url = Column(Text, nullable=True)
    torob_url = Column(Text, nullable=True)
    category = Column(Enum(ProductCategory), default=ProductCategory.UNKNOWN, nullable=False)
    quantity = Column(Integer, nullable=True)                # موجودی انبار (از اکسل)
    is_active = Column(Boolean, default=True, nullable=False)  # False = tracking disabled (e.g. link missing)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    prices = relationship("Price", back_populates="product", cascade="all, delete-orphan")
    history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product id={self.id} name={self.name!r}>"


class Store(Base):
    """
    A price source. "digikala" is a single fixed row.
    Torob sellers are created dynamically (one Store row per distinct seller name
    we encounter, e.g. "torob:فروشگاه فلان") because Torob aggregates many sellers.
    """
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    kind = Column(String(50), nullable=False, default="torob_seller")  # "digikala" | "torob_seller"

    prices = relationship("Price", back_populates="store")

    def __repr__(self):
        return f"<Store id={self.id} name={self.name!r}>"


class Price(Base):
    """
    The CURRENT (most recently observed) price for a product at a given store.
    One row per (product_id, store_id) — updated in place on every scrape;
    a change is additionally recorded into PriceHistory.
    """
    __tablename__ = "prices"
    __table_args__ = (
        UniqueConstraint("product_id", "store_id", name="uq_price_product_store"),
        Index("ix_prices_product_checked", "product_id", "checked_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    price = Column(BigInteger, nullable=True)      # تومان. NULL = ناموجود / پیدا نشد
    is_available = Column(Boolean, nullable=False, default=True)
    url = Column(Text, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="prices")
    store = relationship("Store", back_populates="prices")


class PriceHistory(Base):
    """
    Append-only ledger of price changes, used to draw the line chart and to
    decide when to send a Telegram alert. A row is inserted only when the
    price actually changes between two consecutive checks.
    """
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_history_product_created", "product_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="SET NULL"), nullable=True)
    old_price = Column(BigInteger, nullable=True)
    new_price = Column(BigInteger, nullable=True)
    change_percent = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="history")
    store = relationship("Store")
