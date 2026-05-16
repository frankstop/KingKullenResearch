import argparse
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.robotparser
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from grocery_pricing.parser import parse_product_page

ALLOWED_DOMAINS = {"books.toscrape.com", "www.shopkingkullen.com"}
USER_AGENT = "grocery-pricing-learning-bot/0.1"
POLITENESS_DELAY = 5.0

logger = logging.getLogger(__name__)

def run_probe(url: str) -> None:
    report: dict[str, Any] = {
        "target_url": url,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "robots_checked": None,
        "robots_result": None,
        "http_status": None,
        "content_type": None,
        "response_size": None,
        "elapsed_time": None,
        "extraction_success": False,
        "extracted_fields": None,
        "stop_reason": None,
    }

    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc

    if domain not in ALLOWED_DOMAINS:
        report["stop_reason"] = f"Domain {domain} is not in the allowlist"
        _write_report(report)
        logger.error(report["stop_reason"])
        return

    # Check robots.txt
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    report["robots_checked"] = robots_url
    
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        req = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                rp.parse(response.read().decode("utf-8").splitlines())
                report["robots_result"] = "allowed" if rp.can_fetch(USER_AGENT, url) else "disallowed"
            else:
                report["robots_result"] = "missing"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            report["robots_result"] = "missing"
        else:
            report["robots_result"] = "missing"
            logger.warning(f"Failed to fetch robots.txt: {e}")
    except Exception as e:
        report["robots_result"] = "missing"
        logger.warning(f"Failed to fetch robots.txt: {e}")

    if report["robots_result"] == "disallowed":
        report["stop_reason"] = "Disallowed by robots.txt"
        _write_report(report)
        logger.error(report["stop_reason"])
        return

    # Politeness delay
    logger.info(f"Sleeping for {POLITENESS_DELAY} seconds before fetching...")
    time.sleep(POLITENESS_DELAY)

    # Fetch page
    start_time = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            elapsed = time.monotonic() - start_time
            report["http_status"] = response.status
            report["content_type"] = response.headers.get("Content-Type")
            html = response.read()
            report["response_size"] = len(html)
            report["elapsed_time"] = elapsed

            if response.status != 200:
                report["stop_reason"] = f"Non-200 response: {response.status}"
                _write_report(report)
                return
                
            # Parse page
            try:
                items = parse_product_page(html.decode("utf-8"), strict=False)
                report["extraction_success"] = True
                if isinstance(items, list):
                    report["extracted_fields"] = [i.to_json() for i in items]
                else:
                    report["extracted_fields"] = items.to_json()
            except Exception as e:
                report["extraction_success"] = False
                report["stop_reason"] = f"Parser error: {e}"
                
    except urllib.error.HTTPError as e:
        report["elapsed_time"] = time.monotonic() - start_time
        report["http_status"] = e.code
        report["stop_reason"] = f"Fetch error: {e}"
        logger.error(report["stop_reason"])
    except Exception as e:
        report["elapsed_time"] = time.monotonic() - start_time
        report["stop_reason"] = f"Fetch error: {e}"
        logger.error(report["stop_reason"])

    _write_report(report)


def _write_report(report: dict[str, Any]) -> None:
    domain = urllib.parse.urlparse(report["target_url"]).netloc
    
    if "kingkullen" in domain:
        artifacts_dir = Path("artifacts/kingkullen")
    else:
        artifacts_dir = Path("artifacts")
        
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifacts_dir / "live_probe_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report written to {report_path}")

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Live single page fetch probe.")
    parser.add_argument("--url", required=True, help="The URL to probe.")
    args = parser.parse_args()
    run_probe(args.url)

if __name__ == "__main__":
    main()
