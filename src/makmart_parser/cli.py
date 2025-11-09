"""Command line entry point for Makmart scraper."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from .config import ScraperConfig, ensure_output_directories
from .excel import export_to_excel
from .models import Product, ScrapeSummary
from .scraper import MakmartScraper
from .snapshot import build_snapshot, diff_snapshots, load_snapshot, save_snapshot

LOGGER = logging.getLogger(__name__)


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Сбор данных каталога makmart.ru")
    parser.add_argument("command", choices=["scrape"], help="Команда для выполнения")
    parser.add_argument("--output", dest="output", type=Path, default=Path("data/makmart_inventory.xlsx"), help="Путь к Excel файлу")
    parser.add_argument("--snapshot", dest="snapshot", type=Path, default=Path("data/last_snapshot.json"), help="Путь к JSON снимку")
    parser.add_argument("--store", dest="store", default="Наро-Фоминск", help="Название города склада")
    parser.add_argument("--include", nargs="*", dest="include", help="Список категорий для включения")
    parser.add_argument("--exclude", nargs="*", dest="exclude", help="Список категорий для исключения")
    parser.add_argument("--only", nargs="*", dest="only", help="Список категорий для выборочного сбора")
    parser.add_argument("--log-level", dest="log_level", default="INFO", help="Уровень логирования")
    return parser.parse_args(argv)


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def run_scrape(config: ScraperConfig) -> List[Product]:
    ensure_output_directories([config.output_path, config.snapshot_path])
    scraper = MakmartScraper(config)
    products: List[Product] = []
    try:
        for product in scraper.iter_products():
            products.append(product)
    finally:
        scraper.close()
    return products


def summarize(products: List[Product], diff: dict) -> ScrapeSummary:
    generated_at = datetime.now()
    summary = ScrapeSummary(
        generated_at=generated_at,
        total_products=len(products),
        total_categories=len({product.category for product in products}),
        new_products=len(diff.get("new", {})),
        removed_products=len(diff.get("removed", {})),
        changed_products=len(diff.get("changed", {})),
    )
    return summary


def print_summary(summary: ScrapeSummary) -> None:
    LOGGER.info("Итого товаров: %s", summary.total_products)
    LOGGER.info("Категорий: %s", summary.total_categories)
    LOGGER.info("Новых товаров: %s", summary.new_products)
    LOGGER.info("Удалено товаров: %s", summary.removed_products)
    LOGGER.info("Изменений: %s", summary.changed_products)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = parse_args(argv)
    configure_logging(args.log_level)

    config = ScraperConfig(
        store_city=args.store,
        output_path=args.output,
        snapshot_path=args.snapshot,
        categories_whitelist=args.include,
        categories_blacklist=args.exclude,
        requested_categories=args.only,
    )

    LOGGER.info("Запуск сбора каталога")
    products = run_scrape(config)

    snapshot = build_snapshot(products)
    previous_snapshot = load_snapshot(config.snapshot_path)
    diff = diff_snapshots(snapshot, previous_snapshot)

    export_to_excel(
        products,
        diff,
        str(config.output_path),
        snapshot.generated_at,
        config.store_city,
    )
    save_snapshot(config.snapshot_path, snapshot)

    summary = summarize(products, diff)
    print_summary(summary)


if __name__ == "__main__":
    main()
