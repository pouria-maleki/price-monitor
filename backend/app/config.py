"""
Centralized application settings.
All values are read from environment variables (see .env.example at the repo root).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg2://price_monitor:price_monitor@localhost:5432/price_monitor"

    # --- Scheduler ---
    CHECK_INTERVAL: int = 3600  # seconds between price checks (default: 1 hour)
    SCRAPER_CONCURRENCY: int = 3  # how many products to scrape in parallel
    SCRAPER_REQUEST_TIMEOUT: int = 20  # seconds
    SCRAPER_USE_PLAYWRIGHT_FALLBACK: bool = True

    # --- Telegram ---
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_NOTIFY_THRESHOLD_PERCENT: float = 10.0  # notify on rises >= this %, or any drop

    # --- API / CORS ---
    API_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    ENVIRONMENT: str = "development"

    # --- Excel import ---
    # Relative path so it resolves correctly whether run locally (cwd = repo
    # root) or in Docker (WORKDIR /app, which also contains database/).
    EXCEL_IMPORT_PATH: str = "database/inventory.xlsx"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.API_CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
