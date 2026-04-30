# GitHub Actions Scheduled Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Schedule `weather.py` to run daily on GitHub Actions, appending new rows to `weather_data.csv` and committing the result back to `main`.

**Architecture:** Two changes — (1) refactor `weather.py` to extract a testable `get_api_key()` guard and a `save_weather_data()` append/dedup function; (2) add a single-job GitHub Actions workflow that installs deps, runs the script, and commits the updated CSV. Tests cover the two extracted functions using pytest and `tmp_path` fixtures.

**Tech Stack:** Python 3.11, pandas, pytest, GitHub Actions (`actions/checkout@v4`, `actions/setup-python@v5`)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `weather.py` | Modify | Add `get_api_key()` guard + `save_weather_data()` append/dedup; call both from script body |
| `tests/test_weather.py` | Create | Unit tests for `get_api_key()` and `save_weather_data()` |
| `requirements.txt` | Modify | Add `pytest` |
| `.github/workflows/weather_pipeline.yml` | Create | Scheduled workflow definition |

---

## Task 1: Add pytest to requirements and create tests directory

**Files:**
- Modify: `requirements.txt`
- Create: `tests/__init__.py`

- [ ] **Step 1: Add pytest to requirements.txt**

Open `requirements.txt` and append this line at the end:
```
pytest==8.3.5
```

- [ ] **Step 2: Create the tests package**

```bash
mkdir -p tests && touch tests/__init__.py
```

- [ ] **Step 3: Install updated requirements**

```bash
pip install -r requirements.txt
```

Expected: pytest installs without errors. Verify with:
```bash
pytest --version
```
Expected output contains: `pytest 8.3.5`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt tests/__init__.py
git commit -m "chore: add pytest and tests package"
```

---

## Task 2: Extract get_api_key() with TDD

**Files:**
- Modify: `weather.py` (lines 1–9)
- Create: `tests/test_weather.py`

This extracts the API key loading into a testable function and adds an early guard that fails with a clear message rather than a cryptic `KeyError` later.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_weather.py`:

```python
import pytest
from weather import get_api_key


def test_get_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="WEATHER_API_KEY"):
        get_api_key()


def test_get_api_key_returns_value(monkeypatch):
    monkeypatch.setenv("WEATHER_API_KEY", "test_key_abc")
    assert get_api_key() == "test_key_abc"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_weather.py -v
```

Expected: `ImportError` or `AttributeError` — `get_api_key` does not exist yet.

- [ ] **Step 3: Restructure weather.py with get_api_key() and main guard**

Replace the entire contents of `weather.py`. The script body moves inside `if __name__ == "__main__":` so that `from weather import get_api_key` in tests never triggers `get_api_key()` at import time.

```python
import requests
import json
import time
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()


def get_api_key():
    key = os.getenv("WEATHER_API_KEY")
    if not key:
        raise ValueError("WEATHER_API_KEY environment variable is not set or empty")
    return key


if __name__ == "__main__":
    API_KEY = get_api_key()

    api_url = "https://api.weatherapi.com/v1/forecast.json"

    zip_codes = [
        "90045",  # Los Angeles, CA
        "10001",  # New York, NY
        "60601",  # Chicago, IL
        "98101",  # Seattle, WA
        "33101",  # Miami, FL
        "77001",  # Houston, TX
        "85001",  # Phoenix, AZ
        "19101",  # Philadelphia, PA
        "78201",  # San Antonio, TX
        "92101",  # San Diego, CA
        "75201",  # Dallas, TX
        "95101",  # San Jose, CA
        "78701",  # Austin, TX
        "30301",  # Atlanta, GA
        "28201",  # Charlotte, NC
        "43201",  # Columbus, OH
        "80201",  # Denver, CO
        "32201",  # Jacksonville, FL
        "46201",  # Indianapolis, IN
        "94101",  # San Francisco, CA
    ]

    results = []

    for zip_code in zip_codes:
        params = {
            "key": API_KEY,
            "q": zip_code,
            "days": 7
        }

        response = requests.get(api_url, params=params)
        data = response.json()

        city = data["location"]["name"]
        region = data["location"]["region"]

        for day in data["forecast"]["forecastday"]:
            results.append({
                "zip_code": zip_code,
                "city": city,
                "region": region,
                "date": day["date"],
                "max_temp_f": day["day"]["maxtemp_f"],
                "min_temp_f": day["day"]["mintemp_f"],
                "condition": day["day"]["condition"]["text"],
            })

        print(f"{zip_code} | {city}, {region} | {len(data['forecast']['forecastday'])} days fetched")

        time.sleep(1)

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")

    df.to_csv("weather_data.csv", index=False)
    print("Saved to weather_data.csv")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_weather.py -v
```

Expected:
```
PASSED tests/test_weather.py::test_get_api_key_raises_when_missing
PASSED tests/test_weather.py::test_get_api_key_returns_value
```

- [ ] **Step 5: Commit**

```bash
git add weather.py tests/test_weather.py
git commit -m "feat: extract get_api_key with early guard"
```

---

## Task 3: Extract save_weather_data() with TDD

**Files:**
- Modify: `weather.py` (last 5 lines — the `df.to_csv(...)` block)
- Modify: `tests/test_weather.py` (append new tests)

This replaces the overwrite behavior with append + dedup. The function is extracted so it can be tested with a `tmp_path` fixture without touching real files.

