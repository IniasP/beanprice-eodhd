import datetime
from decimal import Decimal
from unittest import mock

import pytest
import requests

from beanprice_eodhd import EodhdError, Source


class MockResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f"status {self.status_code}")


@pytest.fixture
def with_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("EODHD_API_KEY", raising=False)
    (tmp_path / "apikey").write_text("secret-key\n", encoding="utf8")
    monkeypatch.chdir(tmp_path)


def test_source_init_raises_without_api_key_file(tmp_path, monkeypatch):
    monkeypatch.delenv("EODHD_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(EodhdError, match="apikey"):
        Source()


@pytest.mark.usefixtures("with_api_key")
def test_source_reads_api_key():
    assert Source().api_key == "secret-key"


@pytest.mark.usefixtures("with_api_key")
def test_get_prices_series_success():
    payload = [
        {"date": "2026-08-10", "close": 168.48},
        {"date": "2026-08-11", "close": 168.5},
    ]
    with mock.patch("beanprice_eodhd.requests.get", return_value=MockResponse(payload)):
        prices = Source().get_prices_series(
            "VWCE.XETRA", datetime.datetime(2026, 8, 10), datetime.datetime(2026, 8, 11)
        )

    assert [p.price for p in prices] == [Decimal("168.48"), Decimal("168.5")]
    assert [p.time.date() for p in prices] == [datetime.date(2026, 8, 10), datetime.date(2026, 8, 11)]
    assert all(p.time.tzinfo is not None for p in prices)


@pytest.mark.usefixtures("with_api_key")
def test_get_prices_series_wraps_request_errors():
    with mock.patch("beanprice_eodhd.requests.get", side_effect=requests.ConnectionError("boom")):
        with pytest.raises(EodhdError, match="VWCE.XETRA"):
            Source().get_prices_series(
                "VWCE.XETRA", datetime.datetime(2026, 8, 10), datetime.datetime(2026, 8, 11)
            )


@pytest.mark.usefixtures("with_api_key")
def test_get_prices_series_rejects_non_list_response():
    with mock.patch("beanprice_eodhd.requests.get", return_value=MockResponse({"error": "bad symbol"})):
        with pytest.raises(EodhdError, match="Unexpected response"):
            Source().get_prices_series(
                "VWCE.XETRA", datetime.datetime(2026, 8, 10), datetime.datetime(2026, 8, 11)
            )


@pytest.mark.usefixtures("with_api_key")
def test_get_prices_series_rejects_http_error_status():
    with mock.patch("beanprice_eodhd.requests.get", return_value=MockResponse([], status_code=500)):
        with pytest.raises(EodhdError, match="VWCE.XETRA"):
            Source().get_prices_series(
                "VWCE.XETRA", datetime.datetime(2026, 8, 10), datetime.datetime(2026, 8, 11)
            )


def test_source_reads_api_key_from_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EODHD_API_KEY", " env-key ")
    assert Source().api_key == "env-key"
