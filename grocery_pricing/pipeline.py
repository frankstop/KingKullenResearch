from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from grocery_pricing.analysis_view import (
    build_analysis_from_latest_run,
    render_analysis_view_html,
)
from grocery_pricing.parser import parse_product_page


@dataclass(frozen=True)
class PipelineRunResult:
    status: str
    started_at: str
    completed_at: str
    fixture: str
    parsed_item: Dict[str, str]
    outputs: Dict[str, str]

    def to_json(self) -> dict[str, object]:
        return asdict(self)


def run_local_pipeline(
    fixture_path: Path, artifacts_dir: Path = Path("artifacts")
) -> PipelineRunResult:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    log_path = artifacts_dir / "pipeline.log"
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )

    started_at = utc_now()
    logging.info("pipeline_start fixture=%s", fixture_path)

    parsed_item = parse_product_page(fixture_path.read_text(encoding="utf-8"))
    parsed_item_json = parsed_item.to_json()

    parsed_item_path = artifacts_dir / "parsed_item.json"
    parsed_item_path.write_text(
        json.dumps(parsed_item_json, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    analysis_view_path = artifacts_dir / "analysis_view.html"

    completed_at = utc_now()
    result = PipelineRunResult(
        status="success",
        started_at=started_at,
        completed_at=completed_at,
        fixture=str(fixture_path),
        parsed_item=parsed_item_json,
        outputs={
            "parsed_item": parsed_item_path.name,
            "analysis_view": analysis_view_path.name,
            "log": log_path.name,
        },
    )

    latest_run_path = artifacts_dir / "latest_successful_run.json"
    latest_run_path.write_text(
        json.dumps(result.to_json(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    analysis_view_path.write_text(
        render_analysis_view_html(build_analysis_from_latest_run(latest_run_path)),
        encoding="utf-8",
    )
    logging.info("pipeline_success latest_run=%s", latest_run_path)
    return result


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local grocery pricing pipeline.")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path("fixtures/sample_product.html"),
        help="Fixture product HTML to parse",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts"),
        help="Directory for run outputs",
    )
    args = parser.parse_args()

    result = run_local_pipeline(args.fixture, args.artifacts_dir)
    print(json.dumps(result.to_json(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
