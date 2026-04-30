import pytest
from weather import get_api_key


def test_get_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("WEATHER_API_KEY", raising=False)
    with pytest.raises(ValueError, match="WEATHER_API_KEY"):
        get_api_key()


def test_get_api_key_returns_value(monkeypatch):
    monkeypatch.setenv("WEATHER_API_KEY", "test_key_abc")
    assert get_api_key() == "test_key_abc"
