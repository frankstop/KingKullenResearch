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
    department: str
    categories: list[str]
    timestamp: str

    def to_json(self) -> dict[str, str]:
        return asdict(self)


def extract_freshop_items(html: str, strict: bool = True) -> list[ScrapedItem]:
    import json
    start_marker = "window.__PRELOADED_STATE__="
    start_idx = html.find(start_marker)
    if start_idx == -1:
        if strict:
            raise ValueError("Could not find window.__PRELOADED_STATE__")
        return []
    
    start_idx += len(start_marker)
    json_str = html[start_idx:]

    try:
        data, _ = json.JSONDecoder().raw_decode(json_str)
    except json.JSONDecodeError as e:
        if strict:
            raise ValueError(f"Failed to parse __PRELOADED_STATE__ JSON: {e}")
        return []

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    store = "King Kullen"
    items = []
    
    # In Freshop, products are usually in data["items"] or data["skusDictionary"] or search preview
    # Let's search recursively or specifically in known locations
    # A robust way is to find all dictionaries with "name", "price", "sku"
    def find_products(obj):
        found = []
        if isinstance(obj, dict):
            if obj.get("name") and obj.get("price") and obj.get("sku"):
                found.append(obj)
            for v in obj.values():
                found.extend(find_products(v))
        elif isinstance(obj, list):
            for item in obj:
                found.extend(find_products(item))
        return found
        
    raw_products = find_products(data)
    
    # Deduplicate by UPC
    seen_upcs = set()
    for raw in raw_products:
        upc_raw = raw.get("sku", "")
        if not upc_raw:
            continue
            
        try:
            upc = normalize_upc(upc_raw)
        except ValueError:
            continue
            
        if upc in seen_upcs:
            continue
        seen_upcs.add(upc)
        
        name = normalize_name(raw.get("name", "UNAVAILABLE"))
        price_raw = raw.get("price", "0")
        try:
            price = normalize_price(price_raw)
        except ValueError:
            price = "UNAVAILABLE"
            
        was_price_raw = raw.get("wasPrice", "")
        if was_price_raw:
            try:
                reg_price = normalize_price(was_price_raw)
            except ValueError:
                reg_price = "UNAVAILABLE"
        else:
            reg_price = price
            
        items.append(ScrapedItem(
            upc=upc,
            name=name,
            current_price=price,
            regular_price=reg_price,
            store=store,
            department="UNAVAILABLE",
            categories=[],
            timestamp=timestamp
        ))
        
    if strict and not items:
        raise ValueError("No products found in Freshop JSON")
        
    return items


class ProductHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.values: dict[str, str] = {}
        self._field: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        classes = attr_map.get("class", "").split()
        
        if "data-field" in attr_map:
            self._field = attr_map["data-field"]
            self._text = []
        elif tag == "h1" and not self._field:
            self._field = "name"
            self._text = []
        elif tag == "p" and "price_color" in classes and not self._field:
            self._field = "current-price"
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

    def parse(self, html: str, strict: bool = True) -> ScrapedItem:
        parser = ProductHTMLParser()
        parser.feed(html)
        values = parser.values

        def get_val(field: str, normalizer=lambda x: x, default: str = "UNAVAILABLE") -> str:
            val = values.get(field, "").strip()
            if not val:
                if strict:
                    raise ValueError(f"Missing required product field: {field}")
                return default
            try:
                return normalizer(val)
            except ValueError as e:
                if strict:
                    raise
                return default

        timestamp = values.get("timestamp")
        if not timestamp:
            timestamp = datetime.now(timezone.utc).isoformat()

        return ScrapedItem(
            upc=get_val("upc", normalize_upc),
            name=get_val("name", normalize_name),
            current_price=get_val("current-price", normalize_price),
            regular_price=get_val("regular-price", normalize_price),
            store=get_val("store", normalize_name),
            department="UNAVAILABLE",
            categories=[],
            timestamp=get_val("timestamp", normalize_timestamp, default=normalize_timestamp(timestamp)),
        )


def parse_product_page(html: str, strict: bool = True) -> list[ScrapedItem] | ScrapedItem:
    if "window.__PRELOADED_STATE__" in html:
        return extract_freshop_items(html, strict=strict)
    return GroceryProductPageParser().parse(html, strict=strict)


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
