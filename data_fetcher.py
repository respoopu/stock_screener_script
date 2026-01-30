"""
Data fetcher module for Short Squeeze Screener.
Uses yfinance to retrieve stock data from Yahoo Finance.
"""

import logging
import time

import yfinance as yf
import pandas as pd

from config import SCREENING_CONFIG, TICKER_FETCH_BATCH_SIZE, TICKER_FETCH_DELAY

logger = logging.getLogger("short_squeeze_screener.data_fetcher")


def get_stock_universe() -> list[str]:
    """
    Build a universe of US small/mid-cap stock symbols.

    Uses yfinance screen to get S&P 500, NASDAQ-100, and other indices,
    then fetches a broad list via the Yahoo Finance screener.

    Returns list of ticker symbols.
    """
    logger.info("Building stock universe from Yahoo Finance screeners...")

    # Use yf.screen to get stocks matching our market cap criteria
    # Yahoo Finance screener for small/mid cap equities
    try:
        # Fetch most-active, small-cap, and mid-cap screeners
        screener_keys = [
            "most_actives",
            "small_cap_gainers",
            "undervalued_growth_stocks",
            "aggressive_small_caps",
            "growth_technology_stocks",
            "undervalued_large_caps",
        ]

        all_symbols = set()
        for key in screener_keys:
            try:
                result = yf.screen(key)
                if result and "quotes" in result:
                    for quote in result["quotes"]:
                        sym = quote.get("symbol", "")
                        # Only US stocks (no dots = no foreign tickers like BRK.B excluded)
                        # Allow dots for classes like BRK.B but exclude foreign suffixes
                        if sym and not any(c in sym for c in ["^", "="]):
                            all_symbols.add(sym)
                    logger.debug("Screener '%s': found %d symbols", key, len(result["quotes"]))
            except Exception as e:
                logger.warning("Screener '%s' failed: %s", key, e)

        logger.info("Collected %d unique symbols from Yahoo screeners", len(all_symbols))
        return sorted(all_symbols)

    except Exception as e:
        logger.error("Failed to build stock universe: %s", e)
        return []


def get_stock_data(symbols: list[str]) -> list[dict]:
    """
    Fetch detailed stock data for a list of symbols using yfinance.

    Fetches in batches to avoid throttling.
    Returns list of dicts with all relevant fields for screening.
    """
    results = []
    total = len(symbols)

    for i in range(0, total, TICKER_FETCH_BATCH_SIZE):
        batch = symbols[i : i + TICKER_FETCH_BATCH_SIZE]
        batch_num = (i // TICKER_FETCH_BATCH_SIZE) + 1
        total_batches = (total + TICKER_FETCH_BATCH_SIZE - 1) // TICKER_FETCH_BATCH_SIZE

        logger.info("Fetching data batch %d/%d (%d symbols)...", batch_num, total_batches, len(batch))

        for sym in batch:
            try:
                ticker = yf.Ticker(sym)
                info = ticker.info

                if not info or info.get("quoteType") not in ("EQUITY",):
                    logger.debug("%s: skipped (not equity or no data)", sym)
                    continue

                stock_data = {
                    "symbol": sym,
                    "companyName": info.get("longName") or info.get("shortName") or sym,
                    "price": info.get("currentPrice") or info.get("regularMarketPrice") or 0,
                    "marketCap": info.get("marketCap") or 0,
                    "volume": info.get("regularMarketVolume") or info.get("volume") or 0,
                    "avgVolume": info.get("averageVolume") or info.get("averageDailyVolume3Month") or 0,
                    "avgVolume10d": info.get("averageVolume10days") or info.get("averageDailyVolume10Day") or 0,
                    "floatShares": info.get("floatShares") or 0,
                    "sharesOutstanding": info.get("sharesOutstanding") or info.get("impliedSharesOutstanding") or 0,
                    "sharesShort": info.get("sharesShort") or 0,
                    "sharesShortPriorMonth": info.get("sharesShortPriorMonth") or 0,
                    "shortRatio": info.get("shortRatio") or 0,  # Days to cover from Yahoo
                    "shortPercentOfFloat": (info.get("shortPercentOfFloat") or 0) * 100,  # Convert to percentage
                    "sector": info.get("sector") or "",
                    "industry": info.get("industry") or "",
                }

                results.append(stock_data)
                logger.debug(
                    "%s: mktcap=%s, SI=%.1f%%, DTC=%.1f, float=%s, vol=%s",
                    sym,
                    _fmt_number(stock_data["marketCap"]),
                    stock_data["shortPercentOfFloat"],
                    stock_data["shortRatio"],
                    _fmt_number(stock_data["floatShares"]),
                    _fmt_number(stock_data["volume"]),
                )

            except Exception as e:
                logger.warning("%s: failed to fetch data: %s", sym, e)

        # Delay between batches to avoid throttling
        if i + TICKER_FETCH_BATCH_SIZE < total:
            time.sleep(TICKER_FETCH_DELAY)

    logger.info("Fetched data for %d/%d symbols", len(results), total)
    return results


def calculate_volume_spike(current_volume: float, avg_volume: float) -> float | None:
    """Calculate volume spike ratio = current_volume / avg_volume."""
    if not avg_volume or avg_volume <= 0:
        return None
    if not current_volume or current_volume <= 0:
        return 0.0
    return current_volume / avg_volume


def _fmt_number(n: float) -> str:
    """Format a large number for readable logging."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)
