# AI OFM Store Bot

Automated Telegram platform for selling digital goods (guides, AI generation packs, video tutorials) via crypto payment.

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | aiogram 3.x |
| Database | PostgreSQL 16 + asyncpg |
| ORM | SQLAlchemy 2.0 async + Alembic |
| FSM / Cache | Redis 7 |
| Payments | CryptoBot (aiocryptopay) |
| Config | pydantic-settings |
| Deploy | Docker + Docker Compose |

## Quick Start (local dev)

```bash
# 1. Clone and install deps
poetry install

# 2. Copy env template and fill in your tokens
cp .env.example .env

# 3. Start Postgres + Redis
docker-compose up postgres redis -d

# 4. Run migrations
poetry run alembic upgrade head

# 5. Start bot
poetry run python -m app.main
```

## Deploy to VPS

```bash
# On the server (Ubuntu 22.04+):
git clone <repo> && cd ai_ofm_bot
cp .env.example .env && nano .env   # fill in tokens
docker-compose up -d --build        # builds image, starts all 3 services
```

## Project Structure

```
app/
├── core/           Config (pydantic-settings)
├── database/       Models, engine, repository
├── handlers/       aiogram routers
│   ├── admin.py       Admin panel + product FSM
│   ├── catalog.py     Product listing + buy flow
│   ├── retention.py   Broadcast FSM
│   └── user_base.py   /start + lead magnet
├── keyboards/      Inline keyboard builders
├── locales/        en.json / ru.json + i18n helper
├── middlewares/    DB session, locale, admin filter
├── services/       CryptoPay client, broadcast sender
└── main.py         Entry point
```

## Admin Commands

- `/admin` — open admin panel (only your Telegram ID)
- **Add Product** → FSM collects name / description / price / file, saves `file_id` to DB
- **Broadcast** → compose message with optional photo, preview, confirm, send

## Alembic Migrations

```bash
# Auto-generate after model changes
poetry run alembic revision --autogenerate -m "describe change"

# Apply
poetry run alembic upgrade head

# Rollback one step
poetry run alembic downgrade -1
```

## Environment Variables

| Variable | Description |
|---|---|
| `BOT_TOKEN` | BotFather token |
| `ADMIN_IDS` | Comma-separated Telegram IDs |
| `CRYPTO_PAY_TOKEN` | Token from @CryptoBot |
| `CRYPTO_PAY_NETWORK` | `mainnet` or `testnet` |
| `POSTGRES_*` | DB credentials |
| `REDIS_HOST/PORT` | Redis connection |
| `LEAD_MAGNET_FILE_ID` | Telegram file_id of the free PDF |
