# 📊 Price Monitor — سیستم مانیتورینگ قیمت محصولات

سیستمی برای پایش خودکار قیمت محصولات از **دیجی‌کالا** و **ترب**، ذخیره تاریخچه تغییرات، نمایش در یک داشبورد حرفه‌ای، و اعلان تلگرامی هنگام تغییر قیمت.

لیست اولیه محصولات از فایل اکسل انبار (`database/inventory.xlsx`) وارد سیستم می‌شود.

---

## معماری پروژه

```
price-monitor/
├── backend/           # FastAPI — API + راه‌اندازی Scheduler
│   ├── app/
│   │   ├── main.py        # نقطه ورود FastAPI
│   │   ├── config.py       # تنظیمات از روی .env
│   │   ├── database.py     # اتصال SQLAlchemy / PostgreSQL
│   │   ├── models.py       # جداول Products, Stores, Prices, PriceHistory
│   │   ├── schemas.py      # مدل‌های Pydantic برای پاسخ API
│   │   └── routers/        # /products  /history  /shops
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/          # React + Tailwind + Recharts
│   └── src/
├── scraper/           # اسکریپرهای دیجی‌کالا و ترب + اعلان تلگرام
│   ├── base.py             # ابزارهای مشترک (fetch مقاوم، تبدیل قیمت فارسی/انگلیسی)
│   ├── digikala.py         # استراتژی: API عمومی → JSON-LD → Playwright
│   ├── torob.py             # استراتژی: __NEXT_DATA__ → Playwright
│   ├── playwright_utils.py # رندر مرورگر headless (فقط fallback)
│   └── notifier.py          # ارسال پیام تلگرام
├── scheduler/         # اجرای دوره‌ای بررسی قیمت‌ها (APScheduler)
├── database/
│   ├── schema.sql           # اسکیمای مرجع PostgreSQL
│   ├── seed_from_excel.py   # ایمپورت محصولات از اکسل
│   └── inventory.xlsx       # همان فایل اکسل انبار شما
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## ⚠️ یک نکته مهم و صادقانه درباره اسکریپرها

کد اسکریپینگ دیجی‌کالا و ترب کامل و واقعی نوشته شده (نه Placeholder) و با چند استراتژی مقاوم طراحی شده تا یک تغییر کوچک در سایت باعث خرابی کامل سیستم نشود. **اما** چون این پروژه در محیطی ساخته شده که به `digikala.com` و `torob.com` دسترسی شبکه ندارد، امکان تست مستقیم در برابر سایت‌های زنده وجود نداشت.

قبل از استفاده در Production:
```bash
python -m scraper.digikala "https://www.digikala.com/product/dkp-XXXXXXX/"
python -m scraper.torob "https://torob.com/p/XXXXXXXX/"
```
این دو دستور را روی چند لینک واقعی اجرا کن. اگر خروجی درست نبود، طبق راهنمای بالای هر فایل (`scraper/digikala.py` و `scraper/torob.py`) سلکتور/کلید JSON مربوطه را با DevTools مرورگر بررسی و اصلاح کن — بقیه سیستم (دیتابیس، API، داشبورد، اعلان تلگرام) بدون تغییر کار خواهد کرد.

---

## نصب و اجرا (با Docker — پیشنهادی)

### پیش‌نیاز
- Docker و Docker Compose نصب باشد.

### مراحل

```bash
# ۱. وارد پوشه پروژه شو
cd price-monitor

# ۲. فایل env بساز
cp .env.example .env
# فایل .env را باز کن و حداقل رمز عبور دیتابیس و (اختیاری) توکن تلگرام را تنظیم کن

# ۳. کل سیستم را بالا بیاور
docker compose up -d --build

# ۴. محصولات را از فایل اکسل وارد دیتابیس کن (فقط بار اول)
docker compose exec backend python -m database.seed_from_excel
```

بعد از این مراحل:
- داشبورد: http://localhost:3000
- API: http://localhost:8000  (مستندات Swagger: http://localhost:8000/docs)
- دیتابیس Postgres: `localhost:5432`

Scheduler به‌طور خودکار همراه backend اجرا می‌شود و هر `CHECK_INTERVAL` ثانیه (پیش‌فرض ۳۶۰۰ = ۱ ساعت) قیمت‌ها را بررسی می‌کند.

برای دیدن لاگ‌های زنده:
```bash
docker compose logs -f backend
```

---

## نصب و اجرا بدون Docker (توسعه محلی)

### Backend
```bash
cd price-monitor
python -m venv venv
source venv/bin/activate        # ویندوز: venv\Scripts\activate
pip install -r backend/requirements.txt
playwright install chromium     # فقط برای fallback اسکریپینگ

