import json
import tempfile
import unittest
from pathlib import Path

from grocery_pricing.pipeline import run_local_pipeline


class LocalPipelineTest(unittest.TestCase):
    def test_runs_fixture_pipeline_and_writes_latest_successful_run(self) -> None:
        fixture = Path("fixtures/sample_product.html")
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts_dir = Path(tmpdir)

            result = run_local_pipeline(fixture, artifacts_dir)

            latest_run_path = artifacts_dir / "latest_successful_run.json"
            parsed_item_path = artifacts_dir / "parsed_item.json"
            analysis_view_path = artifacts_dir / "analysis_view.html"

            self.assertEqual(result.status, "success")
            self.assertTrue(latest_run_path.exists())
            self.assertTrue(parsed_item_path.exists())
            self.assertTrue(analysis_view_path.exists())

            latest_run = json.loads(latest_run_path.read_text(encoding="utf-8"))
            self.assertEqual(latest_run["status"], "success")
            self.assertEqual(latest_run["parsed_item"]["upc"], "000123456789")
            self.assertEqual(latest_run["outputs"]["analysis_view"], "analysis_view.html")


if __name__ == "__main__":
    unittest.main()
