import argparse
import json
import logging
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from grocery_pricing.parser import ScrapedItem, normalize_price, normalize_name

USER_AGENT = "grocery-pricing-learning-bot/0.1"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def fetch_api(category_id: str, store_id: int = 23, skip: int = 0, take: int = 10) -> dict:
    url = f"https://storefrontgateway.shopkingkullen.com/api/stores/{store_id}/categories/{category_id}/groupby?take={take}&skip={skip}&productCount=100"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "x-site-host": "https://www.shopkingkullen.com",
        "accept": "application/json"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"Error fetching API for category {category_id} skip {skip}: {e}")
        return None

def extract_items(api_data: dict, store: str, timestamp: str) -> list[ScrapedItem]:
    if not api_data or "items" not in api_data:
        return []
        
    extracted = []
    
    # In groupby, top level items are categories
    for group in api_data.get("items", []):
        cat_name = group.get("categoryName", "UNAVAILABLE")
        
        for raw in group.get("items", []):
            upc = raw.get("sku", "")
            if not upc:
                continue
                
            name = raw.get("name", "UNAVAILABLE")
            price_raw = str(raw.get("priceNumeric", "0"))
            try:
                price = normalize_price(price_raw)
            except ValueError:
                price = "UNAVAILABLE"
                
            reg_price_raw = str(raw.get("regularPriceNumeric", ""))
            if not reg_price_raw or reg_price_raw == "0":
                reg_price_raw = str(raw.get("wasPriceNumeric", ""))
                
            if reg_price_raw and reg_price_raw != "0":
                try:
                    reg_price = normalize_price(reg_price_raw)
                except ValueError:
                    reg_price = "UNAVAILABLE"
            else:
                reg_price = price
                
            extracted.append(ScrapedItem(
                upc=upc.zfill(12),
                name=normalize_name(name),
                current_price=price,
                regular_price=reg_price,
                store=store,
                department="UNAVAILABLE",
                categories=[cat_name] if cat_name != "UNAVAILABLE" else [],
                timestamp=timestamp
            ))
            
    return extracted

def run_crawler(output_path: Path, store_id: int = 23, cat_file: Path | None = None):
    if cat_file is None:
        # Discover categories dynamically from the homepage
        from grocery_pricing.discovery import run_discovery
        logger.info("No category file provided — running discovery first...")
        run_discovery()
        cat_file = Path("artifacts/kingkullen/categories.json")

    if not cat_file.exists():
        logger.error(f"Categories file {cat_file} not found")
        return

    with open(cat_file, "r") as f:
        category_urls = json.load(f)

    category_ids = [url.split("-id-")[-1] for url in category_urls if "-id-" in url]
    logger.info(f"Loaded {len(category_ids)} category IDs.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_handle = open(output_path, "w")  # Always write fresh snapshot for cron runs
    total_count = 0

    store = "King Kullen"
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    take = 10  # API limit is 10 subcategories per page

    for idx, cat_id in enumerate(category_ids):
        logger.info(f"[{idx+1}/{len(category_ids)}] Crawling category {cat_id}")

        skip = 0
        while True:
            api_data = fetch_api(cat_id, store_id=store_id, skip=skip, take=take)

            if not api_data:
                break

            items = extract_items(api_data, store, timestamp)
            if not items:
                break

            for item in items:
                out_handle.write(json.dumps(item.to_json()) + "\n")
                total_count += 1

            logger.info(f"  - Page skip={skip}: +{len(items)} items")

            if api_data.get("count", 0) < take:
                break

            skip += take
            time.sleep(1.0)  # Polite delay between pages

        time.sleep(1.0)  # Polite delay between categories

    out_handle.close()
    logger.info(f"Crawl complete. {total_count} items written to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="King Kullen API Crawler")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(f"data/snapshots/{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"),
        help="Output JSONL file path (default: data/snapshots/YYYY-MM-DD.jsonl)",
    )
    parser.add_argument(
        "--store-id",
        type=int,
        default=23,
        help="King Kullen Freshop store ID (default: 23)",
    )
    parser.add_argument(
        "--categories",
        type=Path,
        default=None,
        help="Path to categories.json. If omitted, discovery runs first.",
    )
    args = parser.parse_args()
    run_crawler(output_path=args.output, store_id=args.store_id, cat_file=args.categories)