# یک PostgreSQL محلی بالا بیاور و DATABASE_URL را در .env تنظیم کن
cp .env.example .env

# جداول را بساز و اکسل را ایمپورت کن
python -m database.seed_from_excel

# اجرای API (این دستور را از ریشه پروژه بزن، نه از داخل backend/)
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env   # اگر ساختی؛ یا مستقیم VITE_API_URL=http://localhost:8000 در frontend/.env بگذار
npm run dev
```
داشبورد روی http://localhost:5173 بالا می‌آید.

---

## تنظیمات (.env)

| متغیر | توضیح | پیش‌فرض |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | مشخصات دیتابیس | `price_monitor` |
| `DATABASE_URL` | آدرس اتصال کامل (در Docker خودکار ساخته می‌شود) | — |
| `CHECK_INTERVAL` | فاصله بررسی قیمت به ثانیه | `3600` |
| `SCRAPER_CONCURRENCY` | تعداد محصولاتی که هم‌زمان اسکرپ می‌شوند | `3` |
| `TELEGRAM_BOT_TOKEN` | توکن ربات (از @BotFather) | خالی = غیرفعال |
| `TELEGRAM_CHAT_ID` | آیدی چت مقصد پیام‌ها | خالی = غیرفعال |
| `TELEGRAM_NOTIFY_THRESHOLD_PERCENT` | حداقل درصد افزایش برای اعلان (کاهش همیشه اعلان می‌شود) | `10` |
| `API_CORS_ORIGINS` | آدرس‌های مجاز برای دسترسی به API | لوکال‌هاست |
| `VITE_API_URL` | آدرسی که فرانت‌اند برای صحبت با بک‌اند استفاده می‌کند | `http://localhost:8000` |

---

## راه‌اندازی ربات تلگرام

