from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """Runtime configuration for the bot."""

    bot_token: str
    admin_chat_id: int | None
    database_path: Path

    @classmethod
    def load(cls) -> "Settings":
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise RuntimeError(
                "BOT_TOKEN environment variable is required to start the bot"
            )

        admin_value = os.getenv("ADMIN_CHAT_ID")
        admin_chat_id = int(admin_value) if admin_value else None

        db_path = Path(os.getenv("DATABASE_PATH", "./data/orders.db")).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        return cls(bot_token=token, admin_chat_id=admin_chat_id, database_path=db_path)


settings = Settings.load()
