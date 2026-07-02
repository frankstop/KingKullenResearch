import json
import tempfile
import unittest
from pathlib import Path

from grocery_pricing.weekly_report import build_weekly_summary, write_report


def write_snapshot(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )


class WeeklyReportTest(unittest.TestCase):
    def test_compares_latest_two_snapshots_and_writes_public_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            snapshots = root / "snapshots"
            snapshots.mkdir()
            base = [
                {
                    "upc": "1",
                    "name": "Apples",
                    "current_price": "4.00",
                    "regular_price": "4.00",
                    "categories": ["Produce"],
                },
                {
                    "upc": "2",
                    "name": "Milk",
                    "current_price": "3.00",
                    "regular_price": "3.00",
                    "categories": ["Dairy"],
                },
            ]
            current = [
                {
                    "upc": "1",
                    "name": "Apples",
                    "current_price": "3.00",
                    "regular_price": "4.00",
                    "categories": ["Produce"],
                },
                {
                    "upc": "2",
                    "name": "Milk",
                    "current_price": "3.50",
                    "regular_price": "3.50",
                    "categories": ["Dairy"],
                },
                {
                    "upc": "3",
                    "name": "Bread",
                    "current_price": "2.00",
                    "regular_price": "2.00",
                    "categories": ["Bakery"],
                },
            ]
            write_snapshot(snapshots / "2026-06-21.jsonl", base)
            write_snapshot(snapshots / "2026-06-28.jsonl", current)

            html_output = root / "docs" / "weekly-report.html"
            json_output = root / "docs" / "data" / "weekly-summary.json"
            summary = write_report(snapshots, html_output, json_output)

            self.assertEqual(summary["comparison"]["price_changes"], 2)
            self.assertEqual(summary["comparison"]["price_decreases"], 1)
            self.assertEqual(summary["comparison"]["price_increases"], 1)
            self.assertEqual(summary["comparison"]["new_products"], 1)
            self.assertEqual(summary["comparison"]["coverage_percentage"], 100.0)
            self.assertEqual(len(summary["comparisons"]), 1)
            self.assertEqual(summary["latest"]["sale_rate"], 33.3)
            self.assertTrue(html_output.exists())
            self.assertTrue(json_output.exists())
            self.assertIn("Price time series", html_output.read_text())

    def test_requires_two_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            one = Path(tmpdir) / "2026-06-28.jsonl"
            write_snapshot(
                one,
                [
                    {
                        "upc": "1",
                        "name": "Apples",
                        "current_price": "3.00",
                        "regular_price": "4.00",
                        "categories": ["Produce"],
                    }
                ],
            )
            with self.assertRaisesRegex(ValueError, "At least two"):
                build_weekly_summary([one])

    def test_rejects_partial_latest_snapshot_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            snapshots = root / "snapshots"
            snapshots.mkdir()
            write_snapshot(
                snapshots / "2026-06-21.jsonl",
                [
                    {
                        "upc": str(index),
                        "name": f"Product {index}",
                        "current_price": "1.00",
                        "regular_price": "1.00",
                        "categories": ["Test"],
                    }
                    for index in range(10)
                ],
            )
            write_snapshot(
                snapshots / "2026-06-28.jsonl",
                [
                    {
                        "upc": "1",
                        "name": "Product 1",
                        "current_price": "1.00",
                        "regular_price": "1.00",
                        "categories": ["Test"],
                    }
                ],
            )

            with self.assertRaisesRegex(ValueError, "minimum coverage"):
                write_report(
                    snapshots,
                    root / "weekly-report.html",
                    root / "weekly-summary.json",
                )
            self.assertFalse((root / "weekly-report.html").exists())


if __name__ == "__main__":
    unittest.main()
