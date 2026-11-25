"""Fetch prices from eodhd.com's EOD API, as a beanprice Source."""
import os
from datetime import datetime, time as dtime, timedelta, timezone
from decimal import Decimal
from typing import Any, List, Optional

import requests

from beanprice import source

FORMAT = "%Y-%m-%d"


class EodhdError(ValueError):
    "An error from the eodhd.com API."


def _get_api_key() -> str:
    """Read the API key from $EODHD_API_KEY, or else an 'apikey' file in the current directory."""
    if os.environ.get("EODHD_API_KEY"):
        return os.environ["EODHD_API_KEY"].strip()
    try:
        with open("apikey", "r", encoding="utf8") as file:
            return file.read().strip()
    except FileNotFoundError as error:
        raise EodhdError(
            "Missing eodhd.com API key: set $EODHD_API_KEY or create an 'apikey' file in the current directory."
        ) from error


def _parse_response(data: Any, ticker: str) -> List[dict]:
    if not isinstance(data, list):
        raise EodhdError(f"Unexpected response fetching prices for {ticker}: {data!r}")
    return data


class Source(source.Source):
    "eodhd.com EOD API price extractor."

    def __init__(self):
        self.api_key = _get_api_key()

    def get_prices_series(
        self, ticker: str, time_begin: datetime, time_end: datetime
    ) -> Optional[List[source.SourcePrice]]:
        """See contract in beanprice.source.Source."""
        try:
            response = requests.get(
                f"https://eodhd.com/api/eod/{ticker}",
                params={
                    "from": time_begin.strftime(FORMAT),
                    "to": time_end.strftime(FORMAT),
                    "period": "d",
                    "api_token": self.api_key,
                    "fmt": "json",
                },
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            raise EodhdError(
                f"Failed to fetch prices for {ticker} from eodhd.com: {error}"
            ) from error

        rows = _parse_response(response.json(), ticker)
        return [
            source.SourcePrice(
                Decimal(str(row["close"])),
                datetime.combine(
                    datetime.strptime(row["date"], FORMAT).date(),
                    dtime(16, 0),
                    tzinfo=timezone.utc,
                ),
                None,
            )
            for row in rows
        ]

    def get_latest_price(self, ticker: str) -> Optional[source.SourcePrice]:
        """See contract in beanprice.source.Source."""
        now = datetime.now(timezone.utc)
        prices = self.get_prices_series(ticker, now - timedelta(days=5), now)
        return prices[-1] if prices else None

    def get_historical_price(
        self, ticker: str, time: datetime
    ) -> Optional[source.SourcePrice]:
        """See contract in beanprice.source.Source."""
        prices = self.get_prices_series(ticker, time - timedelta(days=5), time)
        return prices[-1] if prices else None
