from functools import lru_cache
from typing import Literal, Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Telegram ──────────────────────────────────────────────────────────────
    bot_token: str
    admin_ids: list[int]   # "123,456" is auto-parsed to [123, 456]

    # ── CryptoBot ─────────────────────────────────────────────────────────────
    crypto_pay_token: str
    crypto_pay_network: Literal["mainnet", "testnet"] = "mainnet"

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: Optional[str] = None  # <-- Добавили поле для пароля

    # ── Lead magnet ───────────────────────────────────────────────────────────
    lead_magnet_file_id: str = ""

    # ── Computed ──────────────────────────────────────────────────────────────
    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def redis_url(self) -> str:
        # Если пароль передан, собираем URL с авторизацией: redis://:пароль@хост:порт/0
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()