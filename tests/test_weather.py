import pytest
from weather import get_api_key


def test_get_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="WEATHER_API_KEY"):
        get_api_key()


def test_get_api_key_returns_value(monkeypatch):
    monkeypatch.setenv("WEATHER_API_KEY", "test_key_abc")
    assert get_api_key() == "test_key_abc"


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
    result = pd.read_csv(csv_path, dtype={"zip_code": str})
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
