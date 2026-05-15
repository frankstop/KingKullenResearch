import unittest
import json
import tempfile
from pathlib import Path

from grocery_pricing.analysis_view import (
    build_analysis_from_latest_run,
    build_sample_analysis,
    render_analysis_view_html,
)


class AnalysisViewTest(unittest.TestCase):
    def test_renders_glass_box_analysis_for_one_upc(self) -> None:
        analysis = build_sample_analysis()

        html = render_analysis_view_html(analysis)

        self.assertIn("UPC 000123456789", html)
        self.assertIn("Organic Gala Apples", html)
        self.assertIn("Price spread over time", html)
        self.assertIn("Store comparison", html)
        self.assertIn("Anomaly flags", html)
        self.assertIn("Source rows", html)
        self.assertIn("same-day peer median", html)
        self.assertIn("Budget Basket", html)

    def test_builds_analysis_from_latest_successful_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            latest_run = Path(tmpdir) / "latest_successful_run.json"
            latest_run.write_text(
                json.dumps(
                    {
                        "status": "success",
                        "completed_at": "2026-05-15T01:37:46Z",
                        "parsed_item": {
                            "upc": "000123456789",
                            "name": "Organic Gala Apples",
                        },
                    }
                ),
                encoding="utf-8",
            )

            analysis = build_analysis_from_latest_run(latest_run)
            html = render_analysis_view_html(analysis)

            self.assertIn("Latest successful run", html)
            self.assertIn("2026-05-15T01:37:46Z", html)


if __name__ == "__main__":
    unittest.main()
