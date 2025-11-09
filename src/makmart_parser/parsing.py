"""HTML parsing helpers for Makmart pages."""

from __future__ import annotations

import json
import logging
from datetime import datetime
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import Category, Product

LOGGER = logging.getLogger(__name__)

CATEGORY_LINK_PATTERNS = (
    re.compile(r"^/catalog/(?!search).*"),
    re.compile(r"^https?://[^/]+/catalog/.*"),
)


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_float(text: str) -> Optional[float]:
    cleaned = text.replace("\xa0", " ")
    match = re.search(r"([0-9]+(?:[\s\xa0][0-9]{3})*(?:[.,][0-9]+)?)", cleaned)
    if not match:
        return None
    number = match.group(1).replace(" ", "").replace("\xa0", "").replace(",", ".")
    try:
        return float(number)
    except ValueError:
        return None


def parse_int(text: str) -> Optional[int]:
    cleaned = text.replace("\xa0", " ")
    match = re.search(r"([0-9]+)", cleaned)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def absolute_url(base_url: str, url: str) -> str:
    return urljoin(base_url, url)


def extract_categories(html: str, base_url: str) -> List[Category]:
    soup = BeautifulSoup(html, "html.parser")
    categories: Dict[str, Category] = {}

    for link in soup.select("a"):
        href = link.get("href")
        if not href:
            continue
        text = normalize_whitespace(link.get_text(strip=True))
        if not text:
            continue
        if not any(pattern.match(href) for pattern in CATEGORY_LINK_PATTERNS):
            continue
        url = absolute_url(base_url, href)
        if url in categories:
            continue
        categories[url] = Category(name=text, url=url)

    result = sorted(categories.values(), key=lambda category: category.name.lower())
    LOGGER.debug("Found %s categories", len(result))
    return result


def extract_product_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for container in soup.select("[data-entity='item'] a, a.product-card__link, a.catalog-item__title, a.product-item-image-link"):
        href = container.get("href")
        if not href:
            continue
        url = absolute_url(base_url, href)
        if url not in links:
            links.append(url)

    if not links:
        for link in soup.select("a"):
            href = link.get("href")
            if not href:
                continue
            if "/product/" not in href and "/catalog/" not in href:
                continue
            text = link.get_text(strip=True)
            if not text:
                continue
            url = absolute_url(base_url, href)
            if url not in links:
                links.append(url)

    LOGGER.debug("Found %s product links", len(links))
    return links


def extract_pagination_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: List[str] = []
    for link in soup.select("a"):
        if "PAGEN" not in (link.get("href") or ""):
            continue
        href = link.get("href")
        if not href:
            continue
        url = absolute_url(base_url, href)
        if url not in links:
            links.append(url)
    LOGGER.debug("Found %s pagination links", len(links))
    return links


def parse_json_ld(soup: BeautifulSoup) -> List[dict]:
    payloads: List[dict] = []
    for script in soup.select('script[type="application/ld+json"]'):
        raw = script.string
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            payloads.append(data)
        elif isinstance(data, list):
            payloads.extend([item for item in data if isinstance(item, dict)])
    return payloads


def extract_stock_by_city(soup: BeautifulSoup) -> Dict[str, Optional[int]]:
    stock: Dict[str, Optional[int]] = {}

    for table in soup.select("table"):
        headers = [normalize_whitespace(cell.get_text()) for cell in table.select("th")]
        lower_headers = [header.lower() for header in headers]
        if not any("город" in header or "склад" in header for header in lower_headers):
            if not headers and len(table.select("tr")) > 3:
                pass
            else:
                continue

        for row in table.select("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            city = normalize_whitespace(cells[0].get_text())
            if not city:
                continue
            quantity_text = normalize_whitespace(cells[-1].get_text())
            quantity = parse_int(quantity_text)
            stock[city] = quantity

    if stock:
        return stock

    for element in soup.select("[data-city], .store-item, .shop-item"):
        city_attr = element.get("data-city")
        city_name = normalize_whitespace(city_attr or element.get_text())
        if not city_name:
            continue
        quantity_text = normalize_whitespace(element.get("data-quantity", ""))
        if not quantity_text:
            quantity_text = normalize_whitespace(element.get_text())
        quantity = parse_int(quantity_text)
        stock[city_name] = quantity

    return stock


def parse_product(html: str, category_name: str, url: str) -> Product:
    soup = BeautifulSoup(html, "html.parser")
    json_ld_data = parse_json_ld(soup)

    name: Optional[str] = None
    sku: Optional[str] = None
    description: str = ""
    price: Optional[float] = None
    currency: Optional[str] = None

    for payload in json_ld_data:
        if payload.get("@type") == "Product":
            name = payload.get("name") or name
            sku = payload.get("sku") or payload.get("mpn") or sku
            description = payload.get("description") or description
            offers = payload.get("offers")
            if isinstance(offers, dict):
                price = parse_float(str(offers.get("price", ""))) or price
                currency = offers.get("priceCurrency") or currency
            elif isinstance(offers, list):
                for offer in offers:
                    if not isinstance(offer, dict):
                        continue
                    price = parse_float(str(offer.get("price", ""))) or price
                    currency = offer.get("priceCurrency") or currency
                    availability = offer.get("availability", "")
                    if availability:
                        pass

    if not name:
        name_element = soup.find(attrs={"itemprop": "name"}) or soup.select_one("h1")
        if name_element:
            name = normalize_whitespace(name_element.get_text())

    if not sku:
        sku_element = soup.find(attrs={"itemprop": "sku"})
        if not sku_element:
            sku_label = soup.find(string=re.compile(r"Артикул", re.IGNORECASE))
            if sku_label and sku_label.parent:
                sku_element = sku_label.parent
        if sku_element:
            sku = normalize_whitespace(sku_element.get_text()).replace("Артикул", "").strip(" :")

    description_element = soup.find(attrs={"itemprop": "description"})
    if description_element:
        description = normalize_whitespace(description_element.get_text())
    elif not description:
        paragraphs = [normalize_whitespace(p.get_text()) for p in soup.select(".product-detail__description p")]
        description = "\n".join([paragraph for paragraph in paragraphs if paragraph])

    price_element = soup.find(attrs={"itemprop": "price"})
    if price_element and price is None:
        price = parse_float(price_element.get("content") or price_element.get_text())
    if price_element and not currency:
        currency = price_element.get("data-currency") or price_element.get("content")
    if currency:
        currency = currency.upper()

    stock_by_city = extract_stock_by_city(soup)

    if not sku:
        raise ValueError(f"Не удалось определить артикул для товара: {url}")

    return Product(
        category=category_name,
        url=url,
        sku=sku,
        name=name or "",
        description=description,
        price=price,
        currency=currency,
        stock_by_city=stock_by_city,
        last_updated=datetime.now(),
    )


__all__ = [
    "extract_categories",
    "extract_product_links",
    "extract_pagination_links",
    "parse_product",
]
