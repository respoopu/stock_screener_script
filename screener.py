"""
Screening logic for Short Squeeze Screener.
Applies filters, ranks candidates, and formats reports.
"""

import logging

from config import RANKING_WEIGHTS, SCREENING_CONFIG
from data_fetcher import calculate_volume_spike, get_stock_data

logger = logging.getLogger("short_squeeze_screener.screener")


def screen_for_squeeze_candidates(
    symbols: list[str],
    config: dict,
) -> list[dict]:
    """
    Fetch data and apply all screening criteria.

    Pipeline:
    1. Fetch detailed data for all symbols via yfinance
    2. Filter by market cap range
    3. Filter by volume spike (>= 2x average)
    4. Filter by float (<= 50M shares)
    5. Filter by short interest (>= 20% of float)
    6. Filter by days to cover (>= 5)

    Returns list of candidate dicts with all metrics populated.
    """
    if not symbols:
        return []

    # Fetch data for all symbols
    stocks = get_stock_data(symbols)
    logger.info("Screening %d stocks with data...", len(stocks))

    candidates = []
    for stock in stocks:
        sym = stock["symbol"]

        # Filter: Market cap range
        market_cap = stock["marketCap"]
        if market_cap < config["min_market_cap"] or market_cap > config["max_market_cap"]:
            logger.debug("%s: rejected - market cap $%s outside range", sym, _fmt_cap(market_cap))
            continue

        # Filter: Volume spike
        volume_spike = calculate_volume_spike(stock["volume"], stock["avgVolume"])
        if volume_spike is None or volume_spike < config["min_volume_spike_ratio"]:
            logger.debug(
                "%s: rejected - volume spike %.1fx < %.1fx minimum",
                sym,
                volume_spike or 0,
                config["min_volume_spike_ratio"],
            )
            continue

        # Filter: Float shares
        float_shares = stock["floatShares"]
        if float_shares <= 0:
            logger.debug("%s: rejected - no float data", sym)
            continue
        if float_shares > config["max_float_shares"]:
            logger.debug("%s: rejected - float %.1fM > %.0fM max", sym, float_shares / 1e6, config["max_float_shares"] / 1e6)
            continue

        # Filter: Short interest percentage
        short_pct = stock["shortPercentOfFloat"]
        if short_pct < config["min_short_interest_pct"]:
            logger.debug("%s: rejected - SI %.1f%% < %.0f%% min", sym, short_pct, config["min_short_interest_pct"])
            continue

        # Filter: Days to cover (shortRatio from Yahoo = days to cover)
        days_to_cover = stock["shortRatio"]
        if days_to_cover < config["min_days_to_cover"]:
            logger.debug("%s: rejected - DTC %.1f < %.0f min", sym, days_to_cover, config["min_days_to_cover"])
            continue

        # All filters passed
        stock["volume_spike"] = volume_spike
        stock["days_to_cover"] = days_to_cover
        stock["short_interest_pct"] = short_pct
        candidates.append(stock)

        logger.info(
            "CANDIDATE: %s | SI=%.1f%% | DTC=%.1f | Float=%.1fM | Spike=%.1fx",
            sym,
            short_pct,
            days_to_cover,
            float_shares / 1e6,
            volume_spike,
        )

    logger.info("Screening complete: %d candidates from %d stocks", len(candidates), len(stocks))
    return candidates


def rank_candidates(candidates: list[dict]) -> list[dict]:
    """
    Rank candidates by weighted squeeze score (0-100 scale).

    Uses min-max normalization within the candidate pool.
    Float size is inverted (lower = better).
    """
    if not candidates:
        return []

    if len(candidates) == 1:
        candidates[0]["squeeze_score"] = 50
        return candidates

    si_values = [c["short_interest_pct"] for c in candidates]
    dtc_values = [c["days_to_cover"] for c in candidates]
    spike_values = [c["volume_spike"] for c in candidates]
    float_values = [c["floatShares"] for c in candidates]

    def normalize(value: float, values: list[float], invert: bool = False) -> float:
        """Min-max normalize a value. Returns 0.5 if no variance."""
        min_val = min(values)
        max_val = max(values)
        if max_val == min_val:
            return 0.5
        normalized = (value - min_val) / (max_val - min_val)
        return 1.0 - normalized if invert else normalized

    for candidate in candidates:
        si_norm = normalize(candidate["short_interest_pct"], si_values)
        dtc_norm = normalize(candidate["days_to_cover"], dtc_values)
        spike_norm = normalize(candidate["volume_spike"], spike_values)
        float_norm = normalize(candidate["floatShares"], float_values, invert=True)

        score = (
            RANKING_WEIGHTS["short_interest_pct"] * si_norm
            + RANKING_WEIGHTS["days_to_cover"] * dtc_norm
            + RANKING_WEIGHTS["volume_spike"] * spike_norm
            + RANKING_WEIGHTS["float_size"] * float_norm
        )

        candidate["squeeze_score"] = round(score * 100)

    candidates.sort(key=lambda c: c["squeeze_score"], reverse=True)
    return candidates


def format_candidate_report(candidate: dict) -> str:
    """Format a single candidate into a display block."""
    symbol = candidate["symbol"]
    name = candidate["companyName"]
    si_pct = candidate["short_interest_pct"]
    dtc = candidate["days_to_cover"]
    float_m = candidate["floatShares"] / 1_000_000
    spike = candidate["volume_spike"]
    price = candidate["price"]
    score = candidate["squeeze_score"]

    market_cap = candidate["marketCap"]
    if market_cap >= 1_000_000_000:
        cap_str = f"${market_cap / 1_000_000_000:.1f}B"
    else:
        cap_str = f"${market_cap / 1_000_000:.0f}M"

    return (
        "\u2501" * 22 + "\n"
        f"\U0001f3af {symbol} - {name}\n"
        f"\n"
        f"Short Interest: {si_pct:.1f}% of float\n"
        f"Days to Cover: {dtc:.1f} days\n"
        f"Float: {float_m:.1f}M shares\n"
        f"Volume Spike: {spike:.1f}x average\n"
        f"Current Price: ${price:.2f}\n"
        f"Market Cap: {cap_str}\n"
        f"\n"
        f"Squeeze Score: {score}/100\n"
        + "\u2501" * 22
    )


def _fmt_cap(market_cap: float) -> str:
    """Format market cap for log messages."""
    if market_cap >= 1_000_000_000:
        return f"{market_cap / 1_000_000_000:.1f}B"
    if market_cap >= 1_000_000:
        return f"{market_cap / 1_000_000:.0f}M"
    return str(market_cap)
