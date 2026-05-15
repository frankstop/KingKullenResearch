# Cron Plan

This repo is not scraping live grocery sites yet. Cron should only run local,
fixture-backed commands until live acquisition is explicitly approved.

## Recommended Jobs

### 1. Daily fixture pipeline refresh

Purpose: keep `artifacts/latest_successful_run.json`, `artifacts/parsed_item.json`,
`artifacts/analysis_view.html`, and `artifacts/pipeline.log` fresh.

Suggested schedule: every weekday at 6:15 AM local time.

Cron draft:

```cron
15 6 * * 1-5 cd /Users/poweruser/Desktop/grocery-pricing-pipeline && python3 -m grocery_pricing.pipeline >> artifacts/cron.log 2>&1
```

Status: staged, not installed.

### 2. Weekly local verification

Purpose: prove tests and the local pipeline still pass from the Desktop repo.

Suggested schedule: Monday at 6:30 AM local time.

Cron draft:

```cron
30 6 * * 1 cd /Users/poweruser/Desktop/grocery-pricing-pipeline && python3 scripts/check.py >> artifacts/check-cron.log 2>&1
```

Status: staged, not installed.

### 3. Optional monthly artifact sanity check

Purpose: produce a lightweight reminder to inspect the latest dashboard and logs.

Suggested schedule: first weekday of each month at 7:00 AM local time.

Cron draft:

```cron
0 7 1 * * cd /Users/poweruser/Desktop/grocery-pricing-pipeline && ls -lh artifacts >> artifacts/artifact-review.log 2>&1
```

Status: optional, not installed.

## HITL Before Installing

- Confirm the machine should run these jobs when asleep or logged out.
- Confirm whether weekday-only is right.
- Confirm whether cron is preferred over launchd on macOS.
- Confirm live scraping is still out of scope.
