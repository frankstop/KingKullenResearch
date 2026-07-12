# King Kullen Research Architecture

The repository has three layers. A scheduled run is complete only when all three succeed.

## 1. Raw observations

`grocery_pricing.api_crawler` discovers the current category tree and writes one immutable dated JSONL snapshot to `data/snapshots/`.

Contract:

- A record contains UPC, name, current price, regular price, store, categories, and timestamp.
- The crawler writes to a temporary file and replaces the dated snapshot only after meeting the minimum item threshold.
- Raw snapshots are evidence. Analysis code never rewrites prior snapshots.

## 2. Derived time series

`grocery_pricing.weekly_report` reads every snapshot, deduplicates records by UPC, and derives:

- unique product and category counts;
- average current price and sale rate for every snapshot;
- matched coverage, increases, decreases, additions, and removals for every adjacent pair;
- the largest latest-week price increases and decreases.

The stable machine-readable output is `docs/data/weekly-summary.json`.

`grocery_pricing.catalog_history` builds the union of UPCs across every snapshot, classifies current, new, returned, and missing items, and publishes a compact search index plus 64 deterministic on-demand history shards. The browser aligns observations to the complete snapshot calendar so unobserved weeks remain visible gaps.

Publication fails when the newest snapshot matches less than 80% of the prior catalog. This prevents a partial crawl from silently becoming the comparison baseline.

## 3. Published views

- `docs/index.html` is the project overview. Its live operating metrics are loaded from `docs/data/weekly-summary.json`.
- `docs/weekly-report.html` is generated from the derived time series. It shows historical trends, every weekly comparison, pipeline health, and latest price movers.
- `docs/catalog-history.html` is the searchable all-item explorer with complete UPC-level current/regular price histories.
- `docs/data/catalog-history/` contains the manifest, compact union index, and on-demand history shards.
- GitHub Pages publishes `docs/` after the workflow commits the generated outputs.

## Scheduled control flow

1. GitHub Actions runs every Sunday.
2. The crawler writes and validates the new raw snapshot.
3. The time-series and catalog-history builders derive every published longitudinal view and enforce coverage.
4. The test suite runs.
5. Raw and derived outputs are committed together.
6. The workflow summary reports the current weekly numbers.

If crawling, coverage validation, analysis, or tests fail, no new snapshot or report is committed.

## Extension rule

New analytics should consume the derived JSON contract when possible. Add a field to the report builder and its tests before adding another independent script that reads raw snapshots. This keeps UPC matching, coverage rules, and metric definitions in one place.
