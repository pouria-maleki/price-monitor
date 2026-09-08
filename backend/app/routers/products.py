from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db
from backend.app import models, schemas

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=schemas.ProductsPage)
def list_products(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="جستجو در نام محصول"),
    category: str | None = Query(None, description="new | stock"),
    limit: int = Query(200, le=1000),
    offset: int = Query(0, ge=0),
):
    """
    Main dashboard table: one row per product with the current Digikala price,
    the cheapest current Torob price, the overall cheapest, and the most recent
    change_percent (from PriceHistory) so the UI can color the row.
    """
    query = db.query(models.Product).filter(models.Product.is_active.is_(True))
    if q:
        query = query.filter(models.Product.name.ilike(f"%{q}%"))
    if category:
        query = query.filter(models.Product.category == category)

    total = query.count()
    products = (
        query.order_by(models.Product.id)
        .offset(offset)
        .limit(limit)
        .options(joinedload(models.Product.prices).joinedload(models.Price.store))
        .all()
    )

    items = []
    for p in products:
        digikala_price = None
        digikala_available = None
        torob_min_price = None
        torob_min_store = None
        cheapest_price = None
        cheapest_store_name = None
        last_checked = None

        for pr in p.prices:
            if pr.checked_at and (last_checked is None or pr.checked_at > last_checked):
                last_checked = pr.checked_at

            if pr.store.kind == "digikala":
                digikala_price = pr.price
                digikala_available = pr.is_available
            elif pr.store.kind == "torob_seller":
                if pr.price is not None and (torob_min_price is None or pr.price < torob_min_price):
                    torob_min_price = pr.price
                    torob_min_store = pr.store.name

            if pr.price is not None and (cheapest_price is None or pr.price < cheapest_price):
                cheapest_price = pr.price
                cheapest_store_name = pr.store.name

        # most recent recorded change for this product (any store)
        last_change = (
            db.query(models.PriceHistory)
            .filter(models.PriceHistory.product_id == p.id)
            .order_by(models.PriceHistory.created_at.desc())
            .first()
        )

        items.append(
            schemas.ProductListItem(
                id=p.id,
                name=p.name,
                warehouse_title=p.warehouse_title,
                quantity=p.quantity,
                category=p.category.value if hasattr(p.category, "value") else str(p.category),
                digikala_price=digikala_price,
                digikala_available=digikala_available,
                torob_min_price=torob_min_price,
                torob_min_store=torob_min_store,
                cheapest_price=cheapest_price,
                cheapest_store=cheapest_store_name,
                change_percent=last_change.change_percent if last_change else None,
                last_checked_at=last_checked,
            )
        )

    return schemas.ProductsPage(total=total, items=items)


@router.get("/{product_id}", response_model=schemas.ProductDetailOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(models.Product)
        .options(joinedload(models.Product.prices).joinedload(models.Price.store))
        .filter(models.Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="محصول پیدا نشد")
    return product
