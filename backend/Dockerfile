# Build context is the REPO ROOT (see docker-compose.yml: `context: .`),
# because the backend imports sibling top-level packages: scraper/, scheduler/,
# database/. Running `docker build` from inside backend/ directly will NOT work.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# System deps for psycopg2 + Playwright/Chromium runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
        libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
        libgbm1 libasound2 libpango-1.0-0 libcairo2 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Playwright's chromium is only needed as a LAST-RESORT scraping fallback
# (see scraper/playwright_utils.py). If this download ever fails in your
# network environment, comment it out — the API/JSON scraping strategies
# still work without it, they just lose the fallback.
RUN playwright install --with-deps chromium || echo "Playwright browser install skipped/failed — fallback scraping disabled."

COPY backend/ ./backend/
COPY scraper/ ./scraper/
COPY scheduler/ ./scheduler/
COPY database/ ./database/

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
