"""Configuration helpers for the Makmart scraper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass(slots=True)
class ScraperConfig:
    """Runtime configuration for the scraper."""

    base_url: str = "https://makmart.ru"
    catalog_path: str = "/catalog/"
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.0.0 Safari/537.36"
    )
    store_city: str = "Наро-Фоминск"
    rate_limit_seconds: float = 0.5
    max_retries: int = 3
    timeout: int = 30
    snapshot_path: Path = Path("data/last_snapshot.json")
    output_path: Path = Path("data/makmart_inventory.xlsx")
    categories_whitelist: Optional[List[str]] = None
    categories_blacklist: Optional[List[str]] = None
    requested_categories: Optional[List[str]] = None

    def should_scrape_category(self, category_name: str, category_url: str) -> bool:
        """Determine whether a category should be scraped."""

        if self.requested_categories:
            lowered = {name.lower() for name in self.requested_categories}
            return category_name.lower() in lowered or category_url.lower() in lowered

        if self.categories_whitelist:
            lowered = {name.lower() for name in self.categories_whitelist}
            if category_name.lower() not in lowered and category_url.lower() not in lowered:
                return False

        if self.categories_blacklist:
            lowered = {name.lower() for name in self.categories_blacklist}
            if category_name.lower() in lowered or category_url.lower() in lowered:
                return False

        return True

    @property
    def timestamp(self) -> datetime:
        """Return the timestamp when the scrape was configured."""

        return datetime.now()


def ensure_output_directories(paths: Iterable[Path]) -> None:
    """Ensure that directories for the provided paths exist."""

    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
