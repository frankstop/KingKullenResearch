from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
import re


@dataclass(frozen=True)
class ScrapedItem:
    upc: str
    name: str
    current_price: str
    regular_price: str
    store: str
    timestamp: str

    def to_json(self) -> dict[str, str]:
        return asdict(self)


class ProductHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: dict[str, str] = {}
        self._field: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if "data-field" in attr_map:
            self._field = attr_map["data-field"]
            self._text = []

        if tag == "meta":
            name = attr_map.get("name")
            content = attr_map.get("content")
            if name and content:
                self.values[name] = content

    def handle_data(self, data: str) -> None:
        if self._field:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._field:
            text = " ".join(part.strip() for part in self._text if part.strip())
            self.values[self._field] = text
            self._field = None
            self._text = []


class GroceryProductPageParser:
    """Small Scrapy-style parser for one grocery product fixture page."""

    def parse(self, html: str) -> ScrapedItem:
        parser = ProductHTMLParser()
        parser.feed(html)
        values = parser.values

        return ScrapedItem(
            upc=normalize_upc(require(values, "upc")),
            name=normalize_name(require(values, "name")),
            current_price=normalize_price(require(values, "current-price")),
            regular_price=normalize_price(require(values, "regular-price")),
            store=normalize_name(require(values, "store")),
            timestamp=normalize_timestamp(require(values, "timestamp")),
        )


def parse_product_page(html: str) -> ScrapedItem:
    return GroceryProductPageParser().parse(html)


def require(values: dict[str, str], field: str) -> str:
    value = values.get(field, "").strip()
    if not value:
        raise ValueError(f"Missing required product field: {field}")
    return value


def normalize_upc(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if not digits:
        raise ValueError("UPC must contain digits")
    return digits.zfill(12)


def normalize_name(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def normalize_price(raw: str) -> str:
    cleaned = re.sub(r"[^0-9.]", "", raw)
    try:
        price = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid price: {raw}") from exc
    return f"{price:.2f}"


def normalize_timestamp(raw: str) -> str:
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp: {raw}") from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
