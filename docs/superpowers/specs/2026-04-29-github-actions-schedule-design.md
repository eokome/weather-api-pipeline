# GitHub Actions Scheduled Pipeline Design

**Date:** 2026-04-29
**Project:** weather-api-pipeline
**Status:** Approved

---

## Overview

Add a GitHub Actions workflow that runs `weather.py` on a daily schedule, appends new rows to `weather_data.csv`, and commits the updated file back to `main`. Failures notify via GitHub's built-in email alerting.

---

## Triggers

| Trigger | Value |
|---|---|
| Cron schedule | `0 6 * * *` (6:00 AM UTC daily) |
| Manual | `workflow_dispatch` |

---

## Secrets

One repository secret must be added in GitHub (Settings → Secrets and variables → Actions):

| Secret name | Value |
|---|---|
| `WEATHER_API_KEY` | WeatherAPI.com API key |

The workflow injects it as an environment variable. No changes to the `.env` file or `weather.py`'s `os.getenv` call are required.

---

## Workflow Structure

Single job: `run-pipeline`, runs on `ubuntu-latest`.

### Steps

1. **Checkout** — `actions/checkout@v4` with `fetch-depth: 0`
2. **Setup Python** — `actions/setup-python@v5`, Python 3.11, pip cache enabled
3. **Install dependencies** — `pip install -r requirements.txt`
4. **Run pipeline** — `python weather.py` with `WEATHER_API_KEY` from secrets
5. **Commit & push CSV** — bot git user commits and pushes `weather_data.csv` if changed; skips gracefully if no diff

---

## Script Change: Append Mode

`weather.py` currently overwrites `weather_data.csv` on every run. It will be updated to:

1. Read the existing CSV if it exists
2. Append the new rows from the current run
3. Deduplicate on `(zip_code, date)` keeping the latest entry
4. Write the result back to `weather_data.csv`

This builds a rolling historical archive without double-counting re-runs on the same day.

---

## Error Handling

| Failure mode | Behavior |
|---|---|
| API key missing/invalid | Script raises a descriptive exception early; job fails with a clear log message |
| Network error / API timeout | Job fails; GitHub emails the repo owner automatically |
| No CSV changes (re-run same day) | Commit step detects empty diff and exits cleanly without failing |

---

## File Changes

| File | Change |
|---|---|
| `.github/workflows/weather_pipeline.yml` | New — defines the scheduled workflow |
| `weather.py` | Modified — append + dedup logic instead of overwrite |
