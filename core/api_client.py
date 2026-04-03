"""
api_client.py — Async price fetching for crypto (CoinGecko) and stocks (yfinance).
Runs in QThread workers so the PySide6 UI never freezes.
"""

from __future__ import annotations
import threading
from PySide6.QtCore import QObject, Signal, QThread


class PriceFetcher(QObject):
    """Fetches live prices in a background thread, emits results via Qt signal."""

    # Signal: emits dict {asset_name: new_price}
    prices_ready = Signal(dict)
    error = Signal(str)

    def fetch_crypto_prices(self, coin_ids: list[str], currency: str = "inr"):
        """Fetch crypto prices from CoinGecko (free, no API key)."""
        thread = threading.Thread(
            target=self._fetch_crypto, args=(coin_ids, currency), daemon=True
        )
        thread.start()

    def fetch_stock_prices(self, tickers: list[str]):
        """Fetch stock prices via yfinance."""
        thread = threading.Thread(
            target=self._fetch_stocks, args=(tickers,), daemon=True
        )
        thread.start()

    def _fetch_crypto(self, coin_ids: list[str], currency: str):
        try:
            import urllib.request
            import json

            ids_str = ",".join(coin_ids)
            url = (
                f"https://api.coingecko.com/api/v3/simple/price"
                f"?ids={ids_str}&vs_currencies={currency}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "WalletHub/3.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            prices = {}
            for coin_id in coin_ids:
                if coin_id in data and currency in data[coin_id]:
                    prices[coin_id] = float(data[coin_id][currency])

            self.prices_ready.emit(prices)
        except Exception as e:
            self.error.emit(f"Crypto fetch failed: {e}")

    def _fetch_stocks(self, tickers: list[str]):
        try:
            import yfinance as yf

            prices = {}
            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.fast_info
                    price = getattr(info, "last_price", None)
                    if price is not None:
                        prices[ticker] = float(price)
                except Exception:
                    continue

            self.prices_ready.emit(prices)
        except Exception as e:
            self.error.emit(f"Stock fetch failed: {e}")


# ── Mapping helpers ───────────────────────────────────────────────

# Common crypto name → CoinGecko ID mapping
CRYPTO_ID_MAP = {
    "bitcoin": "bitcoin", "btc": "bitcoin",
    "ethereum": "ethereum", "eth": "ethereum",
    "solana": "solana", "sol": "solana",
    "cardano": "cardano", "ada": "cardano",
    "dogecoin": "dogecoin", "doge": "dogecoin",
    "ripple": "ripple", "xrp": "ripple",
    "polkadot": "polkadot", "dot": "polkadot",
    "polygon": "matic-network", "matic": "matic-network",
    "avalanche": "avalanche-2", "avax": "avalanche-2",
    "chainlink": "chainlink", "link": "chainlink",
    "litecoin": "litecoin", "ltc": "litecoin",
    "bnb": "binancecoin", "binance": "binancecoin",
    "tron": "tron", "trx": "tron",
}


def resolve_crypto_id(name: str) -> str | None:
    """Try to map a user-entered asset name to a CoinGecko coin ID."""
    key = name.lower().strip()
    return CRYPTO_ID_MAP.get(key, key)


def is_likely_ticker(name: str) -> bool:
    """Heuristic: if it's 1-5 uppercase letters, it's probably a stock ticker."""
    clean = name.strip().upper()
    return 1 <= len(clean) <= 5 and clean.isalpha()