1. در تلگرام به [@BotFather](https://t.me/BotFather) پیام بده، دستور `/newbot` را بزن و مراحل را طی کن — یک توکن مثل `123456:ABC-DEF...` دریافت می‌کنی.
2. چت آیدی خودت یا گروهی که می‌خواهی پیام‌ها آنجا برود را از [@userinfobot](https://t.me/userinfobot) بگیر.
3. هر دو مقدار را در `.env` بگذار:
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=987654321
   ```
4. اگر ربات را برای یک گروه می‌خواهی، حتماً ربات را به آن گروه اضافه کن.
5. سرویس backend را ری‌استارت کن.

نمونه پیامی که ارسال می‌شود:
```
⚠️ تغییر قیمت

محصول:
Samsung SSD

فروشگاه:
digikala

قیمت قبلی:
2,500,000

قیمت جدید:
2,900,000

تغییر:
🔺 +16.0%
```

---

## مستندات API

| Endpoint | توضیح |
|---|---|
| `GET /products` | لیست محصولات (پارامترهای اختیاری: `q`, `category`, `limit`, `offset`) |
| `GET /products/{id}` | جزئیات یک محصول به همراه تمام قیمت‌های فعلی |
| `GET /history/{id}` | تاریخچه کامل تغییرات قیمت یک محصول |
| `GET /shops/{id}` | همه فروشندگان شناخته‌شده یک محصول، مرتب‌شده بر اساس ارزان‌ترین |
| `GET /health` | بررسی سلامت سرویس |

مستندات تعاملی کامل (Swagger UI) همیشه در دسترس است: `http://localhost:8000/docs`

---

## آماده‌سازی GitHub

```bash
cd price-monitor
git init
git add .
git commit -m "Initial commit: Price Monitor"

# یک repository خالی در GitHub بساز (روی سایت github.com → New repository)
# سپس:
git branch -M main
git remote add origin https://github.com/<username>/<repo-name>.git
git push -u origin main
```

**نکته امنیتی مهم:** فایل `.env` هرگز نباید commit شود (در `.gitignore` این پروژه از قبل مستثنی شده است). فقط `.env.example` را push کن.

### تنظیم Secrets در GitHub (برای CI/CD یا Actions در صورت نیاز)
مسیر: `Settings → Secrets and variables → Actions → New repository secret`
مقادیری که معمولاً لازم است اضافه کنی: `DATABASE_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `VITE_API_URL`.

---

## Deploy در Production

### ۱. دیتابیس — Supabase (PostgreSQL)
1. در [supabase.com](https://supabase.com) یک پروژه جدید بساز.
2. از بخش `Project Settings → Database → Connection string` مقدار **Connection string (URI)** را کپی کن.
3. آن را به فرمت SQLAlchemy تبدیل کن (پیشوند را تغییر بده):
   ```
   postgresql+psycopg2://postgres:<password>@<host>:5432/postgres
   ```
4. این مقدار را به عنوان `DATABASE_URL` روی سرویس بک‌اند (Render) قرار بده.
5. یک‌بار جداول را بساز:
   - از طریق SQL Editor در Supabase محتوای `database/schema.sql` را اجرا کن،
   - یا کافیست بک‌اند را یک بار بالا بیاوری (خودش جداول را می‌سازد)، سپس:
     ```bash
     python -m database.seed_from_excel
     ```
     را با `DATABASE_URL` اشاره‌شده به Supabase اجرا کن تا محصولات ایمپورت شوند.

### ۲. Backend — Render
1. در [render.com](https://render.com) یک **New Web Service** بساز و ریپازیتوری گیت‌هاب را متصل کن.
2. تنظیمات:
   - **Root Directory:** خالی بگذار (ریشه ریپو، چون Dockerfile به scraper/scheduler/database نیاز دارد)
   - **Environment:** Docker
   - **Dockerfile Path:** `backend/Dockerfile`
   - **Docker Build Context Directory:** `.`
3. در بخش Environment Variables همان مقادیر `.env` را اضافه کن (خصوصاً `DATABASE_URL` اشاره‌شده به Supabase، و `TELEGRAM_*`).
4. Deploy بزن. بعد از بالا آمدن، آدرسی مثل `https://price-monitor-backend.onrender.com` می‌گیری.
5. یک‌بار از طریق Shell سرویس (یا لوکال با DATABASE_URL همان) دستور ایمپورت اکسل را اجرا کن.

> نکته: پلن رایگان Render بعد از مدتی بی‌فعالیتی سرویس را می‌خواباند و اولین درخواست بعدی کند خواهد بود؛ برای اجرای مداوم Scheduler به یک پلن پولی (یا یک Cron Job جدا) نیاز داری.

### ۳. Frontend — Vercel
1. در [vercel.com](https://vercel.com) پروژه جدید بساز و ریپازیتوری را متصل کن.
2. تنظیمات:
   - **Root Directory:** `frontend`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. در Environment Variables اضافه کن:
   ```
   VITE_API_URL=https://price-monitor-backend.onrender.com
   ```
4. Deploy بزن.
5. برگرد به سرویس Render بک‌اند و آدرس Vercel را به `API_CORS_ORIGINS` اضافه کن تا مرورگر اجازه درخواست بدهد، سپس بک‌اند را redeploy کن.

---

## عیب‌یابی سریع

| مشکل | راه‌حل احتمالی |
|---|---|
| داشبورد خالی است | مطمئن شو `seed_from_excel` اجرا شده؛ کنسول مرورگر و CORS را چک کن |
| قیمت‌ها آپدیت نمی‌شوند | لاگ backend را ببین (`docker compose logs -f backend`)؛ ممکن است سلکتور اسکریپر نیاز به آپدیت داشته باشد |
| پیام تلگرام نمی‌آید | توکن/چت‌آیدی را چک کن؛ اگر تغییر قیمت زیر آستانه (`TELEGRAM_NOTIFY_THRESHOLD_PERCENT`) بوده اعلان ارسال نمی‌شود مگر کاهش قیمت باشد |
| خطای اتصال دیتابیس | `DATABASE_URL` و در دسترس بودن سرویس Postgres را بررسی کن |

---

ساخته‌شده با FastAPI · PostgreSQL · React · Tailwind CSS · Recharts · APScheduler · Playwright
