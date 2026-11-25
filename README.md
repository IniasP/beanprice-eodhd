# beanprice-eodhd

A [beanprice](https://github.com/beancount/beanprice) source for [eodhd.com](https://eodhd.com)'s
end-of-day price API.

## Install

```bash
uv add git+https://github.com/IniasP/beanprice-eodhd.git
```

## Usage

Provide your API key either via the `EODHD_API_KEY` environment variable, or an `apikey` file in the
directory you run beanprice from.

Reference the source in a commodity's `price` metadata, using eodhd's `SYMBOL.EXCHANGE` tickers:

```beancount
2020-01-01 commodity VWCE
  price: "EUR:beanprice_eodhd/VWCE.XETRA"
```

Prices are daily closes, stamped 16:00 UTC.

## License

[CC0 1.0](LICENSE) -- public domain dedication.
