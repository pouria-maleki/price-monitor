from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from backend.app.database import get_db
from backend.app import models, schemas

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("/{product_id}", response_model=list[schemas.PriceOut])
def get_sellers_for_product(product_id: int, db: Session = Depends(get_db)):
    """
    All known sellers/prices for one product (Digikala + every Torob seller
    currently on record), sorted cheapest-first. This backs the "فروشندگان"
    view on the product detail page.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="محصول پیدا نشد")

    prices = (
        db.query(models.Price)
        .options(joinedload(models.Price.store))
        .filter(models.Price.product_id == product_id)
        .order_by(models.Price.price.is_(None), models.Price.price.asc())
        .all()
    )
    return prices
