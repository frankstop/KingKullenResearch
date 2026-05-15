from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Optional, Protocol, Sequence


CatalogItem = Mapping[str, Any]
ScrapedCatalogItem = Mapping[str, Any]


@dataclass(frozen=True)
class MatchResult:
    catalog_item: Optional[CatalogItem]
    match_type: str
    confidence: float
    reason: str


class MasterCatalogRepository(Protocol):
    def list_items(self) -> Sequence[CatalogItem]:
        """Return catalog items for reconciliation without exposing storage."""


def reconcile_scraped_item(
    scraped_item: ScrapedCatalogItem, master_catalog: Sequence[CatalogItem]
) -> MatchResult:
    scraped_upc = scraped_item.get("upc")
    scraped_name = normalize_catalog_name(scraped_item.get("name"))

    for catalog_item in master_catalog:
        if scraped_upc and scraped_upc == catalog_item.get("upc"):
            return MatchResult(
                catalog_item=catalog_item,
                match_type="exact_upc",
                confidence=1.0,
                reason="Scraped UPC exactly matched master catalog UPC.",
            )

    for catalog_item in master_catalog:
        if scraped_name and scraped_name == normalize_catalog_name(catalog_item.get("name")):
            return MatchResult(
                catalog_item=catalog_item,
                match_type="normalized_name",
                confidence=0.85,
                reason="Scraped product name matched normalized master catalog name.",
            )

    return MatchResult(
        catalog_item=None,
        match_type="no_match",
        confidence=0.0,
        reason="No catalog item matched.",
    )


def normalize_catalog_name(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip().casefold()
