# Phase 5 Automation Issues

Local issue tracker substitute for this learning repo. No hosted issue tracker is
configured, so these are written as ready-to-grab markdown issues.

## 1. One-command local runner

Type: AFK

Blocked by: None - can start immediately

User stories covered: one-command local runner

What to build: Provide a single command that parses the fixture, records the
latest successful run, writes cron-safe logs, and refreshes the analysis view.

Acceptance criteria:

- [x] `python3 -m grocery_pricing.pipeline` runs from the repo root.
- [x] The run writes `artifacts/latest_successful_run.json`.
- [x] The run writes `artifacts/pipeline.log`.
- [x] The run writes `artifacts/analysis_view.html`.
- [x] The behavior is covered by tests.

## 2. Docker container

Type: AFK

Blocked by: Issue 1

User stories covered: Docker container

What to build: Package the local runner in a container that verifies tests at
build time and runs the fixture pipeline by default.

Acceptance criteria:

- [x] A `Dockerfile` exists.
- [x] `docker build -t grocery-pricing .` builds an image in a Docker-enabled
  environment.
- [x] `docker run --rm grocery-pricing` runs the fixture pipeline.
- [x] HITL: verify Docker locally where Docker is installed and approved.

## 3. Cron-safe logging

Type: AFK

Blocked by: Issue 1

User stories covered: cron-safe logging

What to build: Document a cron entry that can run the local pipeline without
requiring an interactive shell, and make run logs discoverable.

Acceptance criteria:

- [x] The pipeline writes `artifacts/pipeline.log`.
- [x] A cron example exists under `docs/operations/`.
- [ ] HITL: choose the actual schedule and absolute checkout path.
- [ ] HITL: install the cron entry on the target machine.

## 4. Dashboard reads latest successful run

Type: AFK

Blocked by: Issue 1

User stories covered: dashboard reads latest successful run

What to build: Keep the analysis view tied to the latest successful pipeline run
artifact so analysts can inspect the current output without rerunning each step
manually.

Acceptance criteria:

- [x] The pipeline writes `latest_successful_run.json`.
- [x] The pipeline refreshes `analysis_view.html`.
- [x] The latest run artifact records output file names and parsed item details.

## 5. Pre-commit checks

Type: HITL

Blocked by: None - can start immediately

User stories covered: pre-commit checks

What to build: Add commit-time checks once this folder is initialized as a git
repo and the preferred hook system is approved.

Acceptance criteria:

- [x] `python3 scripts/check.py` runs tests and the local pipeline.
- [ ] HITL: initialize or identify the git repo.
- [ ] HITL: approve Node/Husky dependencies, or choose Python-native
  `pre-commit`.
- [ ] HITL: install the hook in the chosen repo.
