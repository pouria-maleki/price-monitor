from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app import models, schemas

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/{product_id}", response_model=list[schemas.PriceHistoryOut])
def get_price_history(
    product_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(500, le=5000),
):
    """
    Full price-change timeline for one product — this is what feeds the
    Recharts line chart on the product detail page.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="محصول پیدا نشد")

    rows = (
        db.query(models.PriceHistory)
        .filter(models.PriceHistory.product_id == product_id)
        .order_by(models.PriceHistory.created_at.asc())
        .limit(limit)
        .all()
    )
    return rows
