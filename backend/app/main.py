import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.database import init_db
from backend.app.routers import products, history, shops

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("price_monitor")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    logger.info("Initializing database (create tables if missing)...")
    init_db()

    scheduler = None
    try:
        from scheduler.scheduler import start_scheduler

        scheduler = start_scheduler()
        logger.info("Price-check scheduler started (interval=%ss).", settings.CHECK_INTERVAL)
    except Exception:
        # A scheduler failure must never take the whole API down — the dashboard
        # and manual endpoints should keep working even if scraping is broken.
        logger.exception("Failed to start scheduler; API will run without automatic price checks.")

    yield

    # --- shutdown ---
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")


app = FastAPI(
    title="Price Monitor API",
    description="مانیتورینگ خودکار قیمت محصولات از دیجی‌کالا و ترب",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(history.router)
app.include_router(shops.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "price-monitor-api"}


@app.get("/health")
def health():
    return {"status": "healthy"}
