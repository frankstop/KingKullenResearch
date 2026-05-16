import json
import logging
import time
import urllib.error
import urllib.request
from pathlib import Path

from grocery_pricing.parser import parse_product_page

USER_AGENT = "grocery-pricing-learning-bot/0.1"
POLITENESS_DELAY = 1.0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8")

def run_crawler():
    categories_file = Path("artifacts/kingkullen/categories.json")
    if not categories_file.exists():
        logger.error(f"{categories_file} not found. Run discovery.py first.")
        return
        
    with open(categories_file, "r") as f:
        urls = json.load(f)
        
    logger.info(f"Loaded {len(urls)} category URLs to crawl.")
    
    out_file = Path("artifacts/kingkullen/all_products.jsonl")
    
    # We will append, so let's keep track of seen UPCs to avoid massive duplicates 
    # if categories overlap (e.g. Milk might be in Dairy and Beverages).
    seen_upcs = set()
    if out_file.exists():
        with open(out_file, "r") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    obj = json.loads(line)
                    if "upc" in obj:
                        seen_upcs.add(obj["upc"])
                except:
                    pass
        logger.info(f"Loaded {len(seen_upcs)} existing UPCs from previous runs.")
        
    new_items_count = 0
    
    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] Fetching {url}")
        try:
            html = fetch_page(url)
            items = parse_product_page(html, strict=False)
            
            if not isinstance(items, list):
                items = [items]
                
            with open(out_file, "a") as f:
                for item in items:
                    if item.upc not in seen_upcs:
                        f.write(json.dumps(item.to_json()) + "\n")
                        seen_upcs.add(item.upc)
                        new_items_count += 1
                        
        except Exception as e:
            logger.error(f"Failed to process {url}: {e}")
            
        time.sleep(POLITENESS_DELAY)
        
    logger.info(f"Crawl completed! Added {new_items_count} new unique products.")
    logger.info(f"Total products in dataset: {len(seen_upcs)}")

if __name__ == "__main__":
    run_crawler()
