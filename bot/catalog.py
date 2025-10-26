from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(slots=True)
class Product:
    """Representation of a single product in the catalog."""

    id: str
    title: str
    description: str
    price: int
    volume: str
    highlights: List[str]
    image_url: str

    @property
    def formatted_price(self) -> str:
        return f"{self.price:,}".replace(",", " ")


@dataclass(slots=True)
class Category:
    slug: str
    title: str
    products: List[Product]


def _build_catalog() -> list[Category]:
    return [
        Category(
            slug="face-care",
            title="Уход за лицом",
            products=[
                Product(
                    id="dr-althea-essence",
                    title="Увлажняющая эссенция Dr. Althea 50 мл",
                    description=(
                        "Лёгкая эссенция с ниацинамидом и пептидами, мгновенно впитывается\n"
                        "и усиливает действие крема. Подходит даже для чувствительной кожи."
                    ),
                    price=1690,
                    volume="50 мл",
                    highlights=[
                        "мгновенно впитывается, без липкости",
                        "подходит для чувствительной кожи",
                        "оригинал, Корея 🇰🇷",
                    ],
                    image_url="https://i.imgur.com/rIDBhp4.jpg",
                ),
                Product(
                    id="cosrx-cica-toner",
                    title="COSRX Cica Toner 150 мл",
                    description=(
                        "Тонер с центеллой, успокаивает и выравнивает тон кожи,"
                        " готовит лицо к дальнейшему уходу."
                    ),
                    price=1450,
                    volume="150 мл",
                    highlights=[
                        "без спирта и отдушек",
                        "снимает покраснения после солнца",
                        "для комбинированной и сухой кожи",
                    ],
                    image_url="https://i.imgur.com/7gE8oI5.jpg",
                ),
            ],
        ),
        Category(
            slug="masks",
            title="Маски",
            products=[
                Product(
                    id="mediheal-teatree",
                    title="MEDIHEAL Tea Tree Mask",
                    description=(
                        "Тканевая маска с чайным деревом — спасение от воспалений"
                        " и жирного блеска."
                    ),
                    price=190,
                    volume="1 шт",
                    highlights=[
                        "в составе чайное дерево и мадекассосид",
                        "успокаивает кожу за 15 минут",
                        "идеально перед важной встречей",
                    ],
                    image_url="https://i.imgur.com/yN8rhcF.jpg",
                ),
                Product(
                    id="laneige-sleeping-mask",
                    title="LANEIGE Water Sleeping Mask",
                    description=(
                        "Ночная маска с гиалуроновой кислотой, обеспечивающая глубокое"
                        " увлажнение пока вы спите."
                    ),
                    price=2490,
                    volume="70 мл",
                    highlights=[
                        "аромат лаванды помогает расслабиться",
                        "утром кожа упругая и сияющая",
                        "экономичный расход",
                    ],
                    image_url="https://i.imgur.com/HiOUJp1.jpg",
                ),
            ],
        ),
        Category(
            slug="perfume",
            title="Парфюм",
            products=[
                Product(
                    id="molecule-02",
                    title="Escentric Molecules Molecule 02",
                    description=(
                        "Прозрачный аромат на основе амброксана: раскрывается индивидуально"
                        " на каждом, создаёт эффект «чистой кожи»."
                    ),
                    price=5990,
                    volume="100 мл",
                    highlights=[
                        "подходит женщинам и мужчинам",
                        "стойкость до 12 часов",
                        "официальная поставка",
                    ],
                    image_url="https://i.imgur.com/qLScxCR.jpg",
                ),
                Product(
                    id="byredo-blanche",
                    title="Byredo Blanche",
                    description=(
                        "Нежный букет из белых цветов с мускусным шлейфом, ассоциируется"
                        " с мягкостью и свежестью."
                    ),
                    price=12490,
                    volume="100 мл",
                    highlights=[
                        "топ-ноты: альдегиды, розовый перец",
                        "база: мускус, сандал",
                        "идеален для дневного образа",
                    ],
                    image_url="https://i.imgur.com/nZ2vKPq.jpg",
                ),
            ],
        ),
        Category(
            slug="makeup",
            title="Макияж",
            products=[
                Product(
                    id="romand-tint",
                    title="Rom&nd Glasting Water Tint",
                    description=(
                        "Тинт с эффектом влажных губ и комфортной текстурой без липкости."
                    ),
                    price=890,
                    volume="4 г",
                    highlights=[
                        "оттенки №05 Rose Splash и №07 Pink Valley",
                        "не сушит губы",
                        "удобный аппликатор",
                    ],
                    image_url="https://i.imgur.com/L25mIYf.jpg",
                ),
                Product(
                    id="clio-kill-cover",
                    title="Clio Kill Cover Cushion",
                    description=(
                        "Кушон со средней плотностью покрытия и эффектом натуральной"
                        " кожи. SPF 50+ PA+++."
                    ),
                    price=2390,
                    volume="15 г + рефилл",
                    highlights=[
                        "перекрывает покраснения",
                        "содержит ухаживающие экстракты",
                        "подходит комбинированной коже",
                    ],
                    image_url="https://i.imgur.com/UJd2CYz.jpg",
                ),
            ],
        ),
    ]


def get_catalog() -> list[Category]:
    return _build_catalog()


def iter_products() -> Iterable[Product]:
    for category in get_catalog():
        yield from category.products


def find_product(product_id: str) -> Product | None:
    for product in iter_products():
        if product.id == product_id:
            return product
    return None


def find_category(slug: str) -> Category | None:
    for category in get_catalog():
        if category.slug == slug:
            return category
    return None
