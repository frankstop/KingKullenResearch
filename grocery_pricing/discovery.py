import json
import logging
import urllib.request
from pathlib import Path

USER_AGENT = "grocery-pricing-learning-bot/0.1"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_html(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read().decode("utf-8")

def find_all_categories(obj):
    all_nodes = []
    if isinstance(obj, dict):
        if "displayName" in obj and "identifier" in obj and "children" in obj:
            all_nodes.append(obj)
            for child in obj["children"]:
                all_nodes.extend(find_all_categories(child))
        else:
            for v in obj.values():
                all_nodes.extend(find_all_categories(v))
    elif isinstance(obj, list):
        for item in obj:
            all_nodes.extend(find_all_categories(item))
    return all_nodes

def run_discovery():
    url = "https://www.shopkingkullen.com/"
    logger.info(f"Fetching {url}")
    html = get_html(url)
    
    start_marker = "window.__PRELOADED_STATE__="
    start_idx = html.find(start_marker)
    if start_idx == -1:
        logger.error("Could not find __PRELOADED_STATE__ on homepage.")
        return
        
    start_idx += len(start_marker)
    json_str = html[start_idx:]
    
    data, _ = json.JSONDecoder().raw_decode(json_str)
    
    categories = find_all_categories(data)
    
    # Deduplicate by identifier
    seen = set()
    unique_categories = []
    for cat in categories:
        ident = cat.get("identifier")
        if ident and ident not in seen:
            seen.add(ident)
            unique_categories.append(cat)
            
    logger.info(f"Found {len(unique_categories)} unique categories.")
    
    # Generate URLs
    urls = [
        f"https://www.shopkingkullen.com/categories/cat-id-{cat['identifier']}"
        for cat in unique_categories
    ]
    
    out_dir = Path("artifacts/kingkullen")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "categories.json"
    
    with open(out_file, "w") as f:
        json.dump(urls, f, indent=2)
        
    logger.info(f"Saved category URLs to {out_file}")

if __name__ == "__main__":
    run_discovery()