- [ ] **Step 1: Append the failing tests to tests/test_weather.py**

Add these tests at the bottom of `tests/test_weather.py`:

```python
import pandas as pd
from weather import save_weather_data

SAMPLE_ROW = {
    "zip_code": "90045",
    "city": "Los Angeles",
    "region": "California",
    "date": "2026-04-29",
    "max_temp_f": 70.0,
    "min_temp_f": 55.0,
    "condition": "Sunny",
}


def test_save_creates_new_file(tmp_path):
    csv_path = str(tmp_path / "weather.csv")
    df = pd.DataFrame([SAMPLE_ROW])
    save_weather_data(df, csv_path)
    result = pd.read_csv(csv_path)
    assert len(result) == 1
    assert result.iloc[0]["zip_code"] == "90045"


def test_save_appends_new_date(tmp_path):
    csv_path = str(tmp_path / "weather.csv")
    row_day1 = {**SAMPLE_ROW, "date": "2026-04-29"}
    row_day2 = {**SAMPLE_ROW, "date": "2026-04-30", "max_temp_f": 72.0}
    save_weather_data(pd.DataFrame([row_day1]), csv_path)
    save_weather_data(pd.DataFrame([row_day2]), csv_path)
    result = pd.read_csv(csv_path)
    assert len(result) == 2


def test_save_deduplicates_same_zip_and_date(tmp_path):
    csv_path = str(tmp_path / "weather.csv")
    row_old = {**SAMPLE_ROW, "max_temp_f": 70.0}
    row_new = {**SAMPLE_ROW, "max_temp_f": 71.5}
    save_weather_data(pd.DataFrame([row_old]), csv_path)
    save_weather_data(pd.DataFrame([row_new]), csv_path)
    result = pd.read_csv(csv_path)
    assert len(result) == 1
    assert result.iloc[0]["max_temp_f"] == 71.5
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_weather.py -v -k "save"
```

Expected: `ImportError` — `save_weather_data` does not exist yet.

- [ ] **Step 3: Add save_weather_data() to weather.py**

Add the function after `get_api_key()` and before the `if __name__ == "__main__":` block:

```python
def save_weather_data(df_new, csv_path="weather_data.csv"):
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=["zip_code", "date"], keep="last")
    else:
        df_combined = df_new
    df_combined.to_csv(csv_path, index=False)
```

- [ ] **Step 4: Replace the old df.to_csv call inside the main block of weather.py**

Find the last 4 lines inside the `if __name__ == "__main__":` block (currently):
```python
    df.to_csv("weather_data.csv", index=False)
    print("Saved to weather_data.csv")
```

Replace with:
```python
    save_weather_data(df)
    print("Appended to weather_data.csv")
```

- [ ] **Step 5: Run all tests to confirm they pass**

```bash
pytest tests/test_weather.py -v
```

Expected: all 5 tests pass (2 from Task 2 + 3 from this task).

- [ ] **Step 6: Commit**

```bash
git add weather.py tests/test_weather.py
git commit -m "feat: replace CSV overwrite with append + dedup"
```

---

## Task 4: Create GitHub Actions workflow

**Files:**
- Create: `.github/workflows/weather_pipeline.yml`

- [ ] **Step 1: Create the workflow directory**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: Create the workflow file**

Create `.github/workflows/weather_pipeline.yml` with this exact content:

```yaml
name: Weather Pipeline

on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  run-pipeline:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run weather pipeline
        env:
          WEATHER_API_KEY: ${{ secrets.WEATHER_API_KEY }}
        run: python weather.py

      - name: Commit and push updated CSV
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add weather_data.csv
          git diff --cached --quiet && exit 0
          git commit -m "chore: update weather_data.csv [skip ci]"
          git push
```

> **Note:** `[skip ci]` in the commit message prevents the push from re-triggering the workflow (an infinite loop).

> **Note:** `permissions: contents: write` is required for the bot to push back to the repo.

- [ ] **Step 3: Verify YAML syntax**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/weather_pipeline.yml'))" && echo "YAML valid"
```

Expected: `YAML valid`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/weather_pipeline.yml
git commit -m "feat: add scheduled GitHub Actions workflow"
```

---

## Task 5: Add WEATHER_API_KEY to GitHub repository secrets

This step is manual — it cannot be done from the terminal.

- [ ] **Step 1: Open repository secrets**

In your browser, navigate to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.

- [ ] **Step 2: Add the secret**

- Name: `WEATHER_API_KEY`
- Value: your WeatherAPI.com API key (same value as in your local `.env` file)

Click **Add secret**.

- [ ] **Step 3: Trigger a manual test run**

In GitHub, go to **Actions** → **Weather Pipeline** → **Run workflow** → **Run workflow**.

Watch the run complete. Verify:
- All 5 steps show green checkmarks
- The **Commit and push updated CSV** step either commits new rows or exits cleanly with "nothing to commit"
- `weather_data.csv` on `main` has updated rows

---

## Verification Checklist

After Task 5 completes:

- [ ] `pytest tests/test_weather.py -v` passes all 5 tests locally
- [ ] `.github/workflows/weather_pipeline.yml` exists and YAML is valid
- [ ] Manual workflow run succeeds on GitHub Actions
- [ ] `weather_data.csv` rows increase (or stay the same on a duplicate run) — no rows deleted
- [ ] Re-running the workflow on the same day does not create duplicate `(zip_code, date)` rows
