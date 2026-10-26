from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TICKMARK_", env_file=".env", extra="ignore")

    gateway_url: str = "http://localhost:4001/v1"
    gateway_key: str = "sk-tickmark-dev"
    local_only: bool = False
    ledger_path: Path = Path("ledger/usage.jsonl")
    daily_budget: dict[str, int] = {"cloud-lite": 1000, "cloud-strong": 250, "cloud-backup": 50}

    database_url: str = "postgresql+psycopg://tickmark:tickmark@localhost:5434/tickmark"

    smtp_host: str = "localhost"
    smtp_port: int = 1026


settings = Settings()
