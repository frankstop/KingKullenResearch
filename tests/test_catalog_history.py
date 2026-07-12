import json
import tempfile
import unittest
from pathlib import Path

from grocery_pricing.catalog_history import build_catalog_history


def write_snapshot(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def item(upc: str, name: str, price: str, regular: str = "") -> dict:
    return {"upc": upc, "name": name, "current_price": price, "regular_price": regular or price, "categories": ["Test"]}


class CatalogHistoryTests(unittest.TestCase):
    def test_builds_union_catalog_and_preserves_regular_prices_and_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshots = root / "snapshots"
            write_snapshot(snapshots / "2026-07-01.jsonl", [item("1", "Apple", "1.00"), item("2", "Milk", "3.00")])
            write_snapshot(snapshots / "2026-07-08.jsonl", [item("2", "Milk", "2.50", "3.00")])
            write_snapshot(snapshots / "2026-07-15.jsonl", [item("1", "Apple", "1.25"), item("3", "Bread", "2.00")])
            output = root / "public"
            manifest = build_catalog_history(snapshots, output)
            self.assertEqual((manifest["unique_items"], manifest["current_items"], manifest["missing_items"]), (3, 2, 1))
            payload = json.loads((output / "catalog-index.json").read_text())
            index = [dict(zip(payload["item_fields"], row)) for row in payload["items"]]
            by_name = {row["name"]: row for row in index}
            self.assertEqual(by_name["Apple"]["status"], "returned")
            self.assertEqual(by_name["Apple"]["trend"], [1.0, None, 1.25])
            self.assertEqual(by_name["Milk"]["status"], "missing")
            shard = json.loads((output / "items" / f'{by_name["Milk"]["shard"]}.json').read_text())
            self.assertEqual(shard["items"]["2"][1][2], 3.0)


if __name__ == "__main__":
    unittest.main()
