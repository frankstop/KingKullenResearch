from __future__ import annotations

import argparse
import json
from pathlib import Path

from grocery_pricing.parser import parse_product_page


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse a fixture grocery product page into normalized JSON."
    )
    parser.add_argument("fixture", type=Path, help="Path to fixture HTML")
    args = parser.parse_args()

    item = parse_product_page(args.fixture.read_text(encoding="utf-8"))
    print(json.dumps(item.to_json(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
