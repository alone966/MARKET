"""High-level scraper orchestration."""

from __future__ import annotations

import logging
from collections import deque
from typing import Generator, List, Set

from .config import ScraperConfig
from .http import HttpClient
from .models import Category, Product
from .parsing import (
    extract_categories,
    extract_pagination_links,
    extract_product_links,
    parse_product,
)

LOGGER = logging.getLogger(__name__)


class MakmartScraper:
    """Scrape Makmart catalog data."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.client = HttpClient(
            base_url=config.base_url,
            user_agent=config.user_agent,
            rate_limit_seconds=config.rate_limit_seconds,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )

    def fetch_categories(self) -> List[Category]:
        LOGGER.info("Загрузка списка категорий")
        response = self.client.get(self.config.catalog_path)
        categories = extract_categories(response.text, self.config.base_url)
        LOGGER.info("Найдено %s категорий", len(categories))
        return categories

    def iter_products(self) -> Generator[Product, None, None]:
        categories = self.fetch_categories()
        for category in categories:
            if not self.config.should_scrape_category(category.name, category.url):
                LOGGER.debug("Пропускаем категорию %s", category.name)
                continue
            yield from self._scrape_category(category)

    def _scrape_category(self, category: Category) -> Generator[Product, None, None]:
        LOGGER.info("Сбор товаров для категории '%s'", category.name)
        visited_pages: Set[str] = set()
        pending_pages: deque[str] = deque([category.url])

        while pending_pages:
            page_url = pending_pages.popleft()
            if page_url in visited_pages:
                continue
            visited_pages.add(page_url)
            try:
                response = self.client.get(page_url)
            except Exception as error:  # noqa: BLE001
                LOGGER.warning("Не удалось загрузить страницу %s: %s", page_url, error)
                continue

            product_links = extract_product_links(response.text, self.config.base_url)
            pagination_links = extract_pagination_links(response.text, self.config.base_url)

            for link in product_links:
                try:
                    product = self._scrape_product(category.name, link)
                except Exception as error:  # noqa: BLE001
                    LOGGER.warning("Ошибка при обработке товара %s: %s", link, error)
                    continue
                else:
                    yield product

            for link in pagination_links:
                if link not in visited_pages:
                    pending_pages.append(link)

    def _scrape_product(self, category_name: str, url: str) -> Product:
        LOGGER.debug("Загрузка товара %s", url)
        response = self.client.get(url)
        product = parse_product(response.text, category_name, url)
        return product

    def close(self) -> None:
        self.client.close()


__all__ = ["MakmartScraper"]
