# Grocery Pricing Pipeline

A small learning repo for a grocery pricing pipeline. The first vertical slice
parses one checked-in product page fixture and prints normalized JSON.

## Commands

Run tests:

```bash
python3 -m unittest
```

Parse the fixture:

```bash
python3 -m grocery_pricing fixtures/sample_product.html
```

Run the local pipeline:

```bash
python3 -m grocery_pricing.pipeline
```

Run local checks:

```bash
python3 scripts/check.py
```

## Current Interfaces

- `parse_product_page(html)` parses one fixture product page into normalized item
  JSON.
- `GroceryProductPageParser().parse(html)` provides a small Scrapy-style parser
  object for Phase 1.
- `reconcile_scraped_item(scraped_item, master_catalog)` matches scraped items to
  a master catalog by exact UPC first, then normalized name. Database writes stay
  outside this function behind a future repository adapter.
- `detect_price_drop_anomalies(records)` flags competitor prices that fall far
  below the same-day peer median and returns the explanation with the source
  record details.

## Roadmap

- Phase 0: Parse one fixture product page into normalized product pricing JSON.
- Phase 1: Build fixture-first parsers with TDD before live scraping.
- Phase 2: Add reconciliation between scraped items and a master catalog.
- Phase 3: Prototype anomaly detection and forecasting with synthetic data.
- Phase 4: Build a glass-box analysis UI for pricing analysts.
- Phase 5: Automate local workflow with Docker, cron-safe logging, and checks.

## Prototypes

Run the Phase 3 modeling prototype:

```bash
python3 prototypes/modeling_phase3_prototype.py
```

Render the Phase 4 Analysis View prototype:

```bash
python3 -m grocery_pricing.analysis_view
```

The generated HTML is written to `artifacts/analysis_view.html`.

## Automation

The local pipeline writes:

- `artifacts/parsed_item.json`
- `artifacts/latest_successful_run.json`
- `artifacts/analysis_view.html`
- `artifacts/pipeline.log`

Build and run with Docker in an environment where Docker is installed:

```bash
docker build -t grocery-pricing .
docker run --rm grocery-pricing
```

Cron example: [docs/operations/cron.example](docs/operations/cron.example)

Cron plan: [docs/operations/cron-plan.md](docs/operations/cron-plan.md)

Phase 5 issue breakdown: [docs/issues/phase5-automation.md](docs/issues/phase5-automation.md)

HITL items remain for installing cron, verifying Docker locally, and choosing a
real pre-commit hook system after this folder is initialized as a git repo.
